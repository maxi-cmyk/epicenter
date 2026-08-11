from datetime import datetime
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


class TicketTransitionRequest(BaseModel):
    readiness_state: ReadinessState
    reason: str
    staff_confirmed: bool = False


class RecommendationDecisionRequest(BaseModel):
    decision: str
    decided_by: str = "Demo operations lead"


class KioskCheckInRequest(BaseModel):
    patient_name: str = Field(min_length=2, max_length=80)
    registration_source: str = "supervised_kiosk"
    nurse_supervisor: str = Field(min_length=2, max_length=80)
    clinical_escalation: bool = False


class ActionResult(BaseModel):
    success: bool
    message: str
    ticket: QueueTicket | None = None
    recommendation: AllocationRecommendation | None = None
