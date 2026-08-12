from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ReadinessState(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    NEEDS_REVIEW = "needs_review"


class VisitPhase(StrEnum):
    INCOMING = "incoming"
    ONGOING = "ongoing"
    FINISHED = "finished"


class IntakeType(StrEnum):
    BOOKED = "booked"
    WALK_IN = "walk_in"


class ServiceTarget(StrEnum):
    ON_TRACK = "on_track"
    APPROACHING = "approaching"
    OVER_TARGET = "over_target"


class CoverageAction(StrEnum):
    REUSE = "reuse"
    REPLACE = "replace"


class PatientSubmissionOutcome(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"


class PatientAccountSession(BaseModel):
    patient_id: int
    source_record_key: str
    synthetic: bool = True


class QueueTicket(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    intake_type: IntakeType
    visit_phase: VisitPhase
    readiness_state: ReadinessState
    readiness_reason: str
    scheduled_at: datetime | None = None
    checked_in_at: datetime | None = None
    original_ordering_at: datetime
    waiting_minutes: int = Field(ge=0)
    expected_counter: str | None = None
    actual_counter: str | None = None
    processing_stage: str
    service_target: ServiceTarget = ServiceTarget.ON_TRACK
    staff_confirmed: bool = False
    clinical_escalation: bool = False
    version: int = Field(default=1, ge=1)


class ReviewCase(BaseModel):
    id: str
    ticket_id: str
    patient_name: str
    reason_code: str
    reason_label: str
    document_name: str | None = None
    evidence_summary: str
    waiting_minutes: int = Field(ge=0)
    service_target: ServiceTarget
    next_action: str


class AllocationRecommendation(BaseModel):
    id: str
    status: str
    pressured_workstream: str
    rationale: str
    qualified_resource: str
    current_wait_minutes: int
    expected_wait_minutes: int
    expires_at: datetime
    constraints_checked: list[str]
    version: int = Field(default=1, ge=1)


class Metric(BaseModel):
    label: str
    value: str
    detail: str
    trend: str | None = None


class ActivityEvent(BaseModel):
    id: str
    occurred_at: datetime
    label: str
    detail: str
    tone: str


class DashboardSnapshot(BaseModel):
    generated_at: datetime
    clinic_name: str
    synthetic: bool = True
    metrics: list[Metric]
    tickets: list[QueueTicket]
    review_cases: list[ReviewCase]
    recommendation: AllocationRecommendation
    activity: list[ActivityEvent]


class SimulatorSnapshot(BaseModel):
    id: str
    scenario_id: str
    scenario_version: str
    seed: int
    assumptions_version: str
    snapshot_hash: str
    snapshot_payload: dict[str, object]
    synthetic: bool = True


class StaffSession(BaseModel):
    role: str
    clinic_id: str


class TicketTransitionRequest(BaseModel):
    readiness_state: ReadinessState
    reason: str
    staff_confirmed: bool = False
    expected_version: int = Field(default=1, ge=1)
    idempotency_key: str = Field(default="demo-transition", min_length=8, max_length=128)


class RecommendationDecisionRequest(BaseModel):
    decision: str
    decided_by: str = "Demo operations lead"
    expected_version: int = Field(default=1, ge=1)
    idempotency_key: str = Field(default="demo-allocation", min_length=8, max_length=128)


class KioskCheckInRequest(BaseModel):
    patient_name: str = Field(min_length=2, max_length=80)
    registration_source: str = "supervised_kiosk"
    nurse_supervisor: str = Field(min_length=2, max_length=80)
    clinical_escalation: bool = False
    idempotency_key: str = Field(default="demo-kiosk-check-in", min_length=8, max_length=128)


class PreArrivalSubmissionRequest(BaseModel):
    appointment_id: str = Field(min_length=2, max_length=80)
    coverage_action: CoverageAction
    file_name: str | None = Field(default=None, max_length=255)
    expected_ticket_version: int = Field(default=1, ge=1)
    idempotency_key: str = Field(default="demo-prearrival", min_length=8, max_length=128)


class PreArrivalSubmissionResult(BaseModel):
    success: bool = True
    synthetic: bool = True
    outcome: PatientSubmissionOutcome = PatientSubmissionOutcome.UNDER_REVIEW
    processing_reference: str
    message: str
    next_action: str


class RegistrationValidationRequest(BaseModel):
    appointment_reference: str = Field(min_length=2, max_length=80)
    identifier_hash: str = Field(pattern="^[0-9a-f]{64}$")
    full_name: str = Field(min_length=2, max_length=120)
    date_of_birth: date
    email: str = Field(min_length=3, max_length=255)
    idempotency_key: str = Field(default="demo-registration-validation", min_length=8, max_length=128)


class RegistrationValidationResult(BaseModel):
    id: str
    outcome: PatientSubmissionOutcome
    field_results: dict[str, str]
    patient_reason_code: str
    patient_next_action: str
    version: int = Field(ge=1)


class DocumentProcessingRequest(BaseModel):
    document_id: str = Field(min_length=2, max_length=80)
    expected_version: int = Field(ge=1)
    readiness_status: str = Field(pattern="^(pass|needs_review)$")
    match_status: str = Field(pattern="^(clean|ambiguous|no_match)$")
    all_required_documents_present: bool
    all_documents_valid: bool
    staff_confirmed: bool
    reason: str = Field(min_length=2, max_length=120)
    idempotency_key: str = Field(min_length=8, max_length=128)


class CounterAssignmentRequest(BaseModel):
    counter_number: str = Field(min_length=2, max_length=40)
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=128)


class PatientRecord(BaseModel):
    id: int
    source_record_key: str
    identifier_masked: str
    full_name: str
    date_of_birth: date | None = None
    email: str | None = None
    contact_mobile: str | None = None
    version: int = Field(ge=1)
    deleted_at: datetime | None = None


class PatientList(BaseModel):
    records: list[PatientRecord]
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)


class PatientCreateRequest(BaseModel):
    source_record_key: str = Field(min_length=2, max_length=120)
    identifier_hash: str = Field(pattern="^[0-9a-f]{64}$")
    identifier_masked: str = Field(min_length=4, max_length=32)
    full_name: str = Field(min_length=2, max_length=120)
    date_of_birth: date | None = None
    email: str | None = Field(default=None, max_length=255)
    contact_mobile: str | None = Field(default=None, max_length=40)
    reason: str = Field(min_length=3, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=128)


class PatientUpdateRequest(BaseModel):
    expected_version: int = Field(ge=1)
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    contact_mobile: str | None = Field(default=None, max_length=40)
    reason: str = Field(min_length=3, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=128)


class PatientDeleteRequest(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=128)


class AuditRecord(BaseModel):
    id: int
    actor_reference: str
    action_type: str
    target_table: str
    target_id: str
    details: dict[str, object]
    occurred_at: datetime


class ActionResult(BaseModel):
    success: bool
    message: str
    ticket: QueueTicket | None = None
    recommendation: AllocationRecommendation | None = None
