"""Authenticated nurse assistant.

FastAPI orchestration route calls this module. Flow:
1. Validate the actor (StaffPrincipal) and clinic scope.
2. Select only task-relevant MCP tools for this actor's role.
3. Call the OpenAI Responses API with those tools.
4. Re-authorize every tool execution before dispatching to the MCP handler.
5. Return a grounded AssistantMessage with snapshot/source labels.

Constraints from openai_integration.md:
- The browser never receives the OpenAI API key.
- OpenAI may summarize, compare, and explain approved tool results only.
- It may NOT approve readiness, correct canonical facts, attest identity/e-card
  checks, confirm billing, reorder the live queue, infer clinical urgency, or
  approve allocations.
- Every tool call is re-authorized against the signed-in actor, role, and clinic.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app.ai.client import create_response
from app.ai.schemas import AssistantMessage
from app.core.auth import StaffPrincipal
from app.core.config import Settings

logger = logging.getLogger(__name__)

# Prompt version for reproducibility tracking
ASSISTANT_PROMPT_VERSION = "v1.0.0"

_SYSTEM_PROMPT = """
You are the Epicenter nurse assistant. You help clinic staff understand operational
data — queue status, readiness summaries, simulation results, and allocation advice.

Rules:
1. Only summarize, compare, and explain the tool results you are given.
2. Never approve readiness, correct canonical patient or coverage facts, attest
   identity or e-card checks, confirm billing, reorder the live queue, infer
   clinical urgency, or approve resource allocations.
