"""MCP request/response schemas for both Epicenter custom MCP servers.

All schemas use extra='forbid' so unexpected fields are rejected cleanly.
Tool names match the contracts in openai_integration.md and techStack.md.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


class MCPError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Operations MCP — tool inputs
# ---------------------------------------------------------------------------


class GetExtractionStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job_id: Annotated[str, Field(min_length=1, max_length=128)]


class PreviewEligibilityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_id: Annotated[str, Field(min_length=1, max_length=128)]
    appointment_reference: Annotated[str, Field(min_length=1, max_length=128)]


class GetVisitTicketInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: Annotated[str, Field(min_length=1, max_length=40)]


class GetOperationalSummaryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    clinic_id: Annotated[str, Field(min_length=1, max_length=80)]
    date_range: Annotated[
        str,
        Field(
            min_length=10,
            max_length=50,
            description="ISO date range, e.g. '2026-08-12/2026-08-12'.",
        ),
    ]


class GetQueueSnapshotInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    clinic_id: Annotated[str, Field(min_length=1, max_length=80)]
    snapshot_at: Annotated[
        str,
        Field(
            min_length=1,
            max_length=30,
            description="ISO 8601 datetime or 'now'.",
        ),
    ]


class GetAllocationRecommendationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recommendation_id: Annotated[str, Field(min_length=1, max_length=128)]


class RunSimulationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: Annotated[str, Field(min_length=1, max_length=128)]
    seed: int = Field(ge=0, le=2**31 - 1)
    bounded_overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional bounded pre-run resource overrides. Simulation only.",
    )


class CompareSimulationRunsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    baseline_run_id: Annotated[str, Field(min_length=1, max_length=128)]
    epicenter_run_id: Annotated[str, Field(min_length=1, max_length=128)]


# ---------------------------------------------------------------------------
# Operations MCP — tool outputs
# ---------------------------------------------------------------------------


class ExtractionStatusOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job_id: str
    status: str  # queued | processing | ready | failed
    model_used: str | None = None
    prompt_version: str | None = None
    coverage_summary: dict[str, Any] | None = None
    synthetic: bool = True
    snapshot_time: str


class EligibilityPreviewOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_id: str
    appointment_reference: str
    match_status: str  # clean | ambiguous | no_match
    matched_package: str | None = None
    outstanding_gates: list[str] = Field(default_factory=list)
    advisory_note: str
    requires_staff_confirmation: bool = True
    synthetic: bool = True
    snapshot_time: str


class VisitTicketOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: str
    readiness_state: str
    visit_phase: str
    waiting_minutes: int
    processing_stage: str
    service_target: str
    staff_confirmed: bool
    synthetic: bool = True
    snapshot_time: str


class OperationalSummaryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    clinic_id: str
    date_range: str
    metrics: list[dict[str, Any]]
    assumptions_version: str
    synthetic: bool = True
    snapshot_time: str


class QueueSnapshotOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    clinic_id: str
    snapshot_at: str
    total_tickets: int
    ready_count: int
    processing_count: int
    review_count: int
    oldest_wait_minutes: int
    p50_wait_minutes: int
    p90_wait_minutes: int
    synthetic: bool = True
    source: str


class AllocationRecommendationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recommendation_id: str
    status: str
    pressured_workstream: str
    rationale: str
    qualified_resource: str
    current_wait_minutes: int
    expected_wait_minutes: int
    expires_at: str
    constraints_checked: list[str]
    advisory_note: str = "Approval required before any change takes effect."
    synthetic: bool = True
    snapshot_time: str


class SimulationRunOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    scenario_id: str
    seed: int
    assumptions_version: str
    status: str
    event_count: int
    summary_metrics: dict[str, Any]
    synthetic: bool = True
    label: str = "synthetic=true: this run does not affect live operational tables."


class SimulationComparisonOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    baseline_run_id: str
    epicenter_run_id: str
    compatible: bool
    metrics_delta: dict[str, Any]
    bottleneck_shift: str | None = None
    synthetic: bool = True
    label: str = "synthetic=true: comparison uses isolated scenario state."


# ---------------------------------------------------------------------------
# Insurance Format Registry MCP — tool inputs
# ---------------------------------------------------------------------------


class GetSchemaInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_family: Annotated[str, Field(min_length=1, max_length=120)]


class ProposeMappingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    form_id: Annotated[str, Field(min_length=1, max_length=128)]
    fixture_classification: Annotated[
        str,
        Field(pattern="^(synthetic|formally_deidentified)$"),
    ]
    approval_reference: Annotated[str, Field(min_length=3, max_length=160)]
    synthetic_fixture: dict[str, Any] = Field(
        description="Approved synthetic or formally de-identified fixture data only.",
    )


class ReviewMappingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_id: Annotated[str, Field(min_length=1, max_length=128)]
    decision: Annotated[str, Field(pattern="^(approved|rejected)$")]
    reason: Annotated[str, Field(min_length=3, max_length=500)]


class GetEvidenceRequirementsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_family: Annotated[str, Field(min_length=1, max_length=120)]


class CompareMappingVersionsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    draft_id: Annotated[str, Field(min_length=1, max_length=128)]
    active_id: Annotated[str, Field(min_length=1, max_length=128)]


class GetRegressionStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mapping_id: Annotated[str, Field(min_length=1, max_length=128)]


# ---------------------------------------------------------------------------
# Insurance Format Registry MCP — tool outputs
# ---------------------------------------------------------------------------


class SchemaOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_family: str
    version: str
    field_definitions: dict[str, Any]
    checkbox_conventions: list[str]
    synthetic: bool = True


class MappingProposalOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    form_id: str
    proposal_id: str
    status: str = "pending_review"
    proposed_fields: dict[str, Any]
    required_evidence_fields: list[str]
    fixture_tests_required: list[str]
    advisory: str = (
        "This proposal is pending_review. "
        "Only an authorized staff maker/checker activation can promote it."
    )
    synthetic: bool = True


class MappingReviewOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_id: str
    status: str
    maker_reference: str
    checker_reference: str
    reviewed_at: str
    reason: str
    synthetic: bool = True


class EvidenceRequirementsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_family: str
    required_source_fields: list[str]
    fixture_test_ids: list[str]
    synthetic: bool = True


class MappingVersionComparisonOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    draft_id: str
    active_id: str
    compatible: bool
    field_delta: dict[str, Any]
    regression_required: bool
    synthetic: bool = True


class RegressionStatusOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mapping_id: str
    regression_status: str  # pending | passed | failed
    test_results: list[dict[str, Any]]
    review_status: str  # pending_review | approved | rejected
    synthetic: bool = True
