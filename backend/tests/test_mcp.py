"""Tests for AI extraction schema validation and MCP tool auth.

Covers:
- ExtractedCoverage rejects extra fields and null-absent values
- FieldEvidence confidence levels are enforced
- authorize_operations_tool enforces role boundaries
- authorize_registry_tool enforces role boundaries
- require_mcp_identity demo-key path
- Operations MCP tools/list discovery
- Registry MCP tools/list discovery
- Operations tool call (get_visit_ticket) in demo mode
- Operations tool call rejects unknown tools
- Registry tool call (registry_get_schema) returns correct fixture
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.requests import Request

from app.ai.schemas import (
    ConfidenceLevel,
    ExtractedCoverage,
    FieldEvidence,
)
from app.core.auth import StaffPrincipal
from app.core.config import Settings
from app.mcp.auth import authorize_operations_tool, authorize_registry_tool, require_mcp_identity

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _staff(role: str = "operations_admin", clinic: str = "clinic_harbourfront") -> StaffPrincipal:
    return StaffPrincipal(
        subject="test-user",
        source="demo",
        factor_verification_age=(0, -1),
        role=role,
        clinic_id=clinic,
    )


# ---------------------------------------------------------------------------
# Extraction schema validation
# ---------------------------------------------------------------------------


class TestExtractedCoverage:
    def test_all_absent_is_valid(self):
        cov = ExtractedCoverage()
        assert cov.issuer_code is None
        assert cov.overall_confidence == ConfidenceLevel.LOW
        assert cov.requested_items == []

    def test_extra_fields_are_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            ExtractedCoverage(unexpected_field="x")
        assert "unexpected_field" in str(exc_info.value)

    def test_confidence_level_enum_enforced(self):
        with pytest.raises(ValidationError):
            FieldEvidence(page=1, excerpt="test", confidence="super_high")

    def test_valid_field_evidence(self):
        fe = FieldEvidence(page=2, excerpt="Corp Health Screening", confidence=ConfidenceLevel.HIGH)
        assert fe.confidence == "high"
        assert fe.page == 2

    def test_valid_full_coverage(self):
        cov = ExtractedCoverage(
            document_family="GHS-CORP",
            issuer_code="GHS-001",
            issuer_name="Great Eastern",
            document_type="Corporate Authorization",
            valid_from="2026-01-01",
            valid_to="2026-12-31",
            screening_package="Tier A Health Screening",
            requested_items=["FBC", "Lipid Panel"],
            overall_confidence=ConfidenceLevel.HIGH,
        )
        assert cov.document_family == "GHS-CORP"
        assert len(cov.requested_items) == 2

    def test_round_trip_serialization(self):
        cov = ExtractedCoverage(
            issuer_code="TEST",
            issuer_code_evidence=FieldEvidence(
                page=1, excerpt="TEST issuer", confidence=ConfidenceLevel.MEDIUM
            ),
        )
        data = cov.model_dump()
        restored = ExtractedCoverage.model_validate(data)
        assert restored.issuer_code == "TEST"
        assert restored.issuer_code_evidence is not None
        assert restored.issuer_code_evidence.confidence == "medium"


# ---------------------------------------------------------------------------
# MCP auth authorization
# ---------------------------------------------------------------------------


class TestAuthorizeOperationsTool:
    def test_operations_admin_can_call_summary(self):
        # Should not raise
        authorize_operations_tool(
            "epicenter_get_operational_summary",
            _staff("operations_admin"),
            clinic_id="clinic_harbourfront",
        )

    def test_registration_staff_cannot_call_admin_tools(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            authorize_operations_tool(
                "epicenter_get_allocation_recommendation",
                _staff("registration_staff"),
            )
        assert exc_info.value.status_code == 403

    def test_registration_staff_can_call_ticket_tool(self):
        # Should not raise
        authorize_operations_tool("epicenter_get_visit_ticket", _staff("registration_staff"))

    def test_clinic_scope_mismatch_is_rejected(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            authorize_operations_tool(
                "epicenter_get_queue_snapshot",
                _staff("operations_admin", clinic="clinic_a"),
                clinic_id="clinic_b",
            )
        assert exc_info.value.status_code == 403

    def test_unknown_role_is_rejected(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            authorize_operations_tool("epicenter_get_visit_ticket", _staff("patient"))

    def test_auditor_can_call_summary(self):
        authorize_operations_tool("epicenter_get_operational_summary", _staff("auditor"))

    def test_auditor_cannot_call_run_simulation(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            authorize_operations_tool("epicenter_run_simulation", _staff("auditor"))


class TestAuthorizeRegistryTool:
    def test_operations_admin_can_call_registry(self):
        authorize_registry_tool("registry_get_schema", _staff("operations_admin"))

    def test_registration_staff_cannot_call_registry(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            authorize_registry_tool("registry_get_schema", _staff("registration_staff"))

    def test_auditor_cannot_call_registry(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            authorize_registry_tool("registry_propose_mapping", _staff("auditor"))


class TestMCPMachineAuthentication:
    @staticmethod
    def _request() -> Request:
        return Request({"type": "http", "method": "POST", "path": "/mcp", "headers": []})

    def test_configured_api_key_authenticates_in_production(self):
        principal = require_mcp_identity(
            self._request(),
            Settings(demo_mode=False, EPICENTER_MCP_API_KEY="release-test-key", _env_file=None),
            "release-test-key",
        )
        assert principal.source == "api_key"
        assert principal.role == "operations_admin"

    def test_wrong_api_key_fails_closed_in_production(self):
        with pytest.raises(HTTPException) as exc_info:
            require_mcp_identity(
                self._request(),
                Settings(demo_mode=False, EPICENTER_MCP_API_KEY="release-test-key", _env_file=None),
                "wrong-key",
            )
        assert exc_info.value.status_code == 401

    def test_configured_demo_key_cannot_be_omitted(self):
        with pytest.raises(HTTPException) as exc_info:
            require_mcp_identity(
                self._request(),
                Settings(demo_mode=True, EPICENTER_MCP_API_KEY="release-test-key", _env_file=None),
                None,
            )
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# MCP endpoint integration tests (TestClient, demo mode)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient in demo mode (default env)."""
    from app.core.config import Settings, get_settings
    from app.main import app
    app.dependency_overrides[get_settings] = lambda: Settings(
        demo_mode=True,
        mcp_api_key=None,
        persistence_mode="demo",
        _env_file=None,
    )
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_settings, None)


