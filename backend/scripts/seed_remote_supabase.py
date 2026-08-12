"""Load the checked-in synthetic raw-data seed through the Supabase Data API."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "backend" / "scripts" / "generate_supabase_seed.py"
DEFAULT_ENV_FILE = ROOT / "backend" / ".env"


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def load_seed_payloads() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    spec = importlib.util.spec_from_file_location("generate_supabase_seed", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the seed generator.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    seed_sql, counts = module.build_seed()
    if counts != {
        "patients": 300,
        "questionnaires": 60,
        "documents": 9,
        "questionnaires_conflict": 54,
        "questionnaires_no_registration": 6,
    }:
        raise RuntimeError(f"Unexpected raw-data counts: {counts}")

    encoded_payloads = re.findall(
        r"jsonb_to_recordset\(\$json\$(\[.*?\])\$json\$::jsonb\)",
        seed_sql,
        flags=re.DOTALL,
    )
    if len(encoded_payloads) != 3:
        raise RuntimeError("Expected patient, questionnaire, and document payloads in the generated seed.")
    return tuple(json.loads(payload) for payload in encoded_payloads)  # type: ignore[return-value]


def normalize_object_keys(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Give every object in a PostgREST bulk request the same set of keys."""
    keys = set().union(*(row.keys() for row in rows))
    return [{key: row.get(key) for key in keys} for row in rows]


class SupabaseDataApi:
    def __init__(self, url: str, secret_key: str) -> None:
        self.base_url = url.rstrip("/") + "/rest/v1"
        self.secret_key = secret_key

    def request(
        self,
        method: str,
        table: str,
        *,
        query: dict[str, str] | None = None,
        payload: object | None = None,
        prefer: str | None = None,
    ) -> tuple[bytes, dict[str, str]]:
        url = f"{self.base_url}/{table}"
        if query:
            url += "?" + urlencode(query, safe="(),.*")
        headers = {"apikey": self.secret_key, "Accept": "application/json"}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload, separators=(",", ":")).encode()
        if prefer:
            headers["Prefer"] = prefer
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                return response.read(), {key.lower(): value for key, value in response.headers.items()}
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"Supabase {method} {table} failed with HTTP {exc.code}: {detail}") from exc

    def upsert(self, table: str, rows: list[dict[str, Any]]) -> None:
        self.request(
            "POST",
            table,
            query={"on_conflict": "source_record_key"},
            payload=rows,
            prefer="resolution=merge-duplicates,return=minimal",
        )

    def select(self, table: str, fields: str) -> list[dict[str, Any]]:
        body, _ = self.request("GET", table, query={"select": fields})
        return json.loads(body)

    def exact_count(self, table: str) -> int:
        _, headers = self.request(
            "HEAD",
            table,
            query={"select": "id"},
            prefer="count=exact",
        )
        content_range = headers.get("content-range", "")
        if "/" not in content_range:
            raise RuntimeError(f"Supabase did not return an exact count for {table}.")
        return int(content_range.rsplit("/", 1)[1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    args = parser.parse_args()

    env = load_env(args.env_file)
    url = env.get("EPICENTER_SUPABASE_URL")
    secret_key = env.get("EPICENTER_SUPABASE_SECRET_KEY")
    if not url or not secret_key:
        raise RuntimeError("EPICENTER_SUPABASE_URL and EPICENTER_SUPABASE_SECRET_KEY are required.")

    patients, questionnaires, documents = load_seed_payloads()
    api = SupabaseDataApi(url, secret_key)

    api.upsert("patients", patients)
    patient_rows = api.select("patients", "id,identifier_hash")
    patient_ids = {row["identifier_hash"]: row["id"] for row in patient_rows}

    questionnaire_rows = []
    for row in questionnaires:
        candidate_hash = row.pop("candidate_identifier_hash")
        verified_hash = row.pop("verified_identifier_hash")
        row["candidate_patient_id"] = patient_ids.get(candidate_hash)
        row["patient_id"] = patient_ids.get(verified_hash)
        questionnaire_rows.append(row)
    api.upsert("questionnaire_submissions", questionnaire_rows)

    document_rows = []
    for row in documents:
        row["patient_id"] = patient_ids.get(row["subject_identifier_hash"])
        document_rows.append(row)
    api.upsert("medical_document_samples", normalize_object_keys(document_rows))

    actual_counts = {
        "patients": api.exact_count("patients"),
        "questionnaires": api.exact_count("questionnaire_submissions"),
        "documents": api.exact_count("medical_document_samples"),
    }
    expected_counts = {"patients": 300, "questionnaires": 60, "documents": 9}
    if actual_counts != expected_counts:
        raise RuntimeError(f"Remote count verification failed: expected {expected_counts}, got {actual_counts}")

    remote_questionnaires = api.select(
        "questionnaire_submissions",
        "verification_status,candidate_patient_id,patient_id",
    )
    status_counts: dict[str, int] = {}
    for row in remote_questionnaires:
        status = row["verification_status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    if status_counts != {"conflict": 54, "no_registration": 6}:
        raise RuntimeError(f"Remote questionnaire reconciliation verification failed: {status_counts}")
    if sum(row["candidate_patient_id"] is not None for row in remote_questionnaires) != 54:
        raise RuntimeError("Expected exactly 54 questionnaire candidate links.")
    if any(row["patient_id"] is not None for row in remote_questionnaires):
        raise RuntimeError("No questionnaire should be promoted to a verified patient link.")

    print(json.dumps({**actual_counts, "questionnaire_statuses": status_counts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
