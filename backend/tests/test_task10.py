from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.ai.assistant import _task_relevant_tools
from app.ai.schemas import ApprovedDocumentDataClass, ClassificationInput
from app.core.auth import StaffPrincipal
from app.mcp.insurance_registry import _PROPOSALS, _REGISTRY_AUDIT, _dispatch_tool
from app.mcp.protocol import MAX_TOOL_RESULT_CHARS, tool_result
from app.services.document_classification import classify_document

ROOT = Path(__file__).resolve().parents[2]
TASK10_MIGRATION = (ROOT / "supabase/migrations/20260813150001_task10_ai_document_governance.sql").read_text()


def principal(subject: str) -> StaffPrincipal:
    return StaffPrincipal(
        subject=subject,
        source="test",
        factor_verification_age=(0, -1),
        role="operations_admin",
        clinic_id="clinic_harbourfront",
    )


@pytest.fixture()
def client():
    from app.core.config import Settings, get_settings
    from app.main import app

    app.dependency_overrides[get_settings] = lambda: Settings(
        demo_mode=True, persistence_mode="demo", _env_file=None
    )
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.parametrize(
    ("signals", "category"),
    [
        ({"page_count": 3, "top_text": "I hereby consent to the declaration"}, "form"),
        (
            {"page_count": 1, "has_letterhead": True, "top_text": "GE authorises and please bill to employer"},
            "authorisation_letter",
        ),
        ({"page_count": 1, "has_table_grid": True, "top_text": "Company screening package panel"}, "benefit_structure"),
        ({"page_count": 1, "top_text": "CHAS Blue"}, "coding_scheme"),
    ],
)
def test_four_step_document_classification(signals, category):
    result = classify_document(
        ClassificationInput(
            **signals,
            data_classification=ApprovedDocumentDataClass.SYNTHETIC,
        )
    )
    assert result.category == category
    assert result.review_status == "pending_review"
    assert result.extractor.endswith(f"_{category}_extractor")


def test_fingerprint_overrides_structural_guess():
    result = classify_document(
        ClassificationInput(
            page_count=1,
            has_table_grid=True,
            layout_fingerprint="ge-authorisation-v1",
            data_classification="formally_deidentified",
        )
    )
    assert result.category == "authorisation_letter"
    assert result.document_family == "GE"
    assert result.synthetic is False


def test_task_relevant_tools_are_narrowed():
    assert _task_relevant_tools("operations_admin", "Summarise the queue") == {"epicenter_get_queue_snapshot"}
    assert "epicenter_run_simulation" not in _task_relevant_tools("operations_admin", "Explain ticket Q-014")


def test_streamable_http_initialize_list_and_call(client):
    initialized = client.post(
        "/mcp/operations",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    )
    assert initialized.status_code == 200
    assert initialized.json()["result"]["protocolVersion"] == "2025-06-18"
    listed = client.post(
        "/mcp/operations",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )
    tools = listed.json()["result"]["tools"]
    assert tools and all("annotations" in tool and "epicenter/governance" in tool["_meta"] for tool in tools)
    called = client.post(
        "/mcp/operations",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "epicenter_get_queue_snapshot",
                "arguments": {"clinic_id": "clinic_harbourfront", "snapshot_at": "now"},
            },
        },
    )
    result = called.json()["result"]
    assert result["isError"] is False
    assert result["structuredContent"]["synthetic"] is True


def test_mcp_inventory_is_exactly_two_servers(client):
    paths = client.get("/openapi.json").json()["paths"]
    roots = {path for path in paths if path.startswith("/mcp/") and path.count("/") == 2}
    assert roots == {"/mcp/operations", "/mcp/insurance-registry"}


def test_tool_response_bound_fails_closed():
    result = tool_result({"payload": "x" * (MAX_TOOL_RESULT_CHARS + 1)})
    assert result["isError"] is True
    assert result["structuredContent"]["error"] == "response_too_large"


def test_staging_rpc_preserves_pending_review_and_staff_confirmation_boundary():
    assert "create or replace function public.epicenter_stage_document_extraction" in TASK10_MIGRATION
    assert "review_status = 'pending_review'" in TASK10_MIGRATION
    assert "field_evidence = coalesce(p_source_evidence" in TASK10_MIGRATION
    assert "security invoker" in TASK10_MIGRATION
    assert "set search_path = ''" in TASK10_MIGRATION
    assert "from public, anon, authenticated" in TASK10_MIGRATION
    assert "review_status = 'confirmed'" not in TASK10_MIGRATION


def test_registry_maker_checker_and_fixture_boundary():
    _PROPOSALS.clear()
    _REGISTRY_AUDIT.clear()
    proposal = _dispatch_tool(
        "registry_propose_mapping",
        {
            "form_id": "synthetic-ge-v2",
            "fixture_classification": "synthetic",
            "approval_reference": "fixture-review-42",
            "synthetic_fixture": {"issuer_code": "GE", "valid_from": "2026-01-01"},
        },
        principal("maker"),
    )
    with pytest.raises(HTTPException):
        _dispatch_tool(
            "registry_review_mapping",
            {"proposal_id": proposal["proposal_id"], "decision": "approved", "reason": "Fixture tests pass."},
            principal("maker"),
        )
    reviewed = _dispatch_tool(
        "registry_review_mapping",
        {"proposal_id": proposal["proposal_id"], "decision": "approved", "reason": "Fixture tests pass."},
        principal("checker"),
    )
    assert reviewed["status"] == "approved"
    assert reviewed["maker_reference"] != reviewed["checker_reference"]
    assert [event["action"] for event in _REGISTRY_AUDIT] == ["mapping_proposed", "mapping_approved"]
    assert _REGISTRY_AUDIT[-1]["actor"] == "checker"


def test_registry_rejects_patient_fields():
    with pytest.raises(HTTPException):
        _dispatch_tool(
            "registry_propose_mapping",
            {
                "form_id": "unsafe",
                "fixture_classification": "formally_deidentified",
                "approval_reference": "approval-unsafe",
                "synthetic_fixture": {"patient_name": "Not allowed"},
            },
            principal("maker"),
        )