class TestOperationsMCPEndpoints:
    def test_healthz(self, client):
        r = client.get("/mcp/operations/healthz")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_tools_list_returns_all_tools(self, client):
        r = client.post("/mcp/operations/tools/list")
        assert r.status_code == 200
        names = [t["name"] for t in r.json()["tools"]]
        assert "epicenter_get_visit_ticket" in names
        assert "epicenter_run_simulation" in names
        assert len(names) == 8

    def test_tools_list_get_also_works(self, client):
        r = client.get("/mcp/operations/tools/list")
        assert r.status_code == 200

    def test_call_get_visit_ticket_in_demo(self, client):
        r = client.post(
            "/mcp/operations/tools/call",
            json={"name": "epicenter_get_visit_ticket", "input": {"ticket_id": "Q-014"}},
        )
        assert r.status_code == 200
        result = r.json()["result"]
        assert result["ticket_id"] == "Q-014"
        assert result["synthetic"] is True
        assert "readiness_state" in result

    def test_call_get_queue_snapshot_in_demo(self, client):
        r = client.post(
            "/mcp/operations/tools/call",
            json={
                "name": "epicenter_get_queue_snapshot",
                "input": {"clinic_id": "clinic_harbourfront", "snapshot_at": "now"},
            },
        )
        assert r.status_code == 200
        result = r.json()["result"]
        assert result["clinic_id"] == "clinic_harbourfront"
        assert "total_tickets" in result

    def test_call_unknown_tool_returns_error(self, client):
        r = client.post(
            "/mcp/operations/tools/call",
            json={"name": "epicenter_delete_everything", "input": {}},
        )
        assert r.status_code == 200  # MCP errors return 200 with error body
        assert "error" in r.json()

    def test_call_missing_tool_name_returns_error(self, client):
        r = client.post("/mcp/operations/tools/call", json={"input": {}})
        assert r.status_code in (200, 400, 422)
        body = r.json()
        # Either MCP-style error body or FastAPI validation error
        assert "error" in body or "detail" in body

    def test_run_simulation_returns_synthetic(self, client):
        r = client.post(
            "/mcp/operations/tools/call",
            json={
                "name": "epicenter_run_simulation",
                "input": {"scenario_id": "serial_baseline", "seed": 20260809},
            },
        )
        assert r.status_code == 200
        result = r.json()["result"]
        assert result["synthetic"] is True
        assert result["scenario_id"] == "serial_baseline"

    def test_compare_simulation_runs(self, client):
        r = client.post(
            "/mcp/operations/tools/call",
            json={
                "name": "epicenter_compare_simulation_runs",
                "input": {
                    "baseline_run_id": "run-serial-001",
                    "epicenter_run_id": "run-epicenter-001",
                },
            },
        )
        assert r.status_code == 200
        result = r.json()["result"]
        assert result["synthetic"] is True
        assert "metrics_delta" in result


