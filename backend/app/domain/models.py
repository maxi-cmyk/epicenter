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


class DocumentCategory(StrEnum):
    """Payer paperwork (TPA, CHAS, corporate insurance, ...) splits into distinct
    kinds, each with different fields worth capturing."""

    FORM = "form"
    AUTHORISATION_LETTER = "authorisation_letter"
    BENEFIT_STRUCTURE = "benefit_structure"
    CODING_SCHEME = "coding_scheme"


class PatientSubmissionOutcome(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"


class PatientAccountSession(BaseModel):
    patient_id: int
    source_record_key: str
    synthetic: bool = True
    onboarding_completed: bool = False
    onboarding_step: str = "singpass"


class OnboardingStep(StrEnum):
    SINGPASS = "singpass"
    INSURANCE = "insurance"
    QUESTIONNAIRE = "questionnaire"
    COMPLETE = "complete"


class SingpassProfileField(BaseModel):
    field_id: str
    label: str
    value: str
    source: str = "Singpass / Myinfo (synthetic)"
    editable: bool = False


class PatientOnboardingState(BaseModel):
    synthetic: bool = True
    completed: bool = False
    current_step: OnboardingStep = OnboardingStep.SINGPASS
    appointment_id: str
    singpass_authenticated: bool = False
    singpass_fields: list[SingpassProfileField]
    insurance_completed: bool = False
    questionnaire_completed: bool = False
    next_href: str = "/onboarding"


class OnboardingAdvanceRequest(BaseModel):
    step: OnboardingStep
    singpass_authenticated: bool | None = None
    insurance_completed: bool | None = None
    questionnaire_completed: bool | None = None
    singpass_fields: list[SingpassProfileField] | None = None
    idempotency_key: str = Field(default="demo-onboarding", min_length=8, max_length=128)


class ChecklistStatus(StrEnum):
    PASS = "pass"
    PENDING = "pending"
    FAIL = "fail"
    NOT_REQUIRED = "not_required"


class PatientSummary(BaseModel):
    full_name: str
    identifier_masked: str
    date_of_birth: date | None = None
    contact_mobile: str | None = None
    address: str | None = None


class ChecklistItem(BaseModel):
    label: str
    status: ChecklistStatus
    detail: str | None = None


class RecordChecklist(BaseModel):
    patient: PatientSummary | None = None
    items: list[ChecklistItem] = []


class Document(BaseModel):
    """One piece of payer paperwork on file for a patient (see DocumentCategory for
    the distinct kinds it can be). Each carries a shared envelope (issuer, category,
    validity) plus a `facts` map for whatever fields are specific to that category
    (e.g. a benefit structure's plan tier vs. an authorisation letter's approval
    number)."""

    id: str
    category: DocumentCategory
    issuer_code: str
    issuer_name: str
    document_type: str
    reference_number: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    facts: dict[str, str] = {}
    confirmed: bool = False
    confirmed_by: str | None = None
    confirmed_at: datetime | None = None
    version: int = Field(default=1, ge=1)


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
    completed_at: datetime | None = None
    original_ordering_at: datetime
    waiting_minutes: int = Field(ge=0)
    expected_room: str | None = None
    actual_room: str | None = None
    processing_stage: str
    service_target: ServiceTarget = ServiceTarget.ON_TRACK
    staff_confirmed: bool = False
    clinical_escalation: bool = False
    version: int = Field(default=1, ge=1)
    record_checklist: RecordChecklist | None = None
    documents: list[Document] = []
    matched_package: str | None = None
    package_confirmed: bool = False
    package_confirmed_by: str | None = None
    package_confirmed_at: datetime | None = None
    billing_code: str | None = None
    uncovered_cost: float | None = None
    queue_number: str | None = None
    billing_confirmed: bool = False
    billing_confirmed_by: str | None = None
    billing_confirmed_at: datetime | None = None
    identity_confirmed: bool = False
    identity_confirmed_by: str | None = None
    identity_confirmed_at: datetime | None = None
    ecard_verified: bool = False
    ecard_not_applicable: bool = False
    ecard_na_reason: str | None = None
    is_checkup: bool = False
    forms_confirmed: bool = False
    forms_confirmed_by: str | None = None
    forms_confirmed_at: datetime | None = None
    physical_forms_received: bool = False
    physical_forms_received_by: str | None = None
    physical_forms_received_at: datetime | None = None


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
    visit_phase: VisitPhase | None = None
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
    is_checkup: bool = False
    idempotency_key: str = Field(default="demo-kiosk-check-in", min_length=8, max_length=128)


class PreArrivalSubmissionRequest(BaseModel):
    appointment_id: str = Field(min_length=2, max_length=80)
    coverage_action: CoverageAction
    file_name: str | None = Field(default=None, max_length=255)
    expected_ticket_version: int = Field(default=1, ge=1)
    idempotency_key: str = Field(default="demo-prearrival", min_length=8, max_length=128)


class OnboardingCoverageRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    idempotency_key: str = Field(default="demo-onboarding-coverage", min_length=8, max_length=128)


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


class DocumentConfirmRequest(BaseModel):
    facts: dict[str, str] | None = None
    reference_number: str | None = Field(default=None, max_length=80)
    valid_from: date | None = None
    valid_to: date | None = None
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=128)


class PackageConfirmRequest(BaseModel):
    corrected_package: str | None = Field(default=None, max_length=160)
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=128)


class BillingConfirmRequest(BaseModel):
    corrected_billing_code: str | None = Field(default=None, max_length=80)
    corrected_uncovered_cost: float | None = Field(default=None, ge=0)
    corrected_queue_number: str | None = Field(default=None, max_length=40)
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=128)