3. Always state the source and snapshot time of any data you reference.
4. If a tool result is labelled synthetic=true, say so clearly.
5. If you do not have the information to answer, say so — do not speculate.
6. Keep answers concise and actionable for a clinic nurse.
""".strip()

# Role-to-allowed-tool mapping (conservative — tools expand with task context)
_ROLE_TOOL_ALLOWLIST: dict[str, set[str]] = {
    "registration_staff": {
        "epicenter_get_visit_ticket",
        "epicenter_get_extraction_status",
        "epicenter_preview_eligibility",
    },
    "operations_admin": {
        "epicenter_get_visit_ticket",
        "epicenter_get_extraction_status",
        "epicenter_preview_eligibility",
        "epicenter_get_queue_snapshot",
        "epicenter_get_operational_summary",
        "epicenter_get_allocation_recommendation",
        "epicenter_run_simulation",
        "epicenter_compare_simulation_runs",
    },
    "auditor": {
        "epicenter_get_operational_summary",
        "epicenter_get_queue_snapshot",
    },
}


def _allowed_tools_for_role(role: str) -> set[str]:
    """Return the set of MCP tool names permitted for this role."""
    return _ROLE_TOOL_ALLOWLIST.get(role, set())


def _build_tool_definitions(allowed: set[str]) -> list[dict[str, Any]]:
    """Build OpenAI tool definitions filtered to the actor's allowed set.

    Each tool definition references the MCP endpoint via the tool name.
    In the Responses API, these are passed as remote MCP tool specs;
    the actual dispatch happens through the FastAPI MCP handler.
    """
    all_tools = [
        {
            "type": "function",
            "name": "epicenter_get_visit_ticket",
            "description": "Retrieve a visit ticket and its current readiness state by ticket ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "The Q-* ticket identifier."},
                },
                "required": ["ticket_id"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": "epicenter_get_extraction_status",
            "description": "Get the status and result of a document extraction job.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "Document processing job ID."},
                },
                "required": ["job_id"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": "epicenter_preview_eligibility",
            "description": (
                "Preview the eligibility assessment for a document against an appointment. "
                "Advisory only — staff confirmation is always required."
            ),
            "parameters": {
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
            "type": "function",
            "name": "epicenter_get_queue_snapshot",
            "description": "Get a de-identified queue snapshot for a clinic at a point in time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "clinic_id": {"type": "string"},
                    "snapshot_at": {
                        "type": "string",
                        "description": "ISO 8601 datetime, or 'now'.",
                    },
                },
                "required": ["clinic_id", "snapshot_at"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": "epicenter_get_operational_summary",
            "description": "Get aggregate operational metrics for a clinic over a date range.",
            "parameters": {
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
            "type": "function",
            "name": "epicenter_get_allocation_recommendation",
            "description": "Retrieve an expiring allocation recommendation by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recommendation_id": {"type": "string"},
                },
                "required": ["recommendation_id"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": "epicenter_run_simulation",
            "description": (
                "Run a deterministic synthetic simulation scenario. "
                "Results are labelled synthetic=true and cannot affect live queue or operational tables."
            ),
            "parameters": {
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
            "type": "function",
            "name": "epicenter_compare_simulation_runs",
            "description": "Compare two simulation runs with the same seed and arrivals.",
            "parameters": {
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
    return [t for t in all_tools if t["name"] in allowed]


async def run_nurse_assistant(
    client: AsyncOpenAI,
    *,
    settings: Settings,
    principal: StaffPrincipal,
    user_message: str,
    tool_dispatcher: "ToolDispatcher",
) -> AssistantMessage:
    """Run one nurse assistant turn.

    Args:
        client: Shared AsyncOpenAI client.
        settings: Application settings.
        principal: Verified staff principal (role + clinic scope).
        user_message: The nurse's question or instruction.
        tool_dispatcher: Callable that executes a named tool after re-authorization.

    Returns:
        AssistantMessage with grounded content and source labels.
    """
    allowed = _allowed_tools_for_role(principal.role)
    if not allowed:
        return AssistantMessage(
            content="Your role does not have access to assistant tools for this query.",
            source_labels=[],
        )

    tools = _build_tool_definitions(allowed)
    input_messages: list[dict[str, Any]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    source_labels: list[str] = []
    snapshot_time: str | None = None
    response_id: str | None = None

    try:
        response = await create_response(
            client,
            model=settings.openai_model,
            input_messages=input_messages,
            tools=tools,
            store=False,
            metadata={
                "actor_role": principal.role,
                "clinic_id": principal.clinic_id,
                "assistant_prompt_version": ASSISTANT_PROMPT_VERSION,
            },
        )
        response_id = getattr(response, "id", None)

        # Process any tool calls the model requested
        tool_results: list[dict[str, Any]] = []
        for item in getattr(response, "output", []):
            if getattr(item, "type", None) == "function_call":
                tool_name = item.name
                if tool_name not in allowed:
                    logger.warning(
                        "Model requested disallowed tool %s for role %s — skipping",
                        tool_name,
                        principal.role,
                    )
                    continue
                try:
                    tool_args = json.loads(item.arguments)
                    result, label, snap = await tool_dispatcher(
                        tool_name, tool_args, principal
                    )
                    source_labels.append(label)
                    if snap:
                        snapshot_time = snap
                    tool_results.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(result),
                    })
                except Exception as exc:
                    logger.error("Tool execution failed for %s: %s", tool_name, exc)
                    tool_results.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps({"error": "Tool execution failed."}),
                    })

        # If tools were called, do a follow-up turn with results
        if tool_results:
            input_messages = input_messages + list(getattr(response, "output", [])) + tool_results
            response = await create_response(
                client,
                model=settings.openai_model,
                input_messages=input_messages,
                store=False,
            )
            response_id = getattr(response, "id", None)

        content = getattr(response, "output_text", "")
        if not content:
            content = "I was unable to retrieve a response. Please try again."

    except OpenAIError as exc:
        logger.error("OpenAI assistant error: %s", type(exc).__name__)
        return AssistantMessage(
            content=(
                "The assistant is temporarily unavailable. "
                "Please use the dashboard directly."
            ),
            source_labels=[],
        )

    return AssistantMessage(
        content=content,
        source_labels=source_labels,
        snapshot_time=snapshot_time,
        synthetic=True,
        openai_response_id=response_id,
    )


# ---------------------------------------------------------------------------
# Type alias for the tool dispatcher injected from FastAPI
# ---------------------------------------------------------------------------

from typing import Protocol, Tuple


class ToolDispatcher(Protocol):
    """Execute a named MCP tool after re-authorizing the actor."""

    async def __call__(
        self,
        tool_name: str,
        args: dict[str, Any],
        principal: StaffPrincipal,
    ) -> Tuple[Any, str, str | None]:
        """Returns (result_dict, source_label, snapshot_time_or_None)."""
        ...
