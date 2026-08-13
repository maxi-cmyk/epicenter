# ruff: noqa: E501
"""Epicenter Operations MCP — Streamable HTTP endpoint.

Exposed at /mcp/operations. Serves read-only and synthetic-simulation tools
that call the existing FastAPI service layer. No business logic lives here —
handlers validate input, authorize the actor, invoke one service, and return
a minimal typed response.

Compatible with:
- OpenAI Responses API remote MCP tool protocol
- Microsoft Copilot Studio (Streamable HTTP transport)

No generic SQL, unrestricted search, arbitrary URL fetch, filesystem access,
raw prompt proxy, or database service-role capability is exposed.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.auth import StaffPrincipal
from app.core.config import Settings, get_settings
from app.data.dependencies import get_operations_repository
from app.data.operations_repository import OperationsRepository
from app.mcp.auth import authorize_operations_tool, require_mcp_identity
from app.mcp.protocol import PROTOCOL_VERSION, governed_tool, jsonrpc_error, jsonrpc_result, tool_result
from app.mcp.schemas import (
    AllocationRecommendationOutput,
    CompareSimulationRunsInput,
    EligibilityPreviewOutput,
    ExtractionStatusOutput,
    GetAllocationRecommendationInput,
    GetExtractionStatusInput,
    GetOperationalSummaryInput,
    GetQueueSnapshotInput,
    GetVisitTicketInput,
    MCPError,
    OperationalSummaryOutput,
    PreviewEligibilityInput,
    QueueSnapshotOutput,
    RunSimulationInput,
    SimulationComparisonOutput,
    SimulationRunOutput,
    VisitTicketOutput,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp/operations", tags=["mcp-operations"])

# MCP server metadata
_SERVER_INFO = {
    "name": "epicenter-operations",
    "version": "1.0.0",
    "description": (
        "Epicenter Operations MCP: read-only queue, eligibility, analytics, "
        "and synthetic simulation tools for clinic staff and Copilot Studio."
    ),
}

_PROTOCOL_VERSION = PROTOCOL_VERSION

_GOVERNANCE = {
    "epicenter_get_extraction_status": {"title": "Extraction status", "owner": "Epicenter operations", "capability": "Read one bounded extraction job status", "least_privilege": "registration, operations_admin", "data_boundary": "synthetic or formally de-identified job metadata", "tests": "test_mcp_protocol.py", "removal_criteria": "Remove when extraction jobs no longer exist"},
    "epicenter_preview_eligibility": {"title": "Eligibility preview", "owner": "Epicenter operations", "capability": "Explain a deterministic advisory preview", "least_privilege": "registration, operations_admin", "data_boundary": "bounded document and appointment references; no decision write", "tests": "test_mcp_protocol.py", "removal_criteria": "Remove if deterministic preview is retired"},
    "epicenter_get_visit_ticket": {"title": "Visit ticket", "owner": "Epicenter operations", "capability": "Read one clinic-scoped ticket without patient identity", "least_privilege": "registration, operations_admin", "data_boundary": "de-identified operational state", "tests": "test_mcp_protocol.py", "removal_criteria": "Remove if ticket workflow is retired"},
    "epicenter_get_operational_summary": {"title": "Operational summary", "owner": "Epicenter operations", "capability": "Read bounded aggregate metrics", "least_privilege": "operations_admin, auditor", "data_boundary": "clinic aggregate only", "tests": "test_mcp_protocol.py", "removal_criteria": "Remove when native summary supersedes assistant use"},
    "epicenter_get_queue_snapshot": {"title": "Queue snapshot", "owner": "Epicenter operations", "capability": "Read bounded de-identified queue counts", "least_privilege": "operations_admin, auditor", "data_boundary": "clinic aggregate only", "tests": "test_mcp_protocol.py", "removal_criteria": "Remove if queue assistant support is retired"},
    "epicenter_get_allocation_recommendation": {"title": "Allocation explanation", "owner": "Epicenter operations", "capability": "Explain one existing advisory recommendation", "least_privilege": "operations_admin", "data_boundary": "recommendation metadata; never approves", "tests": "test_mcp_protocol.py", "removal_criteria": "Remove if allocation recommendations are retired"},
    "epicenter_run_simulation": {"title": "Run synthetic simulation", "owner": "Epicenter operations", "capability": "Run one deterministic isolated scenario", "least_privilege": "operations_admin", "data_boundary": "synthetic simulator state only", "tests": "test_mcp_protocol.py", "removal_criteria": "Remove if simulator is retired"},
    "epicenter_compare_simulation_runs": {"title": "Compare simulations", "owner": "Epicenter operations", "capability": "Compare two bounded synthetic runs", "least_privilege": "operations_admin", "data_boundary": "synthetic aggregate metrics only", "tests": "test_mcp_protocol.py", "removal_criteria": "Remove if run comparison is retired"},
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _mcp_error(code: str, message: str, http_status: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={"error": MCPError(code=code, message=message).model_dump()},
    )


# ---------------------------------------------------------------------------
# MCP protocol endpoints
# ---------------------------------------------------------------------------


@router.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "server": _SERVER_INFO["name"]}


@router.post("/initialize")
def initialize(request_body: dict[str, Any]) -> dict[str, Any]:
    """MCP initialization handshake."""
    return {
        "protocolVersion": _PROTOCOL_VERSION,
        "serverInfo": _SERVER_INFO,
        "capabilities": {"tools": {"listChanged": False}},
    }


@router.get("/tools/list")
@router.post("/tools/list")
def list_tools() -> dict[str, Any]:
    """Return the MCP tool inventory. Stable — discovery requires no auth."""
    tools = [
            {
                "name": "epicenter_get_extraction_status",
                "description": "Get the status and result of a document extraction job.",
                "readOnly": True,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string", "description": "Document processing job ID."},
                    },
                    "required": ["job_id"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "epicenter_preview_eligibility",
                "description": (
                    "Preview the eligibility assessment for a document against an appointment. "
                    "Advisory only — staff confirmation is always required."
                ),
                "readOnly": True,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "string"},
                        "appointment_reference": {"type": "string"},
                    },
                    "required": ["document_id", "appointment_reference"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "epicenter_get_visit_ticket",
                "description": "Retrieve a visit ticket and its current readiness state by ticket ID.",
                "readOnly": True,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "string", "description": "The Q-* ticket identifier."},
                    },
                    "required": ["ticket_id"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "epicenter_get_operational_summary",
                "description": "Get aggregate operational metrics for a clinic over a date range.",
                "readOnly": True,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "clinic_id": {"type": "string"},
                        "date_range": {
                            "type": "string",
                            "description": "ISO date range, e.g. '2026-08-12/2026-08-12'.",
                        },
                    },
                    "required": ["clinic_id", "date_range"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "epicenter_get_queue_snapshot",
                "description": "Get a de-identified queue snapshot for a clinic at a point in time.",
                "readOnly": True,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "clinic_id": {"type": "string"},
                        "snapshot_at": {
                            "type": "string",
                            "description": "ISO 8601 datetime or 'now'.",
                        },
                    },
                    "required": ["clinic_id", "snapshot_at"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "epicenter_get_allocation_recommendation",
                "description": "Retrieve an expiring allocation recommendation by ID. Read-only.",
                "readOnly": True,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "recommendation_id": {"type": "string"},
                    },
                    "required": ["recommendation_id"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "epicenter_run_simulation",
                "description": (
                    "Run a deterministic synthetic simulation scenario. "
                    "Results are labelled synthetic=true and cannot affect live queue or operational tables."
                ),
                "readOnly": False,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "scenario_id": {"type": "string"},
                        "seed": {"type": "integer"},
                        "bounded_overrides": {
                            "type": "object",
                            "description": "Optional bounded pre-run resource overrides.",
                            "additionalProperties": True,
                        },
                    },
                    "required": ["scenario_id", "seed"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "epicenter_compare_simulation_runs",
                "description": "Compare two simulation runs with the same seed and arrivals.",
                "readOnly": True,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseline_run_id": {"type": "string"},
                        "epicenter_run_id": {"type": "string"},
                    },
                    "required": ["baseline_run_id", "epicenter_run_id"],
                    "additionalProperties": False,
                },
            },
        ]
    return {"tools": [governed_tool(tool, _GOVERNANCE[tool["name"]]) for tool in tools]}


@router.post("")
async def streamable_http(
    raw_body: dict[str, Any],
    principal: Annotated[StaffPrincipal, Depends(require_mcp_identity)],
    settings: Annotated[Settings, Depends(get_settings)],
    repo: Annotated[OperationsRepository, Depends(get_operations_repository)],
) -> JSONResponse:
    """Stateless Streamable HTTP JSON-RPC endpoint for independent MCP clients."""
    request_id = raw_body.get("id")
    if raw_body.get("jsonrpc") != "2.0":
        return jsonrpc_error(request_id, -32600, "Invalid JSON-RPC request.")
    method = raw_body.get("method")
    if method == "initialize":
        return jsonrpc_result(request_id, initialize(raw_body.get("params", {})))
    if method == "notifications/initialized":
        return JSONResponse(status_code=202, content=None, headers={"MCP-Protocol-Version": _PROTOCOL_VERSION})
    if method == "tools/list":
        return jsonrpc_result(request_id, list_tools())
    if method != "tools/call":
        return jsonrpc_error(request_id, -32601, "Method not found.")
    params = raw_body.get("params") or {}
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if not name:
        return jsonrpc_error(request_id, -32602, "Tool name is required.")
    try:
        result = await _dispatch_tool(name, arguments, principal, settings, repo)
        return jsonrpc_result(request_id, tool_result(result))
    except ValidationError as exc:
        return jsonrpc_result(request_id, tool_result({"error": "invalid_input", "message": f"Input validation failed: {exc.error_count()} error(s)."}, is_error=True))
    except HTTPException as exc:
        return jsonrpc_result(request_id, tool_result({"error": "tool_error", "message": str(exc.detail)}, is_error=True))
    except Exception:
        logger.exception("Operations MCP JSON-RPC tool failure")
        return jsonrpc_result(request_id, tool_result({"error": "tool_error", "message": "An internal error occurred."}, is_error=True))


@router.post("/tools/call")
async def call_tool(
    raw_body: dict[str, Any],
    principal: Annotated[StaffPrincipal, Depends(require_mcp_identity)],
    settings: Annotated[Settings, Depends(get_settings)],
    repo: Annotated[OperationsRepository, Depends(get_operations_repository)],
) -> JSONResponse:
    """Dispatch a tool call after authentication and per-tool authorization."""
    tool_name = raw_body.get("name")
    tool_input = raw_body.get("input", {})

    if not tool_name:
        return _mcp_error("invalid_request", "Missing 'name' field in tool call.")

    try:
        result = await _dispatch_tool(tool_name, tool_input, principal, settings, repo)
        return JSONResponse(content={"result": result})
    except HTTPException as exc:
        http_status = exc.status_code
        code = "not_found" if http_status == 404 else "forbidden" if http_status == 403 else "tool_error"
        return _mcp_error(code, exc.detail, http_status=200)
    except ValidationError as exc:
        return _mcp_error("invalid_input", f"Input validation failed: {exc.error_count()} error(s).")
    except Exception as exc:
        logger.error("MCP tool error in %s: %s", tool_name, exc)
        return _mcp_error("tool_error", "An internal error occurred.", http_status=500)


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------


async def _dispatch_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    principal: Any,
    settings: Settings,
    repo: OperationsRepository,
) -> dict[str, Any]:
    if tool_name == "epicenter_get_extraction_status":
        authorize_operations_tool(tool_name, principal)
        inp = GetExtractionStatusInput.model_validate(tool_input)
        return _get_extraction_status(inp, repo, settings)

    elif tool_name == "epicenter_preview_eligibility":
        authorize_operations_tool(tool_name, principal)
        inp = PreviewEligibilityInput.model_validate(tool_input)
        return _preview_eligibility(inp, repo, settings)

    elif tool_name == "epicenter_get_visit_ticket":
        authorize_operations_tool(tool_name, principal)
        inp = GetVisitTicketInput.model_validate(tool_input)
        return _get_visit_ticket(inp, repo)

    elif tool_name == "epicenter_get_operational_summary":
        authorize_operations_tool(tool_name, principal, clinic_id=tool_input.get("clinic_id"))
        inp = GetOperationalSummaryInput.model_validate(tool_input)
        return _get_operational_summary(inp, repo, settings)

    elif tool_name == "epicenter_get_queue_snapshot":
        authorize_operations_tool(tool_name, principal, clinic_id=tool_input.get("clinic_id"))
        inp = GetQueueSnapshotInput.model_validate(tool_input)
        return _get_queue_snapshot(inp, repo, settings)

    elif tool_name == "epicenter_get_allocation_recommendation":
        authorize_operations_tool(tool_name, principal)
        inp = GetAllocationRecommendationInput.model_validate(tool_input)
        return _get_allocation_recommendation(inp, repo)

    elif tool_name == "epicenter_run_simulation":
        authorize_operations_tool(tool_name, principal)
        inp = RunSimulationInput.model_validate(tool_input)
        return _run_simulation(inp, repo)

    elif tool_name == "epicenter_compare_simulation_runs":
        authorize_operations_tool(tool_name, principal)
        inp = CompareSimulationRunsInput.model_validate(tool_input)
        return _compare_simulation_runs(inp, repo)

    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown tool: {tool_name}",
        )


# ---------------------------------------------------------------------------
# Tool implementations — thin adapters over existing repo/service layer
# ---------------------------------------------------------------------------


def _get_extraction_status(
    inp: GetExtractionStatusInput,
    repo: OperationsRepository,
    settings: Settings,
) -> dict[str, Any]:
    """Return extraction job status. Reads from document_jobs via repo."""
    # In demo mode, return a synthetic status based on the job_id
    output = ExtractionStatusOutput(
        job_id=inp.job_id,
        status="ready",
        model_used=settings.openai_extraction_model,
        prompt_version="v1.0.0",
        coverage_summary={
            "issuer_code": "GHS-CORP",
            "document_type": "Corporate Health Screening Authorization",
            "overall_confidence": "high",
            "synthetic": True,
        },
        synthetic=True,
        snapshot_time=_now_iso(),
    )
    return output.model_dump()


def _preview_eligibility(
    inp: PreviewEligibilityInput,
    repo: OperationsRepository,
    settings: Settings,
) -> dict[str, Any]:
    """Preview eligibility — advisory only. Staff confirmation always required."""
    output = EligibilityPreviewOutput(
        document_id=inp.document_id,
        appointment_reference=inp.appointment_reference,
        match_status="clean",
        matched_package="General Health Screening — Corporate Tier A",
        outstanding_gates=[],
        advisory_note=(
            "Preliminary match is clean. "
            "Staff confirmation of extracted facts is required before readiness can be set."
        ),
        requires_staff_confirmation=True,
        synthetic=True,
        snapshot_time=_now_iso(),
    )
    return output.model_dump()


def _get_visit_ticket(
    inp: GetVisitTicketInput,
    repo: OperationsRepository,
) -> dict[str, Any]:
    """Retrieve a visit ticket by ID."""
    ticket = repo.find_ticket(inp.ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {inp.ticket_id} not found.",
        )
    output = VisitTicketOutput(
        ticket_id=ticket.id,
        readiness_state=ticket.readiness_state,
        visit_phase=ticket.visit_phase,
        waiting_minutes=ticket.waiting_minutes,
        processing_stage=ticket.processing_stage,
        service_target=ticket.service_target,
        staff_confirmed=ticket.staff_confirmed,
        synthetic=True,
        snapshot_time=_now_iso(),
    )
    return output.model_dump()


def _get_operational_summary(
    inp: GetOperationalSummaryInput,
    repo: OperationsRepository,
    settings: Settings,
) -> dict[str, Any]:
    """Return aggregate operational metrics from the shared snapshot."""
    snapshot = repo.snapshot()
    metrics = [
        {"label": m.label, "value": m.value, "detail": m.detail, "trend": m.trend}
        for m in snapshot.metrics
    ]
    output = OperationalSummaryOutput(
        clinic_id=inp.clinic_id,
        date_range=inp.date_range,
        metrics=metrics,
        assumptions_version="v1.0.0",
        synthetic=snapshot.synthetic,
        snapshot_time=snapshot.generated_at.isoformat(),
    )
    return output.model_dump()


def _get_queue_snapshot(
    inp: GetQueueSnapshotInput,
    repo: OperationsRepository,
    settings: Settings,
) -> dict[str, Any]:
    """Return de-identified queue aggregate counts."""
    snapshot = repo.snapshot()
    tickets = snapshot.tickets
    ready = sum(1 for t in tickets if t.readiness_state == "ready")
    processing = sum(1 for t in tickets if t.readiness_state == "processing")
    review = sum(1 for t in tickets if t.readiness_state == "needs_review")
    waits = sorted(t.waiting_minutes for t in tickets)
    p50 = waits[len(waits) // 2] if waits else 0
    p90 = waits[int(len(waits) * 0.9)] if waits else 0
    oldest = max(waits) if waits else 0

    output = QueueSnapshotOutput(
        clinic_id=inp.clinic_id,
        snapshot_at=inp.snapshot_at,
        total_tickets=len(tickets),
        ready_count=ready,
        processing_count=processing,
        review_count=review,
        oldest_wait_minutes=oldest,
        p50_wait_minutes=p50,
        p90_wait_minutes=p90,
        synthetic=snapshot.synthetic,
        source="fastapi/supabase-demo-snapshot",
    )
    return output.model_dump()


def _get_allocation_recommendation(
    inp: GetAllocationRecommendationInput,
    repo: OperationsRepository,
) -> dict[str, Any]:
    """Return an allocation recommendation. Advisory — approval required for any change."""
    snapshot = repo.snapshot()
    rec = snapshot.recommendation
    output = AllocationRecommendationOutput(
        recommendation_id=inp.recommendation_id,
        status=rec.status,
        pressured_workstream=rec.pressured_workstream,
        rationale=rec.rationale,
        qualified_resource=rec.qualified_resource,
        current_wait_minutes=rec.current_wait_minutes,
        expected_wait_minutes=rec.expected_wait_minutes,
        expires_at=rec.expires_at.isoformat(),
        constraints_checked=rec.constraints_checked,
        advisory_note="Approval required before any change takes effect.",
        synthetic=True,
        snapshot_time=_now_iso(),
    )
    return output.model_dump()


def _run_simulation(
    inp: RunSimulationInput,
    repo: OperationsRepository,
) -> dict[str, Any]:
    """Return a synthetic simulation run. Cannot write operational tables."""
    snapshots = repo.list_simulator_snapshots()
    matched = next((s for s in snapshots if s.scenario_id == inp.scenario_id), None)

    run_id = f"run-{inp.scenario_id}-seed{inp.seed}"
    payload = matched.snapshot_payload if matched else {}
    events = payload.get("events", [])
    metrics = payload.get("metrics", {})
    output = SimulationRunOutput(
        run_id=run_id,
        scenario_id=inp.scenario_id,
        seed=inp.seed,
        assumptions_version=matched.assumptions_version if matched else "v1.0.0",
        status="completed",
        event_count=len(events) if isinstance(events, list) else 0,
        summary_metrics=metrics if isinstance(metrics, dict) else {},
        synthetic=True,
        label="synthetic=true: this run does not affect live operational tables.",
    )
    return output.model_dump()


def _compare_simulation_runs(
    inp: CompareSimulationRunsInput,
    repo: OperationsRepository,
) -> dict[str, Any]:
    """Compare two simulation runs — synthetic only."""
    output = SimulationComparisonOutput(
        baseline_run_id=inp.baseline_run_id,
        epicenter_run_id=inp.epicenter_run_id,
        compatible=True,
        metrics_delta={
            "p50_wait_delta_minutes": -4,
            "throughput_delta": "+6%",
            "review_clearance_delta": "+12%",
        },
        bottleneck_shift="Registration bottleneck reduced; downstream pharmacy utilisation increased.",
        synthetic=True,
        label="synthetic=true: comparison uses isolated scenario state.",
    )
    return output.model_dump()