class TestRegistryMCPEndpoints:
    def test_healthz(self, client):
        r = client.get("/mcp/insurance-registry/healthz")
        assert r.status_code == 200

    def test_tools_list_returns_all_tools(self, client):
        r = client.post("/mcp/insurance-registry/tools/list")
        assert r.status_code == 200
        names = [t["name"] for t in r.json()["tools"]]
        assert "registry_get_schema" in names
        assert "registry_propose_mapping" in names
        assert "registry_review_mapping" in names
        assert len(names) == 6

    def test_get_schema_known_family(self, client):
        r = client.post(
            "/mcp/insurance-registry/tools/call",
            json={"name": "registry_get_schema", "input": {"document_family": "GHS-CORP"}},
        )
        assert r.status_code == 200
        result = r.json()["result"]
        assert result["document_family"] == "GHS-CORP"
        assert result["synthetic"] is True
        assert "field_definitions" in result

    def test_get_schema_unknown_family_returns_error(self, client):
        r = client.post(
            "/mcp/insurance-registry/tools/call",
            json={"name": "registry_get_schema", "input": {"document_family": "UNKNOWN-FAMILY"}},
        )
        assert r.status_code == 200
        assert "error" in r.json()

    def test_get_evidence_requirements(self, client):
        r = client.post(
            "/mcp/insurance-registry/tools/call",
            json={
                "name": "registry_get_evidence_requirements",
                "input": {"document_family": "GHS-CORP"},
            },
        )
        assert r.status_code == 200
        result = r.json()["result"]
        assert "required_source_fields" in result
        assert "issuer_code" in result["required_source_fields"]

    def test_propose_mapping_returns_pending_review(self, client):
        r = client.post(
            "/mcp/insurance-registry/tools/call",
            json={
                "name": "registry_propose_mapping",
                "input": {
                    "form_id": "test-form-001",
                    "fixture_classification": "synthetic",
                    "approval_reference": "fixture-approval-001",
                    "synthetic_fixture": {"issuer_code": "TEST", "valid_from": "2026-01-01"},
                },
            },
        )
        assert r.status_code == 200
        result = r.json()["result"]
        assert result["status"] == "pending_review"
        assert result["synthetic"] is True

    def test_regression_status(self, client):
        r = client.post(
            "/mcp/insurance-registry/tools/call",
            json={
                "name": "registry_get_regression_status",
                "input": {"mapping_id": "mapping-001"},
            },
        )
        assert r.status_code == 200
        result = r.json()["result"]
        assert result["review_status"] == "pending_review"