class IdentityConfirmRequest(BaseModel):
    ecard_not_applicable: bool = False
    ecard_na_reason: str | None = Field(default=None, max_length=200)
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=128)


class FormsConfirmRequest(BaseModel):
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=128)


class PhysicalFormsReceivedRequest(BaseModel):
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
    actor_role: str | None = None
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


class PatientNextAction(StrEnum):
    CONFIRM_COVERAGE = "confirm_coverage"
    UPLOAD_COVERAGE = "upload_coverage"
    COMPLETE_QUESTIONNAIRE = "complete_questionnaire"
    WAIT_FOR_REVIEW = "wait_for_review"
    VIEW_QUEUE = "view_queue"
    PAY = "pay"
    NONE = "none"


class PatientCoverageStatus(StrEnum):
    NOT_STARTED = "not_started"
    CHECK_FIRST = "check_first"
    SUBMITTED = "submitted"
    ACTION_REQUIRED = "action_required"


class PatientQuestionnaireStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    NOT_STARTED = "not_started"
    DRAFT = "draft"
    SUBMITTED = "submitted"


class PatientPaymentStatus(StrEnum):
    NOT_READY = "not_ready"
    READY = "ready"
    MOCK_PROCESSING = "mock_processing"
    MOCKED_PAID = "mocked_paid"
    MOCK_FAILED = "mock_failed"


class PatientNotificationBanner(BaseModel):
    category: str
    message: str
    next_action: str


class PatientAppointmentSummary(BaseModel):
    appointment_id: str
    scheduled_at: datetime
    clinic_name: str
    location: str
    appointment_type: str
    questionnaire_type: str


class PatientHome(BaseModel):
    synthetic: bool = True
    patient_display_name: str
    appointment: PatientAppointmentSummary | None = None
    coverage_status: PatientCoverageStatus
    coverage_summary: str
    questionnaire_status: PatientQuestionnaireStatus
    queue_summary: str
    payment_status: PatientPaymentStatus
    payment_summary: str
    primary_action: PatientNextAction
    primary_action_label: str
    primary_action_href: str
    outcome: PatientSubmissionOutcome | None = None
    outcome_message: str | None = None
    notification: PatientNotificationBanner | None = None
    recent_visit_summary: str | None = None


class PriorCoverageSummary(BaseModel):
    synthetic: bool = True
    appointment_id: str
    has_prior_coverage: bool
    issuer_name: str | None = None
    document_date: date | None = None
    prompt: str
    force_upload: bool = False
    notification: PatientNotificationBanner | None = None


class PatientQueueStatus(BaseModel):
    synthetic: bool = True
    available: bool
    ticket_id: str | None = None
    visit_phase: VisitPhase | None = None
    status_label: str
    status_detail: str
    counter_label: str | None = None
    patients_ahead: int | None = None
    updated_at: datetime
    stale: bool = False
    payment_ready: bool = False


class PatientPaymentSummary(BaseModel):
    synthetic: bool = True
    mocked: bool = True
    appointment_id: str | None = None
    package_label: str
    amount_covered: str
    amount_patient_payable: str
    status: PatientPaymentStatus
    status_detail: str
    receipt_reference: str | None = None
    paid_at: datetime | None = None
    failure_reason: str | None = None
    version: int = Field(default=1, ge=1)


class MockPaymentRequest(BaseModel):
    appointment_id: str = Field(min_length=2, max_length=80)
    expected_version: int = Field(default=1, ge=1)
    idempotency_key: str = Field(default="demo-mock-payment", min_length=8, max_length=128)


class PatientVisitRecord(BaseModel):
    appointment_id: str
    visited_on: date
    visit_label: str
    package_label: str | None = None
    coverage_label: str | None = None
    questionnaire_summary: str | None = None
    outcome: PatientSubmissionOutcome | None = None


class PatientVisitHistory(BaseModel):
    synthetic: bool = True
    visits: list[PatientVisitRecord]


class QuestionnairePrefillField(BaseModel):
    field_id: str
    label: str
    value: str
    source: str
    editable: bool = False


class QuestionnaireInputField(BaseModel):
    field_id: str
    label: str
    field_type: str
    required: bool = True
    help_text: str | None = None
    options: list[str] = Field(default_factory=list)
    value: str | None = None
    section: str | None = None
    show_if_field: str | None = None
    show_if_value: str | None = None
    show_if_mode: str = Field(default="equals", pattern="^(equals|contains|any_of|not_empty)$")
    show_if_field_2: str | None = None
    show_if_value_2: str | None = None
    show_if_mode_2: str = Field(default="equals", pattern="^(equals|contains|any_of|not_empty)$")


class PatientQuestionnaire(BaseModel):
    synthetic: bool = True
    appointment_id: str
    questionnaire_type: str
    title: str
    status: PatientQuestionnaireStatus
    prefill: list[QuestionnairePrefillField]
    fields: list[QuestionnaireInputField]
    declaration_acknowledged: bool = False
    version: int = Field(default=1, ge=1)


class QuestionnaireSaveRequest(BaseModel):
    appointment_id: str = Field(min_length=2, max_length=80)
    answers: dict[str, str | None] = Field(default_factory=dict)
    declaration_acknowledged: bool = False
    submit: bool = False
    expected_version: int = Field(default=1, ge=1)
    idempotency_key: str = Field(default="demo-questionnaire", min_length=8, max_length=128)


class UploadLinkSession(BaseModel):
    synthetic: bool = True
    valid: bool
    appointment_id: str | None = None
    scheduled_at: datetime | None = None
    message: str
    next_action: str
