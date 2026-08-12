#!/usr/bin/env python3
"""Exercise the local FastAPI boundary against configured hosted Supabase."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.data.supabase_client import SupabaseDataApi, SupabaseDataError  # noqa: E402
from app.main import app  # noqa: E402


def main() -> None:
    settings = get_settings()
    if not settings.supabase_configured:
        raise SystemExit("Supabase server credentials are not configured.")

    client = TestClient(app)
    dashboard_response = client.get("/api/v1/dashboard")
    dashboard_response.raise_for_status()
    dashboard = dashboard_response.json()
    original = next(ticket for ticket in dashboard["tickets"] if ticket["id"] == "Q-017")

    transition_key = f"live-verification-{uuid4()}"
    transition_payload = {
        "readiness_state": "needs_review",
        "reason": "live_persistence_verification",
        "staff_confirmed": False,
        "expected_version": original["version"],
        "idempotency_key": transition_key,
    }
    first = client.post("/api/v1/tickets/Q-017/transition", json=transition_payload)
    first.raise_for_status()
    replay = client.post("/api/v1/tickets/Q-017/transition", json=transition_payload)
    replay.raise_for_status()
    first_ticket = first.json()["ticket"]
    replay_ticket = replay.json()["ticket"]
    if first_ticket != replay_ticket:
        raise RuntimeError("Idempotent replay returned a different ticket representation.")

    stale_payload = {
        **transition_payload,
        "reason": "must_not_commit",
        "idempotency_key": f"live-stale-{uuid4()}",
    }
    stale = client.post("/api/v1/tickets/Q-017/transition", json=stale_payload)

    restore_payload = {
        "readiness_state": original["readiness_state"],
        "reason": original["readiness_reason"],
        "staff_confirmed": original["staff_confirmed"],
        "expected_version": first_ticket["version"],
        "idempotency_key": f"live-restore-{uuid4()}",
    }
    restored = client.post("/api/v1/tickets/Q-017/transition", json=restore_payload)
    restored.raise_for_status()
    restored_ticket = restored.json()["ticket"]
    if restored_ticket["id"] != original["id"]:
        raise RuntimeError("The transition replaced the persistent queue ticket.")
    if restored_ticket["original_ordering_at"] != original["original_ordering_at"]:
        raise RuntimeError("The transition reset the ticket's original waiting order.")
    if stale.status_code != 409:
        raise RuntimeError(
            f"Expected stale write status 409, received {stale.status_code}: {stale.json().get('detail')}."
        )

    simulator = client.get("/api/v1/simulator/snapshots")
    simulator.raise_for_status()

    patients = client.get("/api/v1/patients", params={"search": "Tan Kai Xuan", "limit": 5})
    patients.raise_for_status()
    if not patients.json()["records"]:
        raise RuntimeError("The scoped patient browser did not return its seeded record.")

    audit_response = client.get("/api/v1/audit", params={"limit": 10})
    audit_response.raise_for_status()

    server_api = SupabaseDataApi(settings.supabase_url, settings.supabase_secret_key)
    audit_rows = server_api.select(
        "audit_log",
        "id,action_type,target_id",
        filters={"target_id": "eq.Q-017", "action_type": "eq.transition_readiness"},
        order="occurred_at.desc",
        limit=2,
    )
    if len(audit_rows) < 2:
        raise RuntimeError("Expected both committed transitions in the immutable audit log.")

    browser_access = "not_configured"
    if settings.supabase_publishable_key:
        browser_api = SupabaseDataApi(settings.supabase_url, settings.supabase_publishable_key)
        try:
            visible_rows = browser_api.select("queue_entries", "id", limit=1)
            browser_access = "no_rows_visible" if not visible_rows else "unexpected_rows_visible"
        except SupabaseDataError as exc:
            browser_access = f"denied_{exc.status_code}"
        finally:
            browser_api.close()
    server_api.close()
    if browser_access == "unexpected_rows_visible":
        raise RuntimeError("The browser publishable key can read operational queue rows.")

    print(
        json.dumps(
            {
                "dashboard": "passed",
                "ticket_count": len(dashboard["tickets"]),
                "idempotent_replay": "passed",
                "stale_write_status": stale.status_code,
                "single_ticket_preserved": True,
                "restored_state": restored_ticket["readiness_state"],
                "restored_version": restored_ticket["version"],
                "audit_rows_verified": len(audit_rows),
                "simulator_snapshots": len(simulator.json()),
                "patient_search": "passed",
                "audit_endpoint_rows": len(audit_response.json()),
                "browser_database_access": browser_access,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
