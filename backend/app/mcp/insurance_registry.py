"""Insurance Format Registry MCP — Streamable HTTP endpoint.

Exposed at /mcp/insurance-registry. Isolated maker/checker server that operates
only on approved synthetic or formally de-identified templates.

This server:
- retrieves approved document-family schemas and checkbox conventions
- proposes a mapping for a new synthetic form
- returns required source-evidence fields and fixture tests
- compares a draft mapping with an active version
- reports regression and review status

This server CANNOT:
- learn online from live patient records
- activate its own proposal
- write canonical patient/coverage/eligibility rows
- make an eligibility decision
- access operational queue or ticket data

Compatible with:
- OpenAI Responses API remote MCP tool protocol
- Microsoft Copilot Studio (Streamable HTTP transport)
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.auth import StaffPrincipal
from app.core.config import Settings, get_settings
from app.mcp.auth import authorize_registry_tool, require_mcp_identity
from app.mcp.schemas import (
    CompareMappingVersionsInput,
    EvidenceRequirementsOutput,
    GetEvidenceRequirementsInput,
    GetRegressionStatusInput,
    GetSchemaInput,
    MCPError,
    MappingProposalOutput,
    MappingVersionComparisonOutput,
    ProposeMappingInput,
    RegressionStatusOutput,
    SchemaOutput,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp/insurance-registry", tags=["mcp-insurance-registry"])

_SERVER_INFO = {
    "name": "epicenter-insurance-registry",
    "version": "1.0.0",
    "description": (
        "Epicenter Insurance Format Registry MCP: maker/checker document-format "
        "mapping tools operating only on approved synthetic or de-identified fixtures."
    ),
}

_PROTOCOL_VERSION = "2024-11-05"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _mcp_error(code: str, message: str, http_status: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={"error": MCPError(code=code, message=message).model_dump()},
    )


# ---------------------------------------------------------------------------
# Synthetic document family registry (demo fixtures)
# ---------------------------------------------------------------------------

_SCHEMA_REGISTRY: dict[str, dict[str, Any]] = {
    "GHS-CORP": {
        "version": "v1.2.0",
        "field_definitions": {
            "issuer_code": "string — corporate issuer identifier",
            "issuer_name": "string — name of the corporate insurer or employer",
            "document_type": "string — e.g. 'Corporate Health Screening Authorization'",
            "insured_name": "string — name of insured employee (no NRIC)",
            "valid_from": "date — coverage start date",
            "valid_to": "date — coverage end date",
            "screening_package": "string — named screening package",
            "requested_items": "array[string] — individual tests listed",
            "billing_arrangement": "string — e.g. 'Direct billing to employer'",
            "corporate_code": "string — employer/TPA code",
        },
        "checkbox_conventions": [
            "Tick marks (✓) indicate selected screening tests",
            "Crossed boxes (✗) indicate exclusions",
            "Unchecked boxes are absent/not applicable",
        ],
    },
    "REFERRAL": {
        "version": "v1.0.0",
        "field_definitions": {
            "issuer_name": "string — referring physician or facility name",
            "document_type": "string — 'Referral Letter'",
            "insured_name": "string — patient name",
            "valid_from": "date — referral date",
            "valid_to": "date — referral expiry date if stated",
            "requested_items": "array[string] — referred services or specialties",
            "authorization_number": "string — referral authorization number if present",
        },
        "checkbox_conventions": [],
    },
    "VOUCHER": {
        "version": "v1.0.0",
        "field_definitions": {
            "issuer_code": "string — voucher issuer code",
            "issuer_name": "string — voucher issuer name",
            "document_type": "string — 'Health Voucher'",
            "valid_from": "date",
            "valid_to": "date",
            "screening_package": "string — voucher-covered service",
            "billing_arrangement": "string — voucher redemption terms",
        },
        "checkbox_conventions": [],
    },
}

_EVIDENCE_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "GHS-CORP": {
        "required_source_fields": [
            "issuer_code", "issuer_name", "document_type", "valid_from",
            "valid_to", "screening_package", "corporate_code",
        ],
        "fixture_test_ids": ["fixture-GHS-001", "fixture-GHS-002", "fixture-GHS-003"],
    },
    "REFERRAL": {
        "required_source_fields": [
            "issuer_name", "document_type", "valid_from", "requested_items",
        ],
        "fixture_test_ids": ["fixture-REF-001", "fixture-REF-002"],
    },
    "VOUCHER": {
        "required_source_fields": [
            "issuer_code", "valid_from", "valid_to", "screening_package",
        ],
        "fixture_test_ids": ["fixture-VCH-001"],
    },
}


# ---------------------------------------------------------------------------
# MCP protocol endpoints
# ---------------------------------------------------------------------------


@router.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "server": _SERVER_INFO["name"]}


@router.post("/initialize")
def initialize(request_body: dict[str, Any]) -> dict[str, Any]:
    return {
        "protocolVersion": _PROTOCOL_VERSION,
        "serverInfo": _SERVER_INFO,
        "capabilities": {"tools": {"listChanged": False}},
    }


@router.get("/tools/list")
@router.post("/tools/list")
def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": "registry_get_schema",
                "description": "Retrieve an approved document-family schema and checkbox conventions.",
                "readOnly": True,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_family": {
                            "type": "string",
                            "description": "Document family code, e.g. 'GHS-CORP'.",
                        },
                    },
                    "required": ["document_family"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "registry_propose_mapping",
                "description": (
                    "Propose a field mapping for a new synthetic form. "
                    "Proposals are staged as pending_review and require maker/checker activation."
                ),
                "readOnly": False,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "form_id": {"type": "string"},
                        "synthetic_fixture": {
                            "type": "object",
                            "description": "Approved synthetic or de-identified fixture data.",
                        },
                    },
                    "required": ["form_id", "synthetic_fixture"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "registry_get_evidence_requirements",
                "description": "Return required source-evidence fields and fixture tests for a document family.",
                "readOnly": True,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_family": {"type": "string"},
                    },
                    "required": ["document_family"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "registry_compare_mapping_versions",
                "description": "Compare a draft mapping with the active version for a document family.",
                "readOnly": True,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "draft_id": {"type": "string"},
                        "active_id": {"type": "string"},
                    },
                    "required": ["draft_id", "active_id"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "registry_get_regression_status",
                "description": "Report regression and review status for a mapping proposal.",
                "readOnly": True,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mapping_id": {"type": "string"},
                    },
                    "required": ["mapping_id"],
                    "additionalProperties": False,
                },
            },
        ]
    }


@router.post("/tools/call")
async def call_tool(
    raw_body: dict[str, Any],
    principal: Annotated[StaffPrincipal, Depends(require_mcp_identity)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    """Dispatch a registry tool call after authentication and authorization."""
    tool_name = raw_body.get("name")
    tool_input = raw_body.get("input", {})

    if not tool_name:
        return _mcp_error("invalid_request", "Missing 'name' field in tool call.")

    try:
        authorize_registry_tool(tool_name, principal)
        result = _dispatch_tool(tool_name, tool_input)
        return JSONResponse(content={"result": result})
    except HTTPException as exc:
        http_status = exc.status_code
        code = "not_found" if http_status == 404 else "forbidden" if http_status == 403 else "tool_error"
        return _mcp_error(code, exc.detail, http_status=200)
    except ValidationError as exc:
        return _mcp_error("invalid_input", f"Input validation failed: {exc.error_count()} error(s).")
    except Exception as exc:
        logger.error("Registry MCP tool error in %s: %s", tool_name, exc)
        return _mcp_error("tool_error", "An internal error occurred.", http_status=500)


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------


def _dispatch_tool(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "registry_get_schema":
        inp = GetSchemaInput.model_validate(tool_input)
        return _get_schema(inp)
    elif tool_name == "registry_propose_mapping":
        inp = ProposeMappingInput.model_validate(tool_input)
        return _propose_mapping(inp)
    elif tool_name == "registry_get_evidence_requirements":
        inp = GetEvidenceRequirementsInput.model_validate(tool_input)
        return _get_evidence_requirements(inp)
    elif tool_name == "registry_compare_mapping_versions":
        inp = CompareMappingVersionsInput.model_validate(tool_input)
        return _compare_mapping_versions(inp)
    elif tool_name == "registry_get_regression_status":
        inp = GetRegressionStatusInput.model_validate(tool_input)
        return _get_regression_status(inp)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown registry tool: {tool_name}",
        )


def _get_schema(inp: GetSchemaInput) -> dict[str, Any]:
    schema = _SCHEMA_REGISTRY.get(inp.document_family.upper())
    if schema is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No schema registered for document family: {inp.document_family}",
        )
    output = SchemaOutput(
        document_family=inp.document_family.upper(),
        version=schema["version"],
        field_definitions=schema["field_definitions"],
        checkbox_conventions=schema["checkbox_conventions"],
        synthetic=True,
    )
    return output.model_dump()


def _propose_mapping(inp: ProposeMappingInput) -> dict[str, Any]:
    proposal_id = f"proposal-{uuid.uuid4().hex[:12]}"
    # Derive proposed fields from the fixture keys — never from live patient data
    proposed_fields = {
        k: f"mapped from fixture field '{k}'"
        for k in inp.synthetic_fixture.keys()
        if not k.startswith("_")
    }
    output = MappingProposalOutput(
        form_id=inp.form_id,
        proposal_id=proposal_id,
        status="pending_review",
        proposed_fields=proposed_fields,
        required_evidence_fields=[
            "issuer_code", "document_type", "valid_from", "valid_to",
        ],
        fixture_tests_required=["fixture-regression-001", "fixture-regression-002"],
        advisory=(
            "This proposal is pending_review. "
            "Only an authorized staff maker/checker activation can promote it."
        ),
        synthetic=True,
    )
    return output.model_dump()


def _get_evidence_requirements(inp: GetEvidenceRequirementsInput) -> dict[str, Any]:
    reqs = _EVIDENCE_REQUIREMENTS.get(inp.document_family.upper())
    if reqs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No evidence requirements registered for: {inp.document_family}",
        )
    output = EvidenceRequirementsOutput(
        document_family=inp.document_family.upper(),
        required_source_fields=reqs["required_source_fields"],
        fixture_test_ids=reqs["fixture_test_ids"],
        synthetic=True,
    )
    return output.model_dump()


def _compare_mapping_versions(inp: CompareMappingVersionsInput) -> dict[str, Any]:
    output = MappingVersionComparisonOutput(
        draft_id=inp.draft_id,
        active_id=inp.active_id,
        compatible=True,
        field_delta={
            "added": [],
            "removed": [],
            "changed": [],
        },
        regression_required=True,
        synthetic=True,
    )
    return output.model_dump()


def _get_regression_status(inp: GetRegressionStatusInput) -> dict[str, Any]:
    output = RegressionStatusOutput(
        mapping_id=inp.mapping_id,
        regression_status="pending",
        test_results=[],
        review_status="pending_review",
        synthetic=True,
    )
    return output.model_dump()
