from __future__ import annotations

from datetime import UTC, date, datetime
from statistics import median
from typing import Any, Protocol

from app.data.supabase_client import SupabaseDataApi, SupabaseDataError
from app.domain.models import (
    ActivityEvent,
    AllocationRecommendation,
    AuditRecord,
    BillingConfirmRequest,
    ChecklistItem,
    ChecklistStatus,
    DashboardSnapshot,
    Document,
    DocumentCategory,
    DocumentConfirmRequest,
    DocumentProcessingRequest,
    FormsConfirmRequest,
    IdentityConfirmRequest,
    KioskCheckInRequest,
    MedicationDispense,
    MedicationDispenseRequest,
    Metric,
    PackageConfirmRequest,
    MockPaymentRequest,
    OnboardingAdvanceRequest,
    OnboardingStep,
    PatientAppointmentSummary,
    PatientCoverageStatus,
    PatientCreateRequest,
    PatientDeleteRequest,
    PatientHome,
    PatientList,
    PatientNextAction,
    PatientNotificationBanner,
    PatientOnboardingState,
    PatientPaymentStatus,
    PatientPaymentSummary,
    PatientQuestionnaire,
    PatientQuestionnaireStatus,
    PatientQueueStatus,
    PatientRecord,
    PatientSubmissionOutcome,
    PatientSummary,
    PatientUpdateRequest,
    PhysicalFormsReceivedRequest,
    PatientVisitHistory,
    PatientVisitRecord,
    PreArrivalSubmissionRequest,
    PreArrivalSubmissionResult,
    PriorCoverageSummary,
    QueueTicket,
    QuestionnaireSaveRequest,
    RecommendationDecisionRequest,
    RecordChecklist,
    RegistrationValidationRequest,
    RegistrationValidationResult,
    ReviewCase,
    SimulatorSnapshot,
    SingpassProfileField,
    TicketTransitionRequest,
    TpaSubmission,
    TpaSubmissionConfirmRequest,
    UploadLinkSession,
    VisitPhase,
)
from app.services.questionnaire_catalog import (
    build_general_health_fields,
    build_general_health_prefill,
    missing_required_fields,
    singpass_dummy_fields,
    singpass_field_templates,
    singpass_sex_value,
)


class OperationsRepository(Protocol):
    def snapshot(self) -> DashboardSnapshot: ...

    def find_ticket(self, ticket_id: str) -> QueueTicket | None: ...

    def list_simulator_snapshots(self) -> list[SimulatorSnapshot]: ...

    def validate_registration(
        self, request: RegistrationValidationRequest, actor: str, patient_id: int | None = None
    ) -> RegistrationValidationResult: ...

    def submit_prearrival(
        self, request: PreArrivalSubmissionRequest, actor: str, patient_id: int | None = None
    ) -> PreArrivalSubmissionResult: ...

    def submit_onboarding_coverage(
        self,
        *,
        file_name: str,
        actor: str,
        patient_id: int | None,
        idempotency_key: str,
    ) -> PreArrivalSubmissionResult: ...

    def get_onboarding_state(self, subject: str, patient_id: int | None = None) -> PatientOnboardingState: ...

    def advance_onboarding(
        self, request: OnboardingAdvanceRequest, subject: str, patient_id: int | None = None
    ) -> PatientOnboardingState: ...

    def get_patient_home(self, patient_id: int | None = None) -> PatientHome: ...

    def get_prior_coverage(
        self, appointment_id: str, patient_id: int | None = None, *, first_visit: bool = False
    ) -> PriorCoverageSummary: ...

    def get_patient_queue(self, patient_id: int | None = None) -> PatientQueueStatus: ...

    def get_patient_payment(self, patient_id: int | None = None) -> PatientPaymentSummary: ...

    def submit_mock_payment(
        self, request: MockPaymentRequest, actor: str, patient_id: int | None = None
    ) -> PatientPaymentSummary: ...

    def get_patient_records(self, patient_id: int | None = None) -> PatientVisitHistory: ...

    def get_patient_questionnaire(
        self, appointment_id: str, patient_id: int | None = None
    ) -> PatientQuestionnaire: ...

    def save_patient_questionnaire(
        self, request: QuestionnaireSaveRequest, actor: str, patient_id: int | None = None
    ) -> PatientQuestionnaire: ...

    def resolve_upload_link(self, token: str) -> UploadLinkSession: ...

    def transition_ticket(self, ticket_id: str, request: TicketTransitionRequest, actor: str) -> QueueTicket: ...

    def add_walk_in(self, request: KioskCheckInRequest, actor: str) -> QueueTicket: ...

    def process_document(self, ticket_id: str, request: DocumentProcessingRequest, actor: str) -> QueueTicket: ...

    def decide_recommendation(
        self,
        recommendation_id: str,
        request: RecommendationDecisionRequest,
        actor: str,
    ) -> AllocationRecommendation: ...

    def list_patients(
        self, *, search: str | None, offset: int, limit: int, contact_filter: str = "all", sort: str = "name"
    ) -> PatientList: ...

    def get_patient(self, patient_id: int) -> PatientRecord | None: ...

    def create_patient(self, request: PatientCreateRequest, actor: str) -> PatientRecord: ...

    def update_patient(self, patient_id: int, request: PatientUpdateRequest, actor: str) -> PatientRecord: ...

    def delete_patient(self, patient_id: int, request: PatientDeleteRequest, actor: str) -> PatientRecord: ...

    def list_audit(
        self,
        *,
        limit: int,
        offset: int = 0,
        search: str | None = None,
        actor: str | None = None,
        actor_role: str | None = None,
        outcome: str | None = None,
        action_type: str | None = None,
        target_table: str | None = None,
        occurred_from: datetime | None = None,
        occurred_to: datetime | None = None,
    ) -> list[AuditRecord]: ...

    def record_medication_dispense(
        self, ticket_id: str, request: MedicationDispenseRequest, actor: str
    ) -> MedicationDispense: ...

    def draft_tpa_submission(self, ticket_id: str) -> TpaSubmission: ...

    def confirm_tpa_submission(
        self, ticket_id: str, request: TpaSubmissionConfirmRequest, actor: str
    ) -> TpaSubmission: ...

    def confirm_document(
        self, ticket_id: str, document_id: str, request: DocumentConfirmRequest, actor: str
    ) -> QueueTicket: ...

    def confirm_package(self, ticket_id: str, request: PackageConfirmRequest, actor: str) -> QueueTicket: ...

    def confirm_billing(self, ticket_id: str, request: BillingConfirmRequest, actor: str) -> QueueTicket: ...

    def confirm_identity(self, ticket_id: str, request: IdentityConfirmRequest, actor: str) -> QueueTicket: ...

    def confirm_forms(self, ticket_id: str, request: FormsConfirmRequest, actor: str) -> QueueTicket: ...

    def mark_physical_forms_received(
        self, ticket_id: str, request: PhysicalFormsReceivedRequest, actor: str
    ) -> QueueTicket: ...


def _ticket_from_row(row: dict[str, object]) -> QueueTicket:
    return QueueTicket(
        id=str(row["id"]),
        patient_id=str(row["patient_reference"]),
        patient_name=str(row["patient_name_snapshot"]),
        intake_type=str(row["intake_type"]),
        visit_phase=str(row["visit_status"]),
        readiness_state=str(row["readiness_state"]),
        readiness_reason=str(row["readiness_reason"]),
        scheduled_at=row.get("scheduled_at"),
        checked_in_at=row.get("checked_in_at"),
        completed_at=row.get("completed_at"),
        original_ordering_at=row["original_ordering_at"],
        waiting_minutes=int(row.get("waiting_minutes") or 0),
        expected_room=row.get("expected_counter_number"),
        actual_room=row.get("counter_number"),
        processing_stage=str(row["processing_stage"]),
        service_target=str(row.get("service_target") or "on_track"),
        staff_confirmed=bool(row.get("staff_confirmed")),
        clinical_escalation=bool(row.get("clinical_escalation")),
        version=int(row.get("version") or 1),
        matched_package=row.get("matched_package"),
        package_confirmed=bool(row.get("package_confirmed")),
        package_confirmed_by=row.get("package_confirmed_by"),
        package_confirmed_at=row.get("package_confirmed_at"),
        billing_code=row.get("billing_code"),
        uncovered_cost=float(row["uncovered_cost"]) if row.get("uncovered_cost") is not None else None,
        queue_number=row.get("queue_number"),
        billing_confirmed=bool(row.get("billing_confirmed")),
        billing_confirmed_by=row.get("billing_confirmed_by"),
        billing_confirmed_at=row.get("billing_confirmed_at"),
        identity_confirmed=bool(row.get("identity_confirmed")),
        identity_confirmed_by=row.get("identity_confirmed_by"),
        identity_confirmed_at=row.get("identity_confirmed_at"),
        ecard_verified=bool(row.get("ecard_verified")),
        ecard_not_applicable=bool(row.get("ecard_not_applicable")),
        ecard_na_reason=row.get("ecard_na_reason"),
        is_checkup=bool(row.get("is_checkup")),
        forms_confirmed=bool(row.get("forms_confirmed")),
        forms_confirmed_by=row.get("forms_confirmed_by"),
        forms_confirmed_at=row.get("forms_confirmed_at"),
        physical_forms_received=bool(row.get("physical_forms_received")),
        physical_forms_received_by=row.get("physical_forms_received_by"),
        physical_forms_received_at=row.get("physical_forms_received_at"),
    )


def _document_from_row(row: dict[str, object]) -> Document:
    raw_facts = row.get("extracted_facts") or {}
    assert isinstance(raw_facts, dict)
    return Document(
        id=str(row["id"]),
        category=DocumentCategory(str(row.get("document_category") or "benefit_structure")),
        issuer_code=str(row.get("issuer_code") or "UNKNOWN"),
        issuer_name=str(row.get("issuer_name") or "Unknown issuer"),
        document_type=str(row["document_type"]),
        reference_number=row.get("reference_number"),
        valid_from=row.get("validity_start"),
        valid_to=row.get("validity_end"),
        facts={str(key): str(value) for key, value in raw_facts.items()},
        confirmed=str(row.get("review_status")) == "confirmed",
        confirmed_by=row.get("confirmed_by_reference"),
        confirmed_at=row.get("confirmed_at"),
        version=int(row.get("version") or 1),
    )


def _checklist_status_from_bool(ok: bool) -> ChecklistStatus:
    return ChecklistStatus.PASS if ok else ChecklistStatus.FAIL


def _questionnaire_item(label: str, status_by_type: dict[str, str], questionnaire_type: str) -> ChecklistItem:
    verification_status = status_by_type.get(questionnaire_type)
    if verification_status is None:
        return ChecklistItem(label=label, status=ChecklistStatus.NOT_REQUIRED)
    if verification_status == "verified":
        return ChecklistItem(label=label, status=ChecklistStatus.PASS, detail="Verified")
    return ChecklistItem(label=label, status=ChecklistStatus.PENDING, detail=verification_status.replace("_", " "))


def _build_checklist(
    row: dict[str, object],
    *,
    patients_by_id: dict[int, dict[str, object]],
    coverage_by_appointment: dict[str, dict[str, object]],
    eligibility_by_appointment: dict[str, dict[str, object]],
    rules_by_id: dict[str, dict[str, object]],
    questionnaires_by_patient: dict[int, dict[str, str]],
) -> RecordChecklist:
    patient_id = row.get("patient_id")
    appointment_id = row.get("appointment_id")

    patient_row = patients_by_id.get(int(patient_id)) if patient_id is not None else None  # type: ignore[arg-type]
    patient = (
        PatientSummary(
            full_name=str(patient_row["full_name"]),
            identifier_masked=str(patient_row["identifier_masked"]),
            date_of_birth=patient_row.get("date_of_birth"),
            contact_mobile=patient_row.get("contact_mobile"),
            address=patient_row.get("address"),
        )
        if patient_row
        else None
    )

    coverage_row = coverage_by_appointment.get(str(appointment_id)) if appointment_id else None
    documents_present = bool(row.get("all_required_documents_present"))
    documents_valid = bool(row.get("all_documents_valid"))
    extraction_pass = str(row.get("extraction_status") or "needs_review") == "pass"
    coverage_detail = (
        f"{coverage_row.get('issuer_name')} · {coverage_row.get('document_type')}"
        if coverage_row and coverage_row.get("issuer_name")
        else None
    )

    eligibility_row = eligibility_by_appointment.get(str(appointment_id)) if appointment_id else None
    match_status = str(row.get("match_status") or "no_match")
    eligibility_status = (
        ChecklistStatus.PASS
        if match_status == "clean"
        else ChecklistStatus.PENDING
        if match_status == "ambiguous"
        else ChecklistStatus.FAIL
    )
    matched_rule = rules_by_id.get(str(eligibility_row.get("matched_rule_id"))) if eligibility_row else None
    eligibility_detail = str(matched_rule["package_name"]) if matched_rule else None

    status_by_type = questionnaires_by_patient.get(int(patient_id), {}) if patient_id is not None else {}  # type: ignore[arg-type]

    return RecordChecklist(
        patient=patient,
        items=[
            ChecklistItem(
                label="Patient details",
                status=ChecklistStatus.PASS if patient else ChecklistStatus.PENDING,
                detail=patient.identifier_masked if patient else None,
            ),
            ChecklistItem(
                label="Coverage document",
                status=_checklist_status_from_bool(documents_present and documents_valid and extraction_pass),
                detail=coverage_detail,
            ),
            ChecklistItem(label="Eligibility match", status=eligibility_status, detail=eligibility_detail),
            _questionnaire_item("General health questionnaire", status_by_type, "general_health"),
            _questionnaire_item("Occupational health questionnaire", status_by_type, "occupational_health"),
        ],
    )


def _recommendation_from_row(row: dict[str, object]) -> AllocationRecommendation:
    demand = row.get("demand_snapshot") or {}
    effect = row.get("expected_effect") or {}
    assert isinstance(demand, dict) and isinstance(effect, dict)
    constraints = row.get("constraints_checked") or []
    assert isinstance(constraints, list)
    return AllocationRecommendation(
        id=str(row["id"]),
        status=str(row["status"]),
        pressured_workstream=str(row["pressured_workstream"]),
        rationale=str(row["rationale"]),
        qualified_resource=str(row["qualified_resource"]),
        current_wait_minutes=int(demand.get("current_wait_minutes", 0)),
        expected_wait_minutes=int(effect.get("expected_wait_minutes", 0)),
        expires_at=row["expires_at"],
        constraints_checked=[str(item) for item in constraints],
        version=int(row.get("version") or 1),
    )


def _patient_from_row(row: dict[str, object]) -> PatientRecord:
    return PatientRecord(
        id=int(row["id"]),
        source_record_key=str(row["source_record_key"]),
        identifier_masked=str(row["identifier_masked"]),
        full_name=str(row["full_name"]),
        date_of_birth=row.get("date_of_birth"),
        email=row.get("email"),
        contact_mobile=row.get("contact_mobile"),
        version=int(row.get("version") or 1),
        deleted_at=row.get("deleted_at"),
    )


def _parse_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _parse_date(value: object) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value)[:10])


def _patient_home_from_row(row: dict[str, Any]) -> PatientHome:
    appointment_raw = row.get("appointment")
    appointment = None
    if isinstance(appointment_raw, dict):
        scheduled = _parse_datetime(appointment_raw.get("scheduled_at"))
        if scheduled is not None:
            appointment = PatientAppointmentSummary(
                appointment_id=str(appointment_raw.get("appointment_id") or ""),
                scheduled_at=scheduled,
                clinic_name=str(appointment_raw.get("clinic_name") or ""),
                location=str(appointment_raw.get("location") or ""),
                appointment_type=str(appointment_raw.get("appointment_type") or ""),
                questionnaire_type=str(appointment_raw.get("questionnaire_type") or "general_health"),
            )
    notification_raw = row.get("notification")
    notification = None
    if isinstance(notification_raw, dict):
        notification = PatientNotificationBanner(
            category=str(notification_raw.get("category") or ""),
            message=str(notification_raw.get("message") or ""),
            next_action=str(notification_raw.get("next_action") or ""),
        )
    outcome_raw = row.get("outcome")
    return PatientHome(
        synthetic=bool(row.get("synthetic", True)),
        patient_display_name=str(row.get("patient_display_name") or ""),
        appointment=appointment,
        coverage_status=PatientCoverageStatus(str(row.get("coverage_status") or "not_started")),
        coverage_summary=str(row.get("coverage_summary") or ""),
        questionnaire_status=PatientQuestionnaireStatus(str(row.get("questionnaire_status") or "not_started")),
        queue_summary=str(row.get("queue_summary") or ""),
        payment_status=PatientPaymentStatus(str(row.get("payment_status") or "not_ready")),
        payment_summary=str(row.get("payment_summary") or ""),
        primary_action=PatientNextAction(str(row.get("primary_action") or "none")),
        primary_action_label=str(row.get("primary_action_label") or ""),
        primary_action_href=str(row.get("primary_action_href") or "/"),
        outcome=PatientSubmissionOutcome(str(outcome_raw)) if outcome_raw else None,
        outcome_message=str(row["outcome_message"]) if row.get("outcome_message") else None,
        notification=notification,
        recent_visit_summary=str(row["recent_visit_summary"]) if row.get("recent_visit_summary") else None,
    )


def _patient_queue_from_row(row: dict[str, Any]) -> PatientQueueStatus:
    phase_raw = row.get("visit_phase")
    updated = _parse_datetime(row.get("updated_at")) or datetime.now(UTC)
    patients_ahead = row.get("patients_ahead")
    return PatientQueueStatus(
        synthetic=bool(row.get("synthetic", True)),
        available=bool(row.get("available")),
        ticket_id=str(row["ticket_id"]) if row.get("ticket_id") else None,
        visit_phase=VisitPhase(str(phase_raw)) if phase_raw else None,
        status_label=str(row.get("status_label") or ""),
        status_detail=str(row.get("status_detail") or ""),
        queue_number=str(row["queue_number"]) if row.get("queue_number") else None,
        counter_label=str(row["counter_label"]) if row.get("counter_label") else None,
        patients_ahead=int(patients_ahead) if patients_ahead is not None else None,
        updated_at=updated,
        stale=bool(row.get("stale", False)),
        payment_ready=bool(row.get("payment_ready", False)),
    )


def _patient_payment_from_row(row: dict[str, Any]) -> PatientPaymentSummary:
    return PatientPaymentSummary(
        synthetic=bool(row.get("synthetic", True)),
        mocked=bool(row.get("mocked", True)),
        appointment_id=str(row["appointment_id"]) if row.get("appointment_id") else None,
        package_label=str(row.get("package_label") or ""),
        amount_covered=str(row.get("amount_covered") or ""),
        amount_patient_payable=str(row.get("amount_patient_payable") or ""),
        status=PatientPaymentStatus(str(row.get("status") or "not_ready")),
        status_detail=str(row.get("status_detail") or ""),
        receipt_reference=str(row["receipt_reference"]) if row.get("receipt_reference") else None,
        paid_at=_parse_datetime(row.get("paid_at")),
        failure_reason=str(row["failure_reason"]) if row.get("failure_reason") else None,
        version=int(row.get("version") or 1),
    )


def _patient_records_from_row(row: dict[str, Any]) -> PatientVisitHistory:
    visits_raw = row.get("visits")
    visits: list[PatientVisitRecord] = []
    if isinstance(visits_raw, list):
        for item in visits_raw:
            if not isinstance(item, dict):
                continue
            outcome_raw = item.get("outcome")
            visits.append(
                PatientVisitRecord(
                    appointment_id=str(item.get("appointment_id") or ""),
                    visited_on=_parse_date(item.get("visited_on")),
                    visit_label=str(item.get("visit_label") or ""),
                    package_label=str(item["package_label"]) if item.get("package_label") else None,
                    coverage_label=str(item["coverage_label"]) if item.get("coverage_label") else None,
                    questionnaire_summary=(
                        str(item["questionnaire_summary"]) if item.get("questionnaire_summary") else None
                    ),
                    outcome=PatientSubmissionOutcome(str(outcome_raw)) if outcome_raw else None,
                )
            )
    return PatientVisitHistory(synthetic=bool(row.get("synthetic", True)), visits=visits)


def _onboarding_from_row(row: dict[str, object], *, allow_manual_singpass: bool = False) -> PatientOnboardingState:
    authenticated = bool(row.get("singpass_authenticated"))
    profile = row.get("singpass_profile")
    fields: list[SingpassProfileField] = []
    if isinstance(profile, list) and profile:
        for item in profile:
            if not isinstance(item, dict):
                continue
            editable = bool(item.get("editable", False))
            if allow_manual_singpass and authenticated and not row.get("completed"):
                # Keep the confirm step editable until the patient leaves Singpass.
                current_step = str(row.get("current_step") or "singpass")
                editable = editable or current_step == "singpass"
            fields.append(
                SingpassProfileField(
                    field_id=str(item.get("field_id") or ""),
                    label=str(item.get("label") or ""),
                    value=str(item.get("value") or "") if authenticated else "",
                    source=str(
                        item.get("source")
                        or (
                            "Patient-provided (Singpass adapter offline)"
                            if allow_manual_singpass
                            else "Singpass / Myinfo (synthetic)"
                        )
                    ),
                    editable=editable,
                )
            )
    if not fields:
        if allow_manual_singpass:
            fields = [
                SingpassProfileField(
                    field_id=str(item["field_id"]),
                    label=str(item["label"]),
                    value=str(item["value"]) if authenticated else "",
                    source=str(item["source"]),
                    editable=bool(item["editable"]) if authenticated else False,
                )
                for item in singpass_field_templates(editable=True)
            ]
        else:
            fields = [
                SingpassProfileField(
                    field_id=item["field_id"],
                    label=item["label"],
                    value=item["value"] if authenticated else "",
                )
                for item in singpass_dummy_fields()
            ]
    completed = bool(row.get("completed"))
    appointment_id = str(row.get("appointment_id") or "")
    return PatientOnboardingState(
        completed=completed,
        current_step=OnboardingStep(str(row.get("current_step") or "singpass")),
        appointment_id=appointment_id or "pending-booking",
        singpass_authenticated=authenticated,
        singpass_fields=fields,
        insurance_completed=bool(row.get("insurance_completed")),
        questionnaire_completed=bool(row.get("questionnaire_completed")),
        next_href="/" if completed else "/onboarding",
    )


def _answers_from_payload(raw: object) -> dict[str, str | None]:
    if not isinstance(raw, dict):
        return {}
    answers: dict[str, str | None] = {}
    for key, value in raw.items():
        if value is None:
            answers[str(key)] = None
        else:
            answers[str(key)] = str(value)
    return answers


def _questionnaire_from_row(
    row: dict[str, object],
    *,
    singpass_profile: list[dict[str, object]] | None = None,
    use_synthetic_singpass: bool = True,
) -> PatientQuestionnaire:
    answers = _answers_from_payload(row.get("answers"))
    if singpass_profile is not None:
        profile: list[dict[str, object]] | None = singpass_profile
    elif use_synthetic_singpass:
        profile = [dict(item) for item in singpass_dummy_fields()]
    else:
        profile = []
    if "gender" not in answers or not answers.get("gender"):
        sex = singpass_sex_value(profile)
        if sex:
            answers = {**answers, "gender": sex}
    status_raw = str(row.get("status") or "draft")
    status = (
        PatientQuestionnaireStatus.SUBMITTED
        if status_raw == "submitted"
        else PatientQuestionnaireStatus.DRAFT
        if status_raw == "draft"
        else PatientQuestionnaireStatus.NOT_STARTED
    )
    return PatientQuestionnaire(
        appointment_id=str(row["appointment_id"]),
        questionnaire_type="general_health",
        title="General Health Screening Questionnaire",
        status=status,
        prefill=build_general_health_prefill(profile),
        fields=build_general_health_fields(answers),
        declaration_acknowledged=bool(row.get("declaration_acknowledged")),
        version=int(row.get("version") or 1),
    )


class SupabaseOperationsRepository:
    def __init__(
        self,
        api: SupabaseDataApi,
        *,
        clinic_id: str = "clinic_harbourfront",
        use_synthetic_singpass: bool = True,
    ) -> None:
        self.api = api
        self.clinic_id = clinic_id
        self.use_synthetic_singpass = use_synthetic_singpass

    def snapshot(self) -> DashboardSnapshot:
        generated_at = datetime.now(UTC)
        clinic_rows = self.api.select("clinics", "id,name", filters={"id": f"eq.{self.clinic_id}"}, limit=1)
        ticket_rows = self.api.select(
            "queue_entries",
            "*",
            filters={"clinic_id": f"eq.{self.clinic_id}", "deleted_at": "is.null"},
            order="original_ordering_at.asc",
        )
        review_rows = self.api.select("review_cases", "*", filters={"resolved_at": "is.null"})
        recommendation_rows = self.api.select(
            "allocation_recommendations",
            "*",
            filters={"clinic_id": f"eq.{self.clinic_id}"},
            order="generated_at.desc",
            limit=1,
        )
        event_rows = self.api.select(
            "operational_events",
            "id,occurred_at,metadata,event_type",
            filters={"clinic_id": f"eq.{self.clinic_id}"},
            order="occurred_at.desc",
            limit=12,
        )
        if not clinic_rows or not recommendation_rows:
            raise RuntimeError("The Supabase operational seed has not been applied.")

        tickets = [_ticket_from_row(row) for row in ticket_rows]
        tickets_by_id = {ticket.id: ticket for ticket in tickets}

        patient_ids = {int(row["patient_id"]) for row in ticket_rows if row.get("patient_id") is not None}
        appointment_ids = {str(row["appointment_id"]) for row in ticket_rows if row.get("appointment_id") is not None}

        patient_rows = (
            self.api.select(
                "patients",
                "id,full_name,identifier_masked,date_of_birth,contact_mobile,address",
                filters={"id": f"in.({','.join(str(pid) for pid in patient_ids)})"},
            )
            if patient_ids
            else []
        )
        patients_by_id = {int(row["id"]): row for row in patient_rows}

        coverage_rows = (
            self.api.select(
                "coverage_documents",
                (
                    "id,appointment_id,issuer_code,issuer_name,document_type,document_category,"
                    "reference_number,validity_start,validity_end,extracted_facts,review_status,"
                    "confirmed_by_reference,confirmed_at,version,updated_at"
                ),
                filters={"appointment_id": f"in.({','.join(appointment_ids)})", "deleted_at": "is.null"},
                order="updated_at.desc",
            )
            if appointment_ids
            else []
        )
        coverage_by_appointment: dict[str, dict[str, object]] = {}
        documents_by_appointment: dict[str, list[Document]] = {}
        for row in coverage_rows:
            coverage_by_appointment.setdefault(str(row["appointment_id"]), row)
            documents_by_appointment.setdefault(str(row["appointment_id"]), []).append(_document_from_row(row))

        eligibility_rows = (
            self.api.select(
                "eligibility_matches",
                "appointment_id,matched_rule_id,match_status,updated_at",
                filters={"appointment_id": f"in.({','.join(appointment_ids)})", "deleted_at": "is.null"},
                order="updated_at.desc",
            )
            if appointment_ids
            else []
        )
        eligibility_by_appointment: dict[str, dict[str, object]] = {}
        for row in eligibility_rows:
            eligibility_by_appointment.setdefault(str(row["appointment_id"]), row)

        rule_ids = {str(row["matched_rule_id"]) for row in eligibility_rows if row.get("matched_rule_id")}
        rule_rows = (
            self.api.select("eligibility_rules", "id,package_name", filters={"id": f"in.({','.join(rule_ids)})"})
            if rule_ids
            else []
        )
        rules_by_id = {str(row["id"]): row for row in rule_rows}

        questionnaire_rows = (
            self.api.select(
                "questionnaire_submissions",
                "patient_id,questionnaire_type,verification_status",
                filters={"patient_id": f"in.({','.join(str(pid) for pid in patient_ids)})"},
            )
            if patient_ids
            else []
        )
        questionnaires_by_patient: dict[int, dict[str, str]] = {}
        for row in questionnaire_rows:
            if row.get("patient_id") is None:
                continue
            bucket = questionnaires_by_patient.setdefault(int(row["patient_id"]), {})
            bucket[str(row["questionnaire_type"])] = str(row["verification_status"])

        for row, ticket in zip(ticket_rows, tickets, strict=True):
            ticket.record_checklist = _build_checklist(
                row,
                patients_by_id=patients_by_id,
                coverage_by_appointment=coverage_by_appointment,
                eligibility_by_appointment=eligibility_by_appointment,
                rules_by_id=rules_by_id,
                questionnaires_by_patient=questionnaires_by_patient,
            )
            appointment_id = row.get("appointment_id")
            ticket.documents = documents_by_appointment.get(str(appointment_id), []) if appointment_id else []
            eligibility_row = eligibility_by_appointment.get(str(appointment_id)) if appointment_id else None
            matched_rule = rules_by_id.get(str(eligibility_row.get("matched_rule_id"))) if eligibility_row else None
            if ticket.matched_package is None:
                ticket.matched_package = str(matched_rule["package_name"]) if matched_rule else None

        review_cases = []
        for row in review_rows:
            ticket = tickets_by_id.get(str(row["queue_entry_id"]))
            if ticket is None:
                continue
            review_cases.append(
                ReviewCase(
                    id=str(row["id"]),
                    ticket_id=ticket.id,
                    patient_name=ticket.patient_name,
                    reason_code=str(row["reason_code"]),
                    reason_label=str(row["reason_label"]),
                    document_name=row.get("document_name"),
                    evidence_summary=str(row["evidence_summary"]),
                    waiting_minutes=ticket.waiting_minutes,
                    service_target=ticket.service_target,
                    next_action=str(row["next_action"]),
                )
            )

        active_waits = [ticket.waiting_minutes for ticket in tickets if ticket.visit_phase == "ongoing"]
        booked = [ticket for ticket in tickets if ticket.intake_type == "booked" and ticket.visit_phase == "incoming"]
        booked_ready = sum(ticket.readiness_state == "ready" for ticket in booked)
        metrics = [
            Metric(
                label="Ready before arrival",
                value=f"{round((booked_ready / len(booked)) * 100) if booked else 0}%",
                detail=f"{booked_ready} of {len(booked)} booked patients",
                trend="Synthetic operational snapshot",
            ),
            Metric(
                label="Oldest review",
                value=f"{max((case.waiting_minutes for case in review_cases), default=0)} min",
                detail=review_cases[0].ticket_id if review_cases else "No active review",
                trend="Actionable worklist",
            ),
            Metric(
                label="Median admin wait",
                value=f"{round(median(active_waits)) if active_waits else 0} min",
                detail=f"{len(active_waits)} active visits",
                trend="Database-backed",
            ),
            Metric(
                label="Staff confirmations",
                value=str(sum(ticket.staff_confirmed for ticket in tickets)),
                detail="Current seeded visits",
                trend="Human-confirmed only",
            ),
        ]
        activity = []
        for row in event_rows:
            metadata = row.get("metadata") or {}
            assert isinstance(metadata, dict)
            activity.append(
                ActivityEvent(
                    id=f"E-{row['id']}",
                    occurred_at=row["occurred_at"],
                    label=str(metadata.get("label") or str(row["event_type"]).replace("_", " ").title()),
                    detail=str(metadata.get("detail") or "Stored operational event."),
                    tone=str(metadata.get("tone") or "neutral"),
                )
            )

        return DashboardSnapshot(
            generated_at=generated_at,
            clinic_name=str(clinic_rows[0]["name"]),
            tickets=tickets,
            review_cases=review_cases,
            recommendation=_recommendation_from_row(recommendation_rows[0]),
            metrics=metrics,
            activity=activity,
        )

    def find_ticket(self, ticket_id: str) -> QueueTicket | None:
        rows = self.api.select(
            "queue_entries",
            "*",
            filters={"id": f"eq.{ticket_id}", "deleted_at": "is.null"},
            limit=1,
        )
        return _ticket_from_row(rows[0]) if rows else None

    def list_simulator_snapshots(self) -> list[SimulatorSnapshot]:
        rows = self.api.select(
            "simulator_snapshots",
            "id,scenario_id,scenario_version,seed,assumptions_version,snapshot_hash,snapshot_payload,is_synthetic",
            filters={"clinic_id": f"eq.{self.clinic_id}", "active": "eq.true"},
            order="scenario_id.asc",
        )
        return [
            SimulatorSnapshot(
                id=str(row["id"]),
                scenario_id=str(row["scenario_id"]),
                scenario_version=str(row["scenario_version"]),
                seed=int(row["seed"]),
                assumptions_version=str(row["assumptions_version"]),
                snapshot_hash=str(row["snapshot_hash"]),
                snapshot_payload=dict(row["snapshot_payload"]),
                synthetic=bool(row["is_synthetic"]),
            )
            for row in rows
        ]

    def validate_registration(
        self, request: RegistrationValidationRequest, actor: str, patient_id: int | None = None
    ) -> RegistrationValidationResult:
        if patient_id is not None:
            scoped = self.api.select(
                "appointments",
                "id",
                filters={
                    "appointment_reference": f"eq.{request.appointment_reference}",
                    "patient_id": f"eq.{patient_id}",
                    "deleted_at": "is.null",
                },
                limit=1,
            )
            if not scoped:
                raise SupabaseDataError("Appointment not found for this patient.", code="PT404", status_code=404)
        row = self.api.rpc(
            "epicenter_validate_registration",
            {
                "p_appointment_reference": request.appointment_reference,
                "p_identifier_hash": request.identifier_hash,
                "p_full_name": request.full_name,
                "p_date_of_birth": request.date_of_birth.isoformat(),
                "p_email": request.email,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return RegistrationValidationResult(
            id=str(row["id"]),
            outcome=str(row["outcome"]),
            field_results=dict(row["field_results"]),
            patient_reason_code=str(row["patient_reason_code"]),
            patient_next_action=str(row["patient_next_action"]),
            version=int(row["version"]),
        )

    def submit_prearrival(
        self, request: PreArrivalSubmissionRequest, actor: str, patient_id: int | None = None
    ) -> PreArrivalSubmissionResult:
        if patient_id is not None:
            scoped = self.api.select(
                "appointments",
                "id",
                filters={
                    "appointment_reference": f"eq.{request.appointment_id}",
                    "patient_id": f"eq.{patient_id}",
                    "deleted_at": "is.null",
                },
                limit=1,
            )
            if not scoped:
                raise SupabaseDataError("Appointment not found for this patient.", code="PT404", status_code=404)
        row = self.api.rpc(
            "epicenter_submit_prearrival",
            {
                "p_appointment_reference": request.appointment_id,
                "p_coverage_action": request.coverage_action.value,
                "p_file_name": request.file_name,
                "p_expected_ticket_version": request.expected_ticket_version,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return PreArrivalSubmissionResult(
            processing_reference=str(row["id"]),
            outcome=PatientSubmissionOutcome(str(row["outcome"])),
            message="The submission was stored for current administrative checks.",
            next_action=str(row["patient_next_action"]),
        )

    def transition_ticket(self, ticket_id: str, request: TicketTransitionRequest, actor: str) -> QueueTicket:
        row = self.api.rpc(
            "epicenter_transition_ticket",
            {
                "p_ticket_id": ticket_id,
                "p_expected_version": request.expected_version,
                "p_readiness_state": request.readiness_state.value,
                "p_reason": request.reason,
                "p_staff_confirmed": request.staff_confirmed,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _ticket_from_row(row)

    def add_walk_in(self, request: KioskCheckInRequest, actor: str) -> QueueTicket:
        row = self.api.rpc(
            "epicenter_create_walk_in_ticket",
            {
                "p_clinic_id": self.clinic_id,
                "p_patient_name": request.patient_name,
                "p_nurse_supervisor": request.nurse_supervisor,
                "p_clinical_escalation": request.clinical_escalation,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _ticket_from_row(row)

    def process_document(self, ticket_id: str, request: DocumentProcessingRequest, actor: str) -> QueueTicket:
        row = self.api.rpc(
            "epicenter_process_document",
            {
                "p_ticket_id": ticket_id,
                "p_document_id": request.document_id,
                "p_expected_version": request.expected_version,
                "p_readiness_status": request.readiness_status,
                "p_match_status": request.match_status,
                "p_all_required_documents_present": request.all_required_documents_present,
                "p_all_documents_valid": request.all_documents_valid,
                "p_staff_confirmed": request.staff_confirmed,
                "p_reason": request.reason,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _ticket_from_row(row)

    def record_medication_dispense(
        self, ticket_id: str, request: MedicationDispenseRequest, actor: str
    ) -> MedicationDispense:
        raise NotImplementedError(
            "Pharmacist medication dispensing is only available in the demo repository "
            "pending the deferred production migration (task #13)."
        )

    def draft_tpa_submission(self, ticket_id: str) -> TpaSubmission:
        raise NotImplementedError(
            "TPA submission drafting is only available in the demo repository "
            "pending the deferred production migration (task #13)."
        )

    def confirm_tpa_submission(self, ticket_id: str, request: TpaSubmissionConfirmRequest, actor: str) -> TpaSubmission:
        raise NotImplementedError(
            "TPA submission confirmation is only available in the demo repository "
            "pending the deferred production migration (task #13)."
        )

    def confirm_document(
        self, ticket_id: str, document_id: str, request: DocumentConfirmRequest, actor: str
    ) -> QueueTicket:
        row = self.api.rpc(
            "epicenter_confirm_document",
            {
                "p_ticket_id": ticket_id,
                "p_document_id": document_id,
                "p_expected_version": request.expected_version,
                "p_facts": request.facts,
                "p_reference_number": request.reference_number,
                "p_valid_from": request.valid_from.isoformat() if request.valid_from else None,
                "p_valid_to": request.valid_to.isoformat() if request.valid_to else None,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _ticket_from_row(row)

    def confirm_package(self, ticket_id: str, request: PackageConfirmRequest, actor: str) -> QueueTicket:
        row = self.api.rpc(
            "epicenter_confirm_package",
            {
                "p_ticket_id": ticket_id,
                "p_expected_version": request.expected_version,
                "p_corrected_package": request.corrected_package,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _ticket_from_row(row)

    def confirm_billing(self, ticket_id: str, request: BillingConfirmRequest, actor: str) -> QueueTicket:
        row = self.api.rpc(
            "epicenter_confirm_billing",
            {
                "p_ticket_id": ticket_id,
                "p_expected_version": request.expected_version,
                "p_corrected_billing_code": request.corrected_billing_code,
                "p_corrected_uncovered_cost": request.corrected_uncovered_cost,
                "p_corrected_queue_number": request.corrected_queue_number,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _ticket_from_row(row)

    def confirm_identity(self, ticket_id: str, request: IdentityConfirmRequest, actor: str) -> QueueTicket:
        row = self.api.rpc(
            "epicenter_confirm_identity",
            {
                "p_ticket_id": ticket_id,
                "p_expected_version": request.expected_version,
                "p_ecard_not_applicable": request.ecard_not_applicable,
                "p_ecard_na_reason": request.ecard_na_reason,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _ticket_from_row(row)

    def confirm_forms(self, ticket_id: str, request: FormsConfirmRequest, actor: str) -> QueueTicket:
        row = self.api.rpc(
            "epicenter_confirm_forms",
            {
                "p_ticket_id": ticket_id,
                "p_expected_version": request.expected_version,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _ticket_from_row(row)

    def mark_physical_forms_received(
        self, ticket_id: str, request: PhysicalFormsReceivedRequest, actor: str
    ) -> QueueTicket:
        row = self.api.rpc(
            "epicenter_mark_physical_forms_received",
            {
                "p_ticket_id": ticket_id,
                "p_expected_version": request.expected_version,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _ticket_from_row(row)

    def decide_recommendation(
        self,
        recommendation_id: str,
        request: RecommendationDecisionRequest,
        actor: str,
    ) -> AllocationRecommendation:
        row = self.api.rpc(
            "epicenter_decide_allocation",
            {
                "p_recommendation_id": recommendation_id,
                "p_expected_version": request.expected_version,
                "p_decision": request.decision,
                "p_decided_by": request.decided_by,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _recommendation_from_row(row)

    def list_patients(
        self, *, search: str | None, offset: int, limit: int, contact_filter: str = "all", sort: str = "name"
    ) -> PatientList:
        filters = {"deleted_at": "is.null"}
        if search:
            safe_search = search.replace("%", "").replace("*", "").strip()
            if safe_search:
                filters["full_name"] = f"ilike.*{safe_search}*"
        if contact_filter == "email":
            filters["email"] = "not.is.null"
        elif contact_filter == "mobile":
            filters["contact_mobile"] = "not.is.null"
        elif contact_filter == "complete":
            filters["email"] = "not.is.null"
            filters["contact_mobile"] = "not.is.null"
        order = {
            "reference": "source_record_key.asc",
            "dob": "date_of_birth.desc.nullslast",
        }.get(sort, "full_name.asc")
        rows = self.api.select(
            "patients",
            "id,source_record_key,identifier_masked,full_name,date_of_birth,email,contact_mobile,version,deleted_at",
            filters=filters,
            order=order,
            limit=limit,
            offset=offset,
        )
        return PatientList(records=[_patient_from_row(row) for row in rows], offset=offset, limit=limit)

    def get_patient(self, patient_id: int) -> PatientRecord | None:
        rows = self.api.select(
            "patients",
            "id,source_record_key,identifier_masked,full_name,date_of_birth,email,contact_mobile,version,deleted_at",
            filters={"id": f"eq.{patient_id}", "deleted_at": "is.null"},
            limit=1,
        )
        return _patient_from_row(rows[0]) if rows else None

    def create_patient(self, request: PatientCreateRequest, actor: str) -> PatientRecord:
        row = self.api.rpc(
            "epicenter_create_patient",
            {
                "p_clinic_id": self.clinic_id,
                "p_source_record_key": request.source_record_key,
                "p_identifier_hash": request.identifier_hash,
                "p_identifier_masked": request.identifier_masked,
                "p_full_name": request.full_name,
                "p_date_of_birth": request.date_of_birth.isoformat() if request.date_of_birth else None,
                "p_email": request.email,
                "p_contact_mobile": request.contact_mobile,
                "p_reason": request.reason,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _patient_from_row(row)

    def update_patient(self, patient_id: int, request: PatientUpdateRequest, actor: str) -> PatientRecord:
        row = self.api.rpc(
            "epicenter_update_patient",
            {
                "p_patient_id": patient_id,
                "p_clinic_id": self.clinic_id,
                "p_expected_version": request.expected_version,
                "p_full_name": request.full_name,
                "p_email": request.email,
                "p_contact_mobile": request.contact_mobile,
                "p_reason": request.reason,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _patient_from_row(row)

    def delete_patient(self, patient_id: int, request: PatientDeleteRequest, actor: str) -> PatientRecord:
        row = self.api.rpc(
            "epicenter_soft_delete_patient",
            {
                "p_patient_id": patient_id,
                "p_clinic_id": self.clinic_id,
                "p_expected_version": request.expected_version,
                "p_reason": request.reason,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _patient_from_row(row)

    def list_audit(
        self,
        *,
        limit: int,
        offset: int = 0,
        search: str | None = None,
        actor: str | None = None,
        actor_role: str | None = None,
        outcome: str | None = None,
        action_type: str | None = None,
        target_table: str | None = None,
        occurred_from: datetime | None = None,
        occurred_to: datetime | None = None,
    ) -> list[AuditRecord]:
        filters = {"clinic_id": f"eq.{self.clinic_id}"}
        if action_type:
            filters["action_type"] = f"eq.{action_type}"
        if target_table:
            filters["target_table"] = f"eq.{target_table}"
        if occurred_from:
            filters["occurred_at"] = f"gte.{occurred_from.isoformat()}"
        # PostgREST cannot express two constraints for the same mapping key, so
        # apply the upper date bound after the clinic-scoped query.
        fetch_limit = min(500, limit + offset + (200 if search or occurred_to else 0))
        rows = self.api.select(
            "audit_log",
            "id,actor_reference,action_type,target_table,target_id,details,occurred_at",
            filters=filters,
            order="occurred_at.desc,id.desc",
            limit=fetch_limit,
        )
        records = [AuditRecord(**row) for row in rows]
        if occurred_to:
            records = [record for record in records if record.occurred_at <= occurred_to]
        if search:
            needle = search.casefold()
            records = [
                record
                for record in records
                if needle
                in " ".join(
                    (
                        record.actor_reference,
                        record.action_type,
                        record.target_table,
                        record.target_id,
                    )
                ).casefold()
            ]
        if actor:
            records = [record for record in records if actor.casefold() in record.actor_reference.casefold()]
        if actor_role:
            role = actor_role.casefold()
            records = [
                record
                for record in records
                if record.actor_role == role or str(record.details.get("actor_role", "")).casefold() == role
            ]
        if outcome:
            records = [
                record
                for record in records
                if outcome.casefold()
                in str(record.details.get("outcome") or record.details.get("status") or "committed").casefold()
            ]
        return records[offset : offset + limit]

    def get_patient_home(self, patient_id: int | None = None) -> PatientHome:
        if patient_id is None:
            raise SupabaseDataError("Patient identity is required for home.", code="PT422", status_code=422)
        row = self.api.rpc("epicenter_get_patient_home", {"p_patient_id": patient_id})
        return _patient_home_from_row(row)

    def get_onboarding_state(self, subject: str, patient_id: int | None = None) -> PatientOnboardingState:
        if patient_id is None:
            raise SupabaseDataError("Patient identity is required for onboarding.", code="PT422", status_code=422)
        try:
            row = self.api.rpc(
                "epicenter_get_onboarding",
                {
                    "p_clerk_user_id": subject,
                    "p_patient_id": patient_id,
                    "p_appointment_reference": "",
                },
            )
        except SupabaseDataError as exc:
            # Demo patient ids shifted after seeding; rebind stale onboarding rows once.
            if "onboarding_patient_mismatch" not in str(exc):
                raise
            updated = self.api.update(
                "patient_onboarding_states",
                {"patient_id": patient_id},
                filters={"clerk_user_id": f"eq.{subject}"},
            )
            if not updated:
                raise
            row = self.api.rpc(
                "epicenter_get_onboarding",
                {
                    "p_clerk_user_id": subject,
                    "p_patient_id": patient_id,
                    "p_appointment_reference": "",
                },
            )
        return self._finalize_onboarding_row(row, subject=subject, patient_id=patient_id)

    def _resolve_onboarding_appointment(
        self, appointment_id: str, *, subject: str, patient_id: int
    ) -> str:
        normalized = (appointment_id or "").strip()
        if not normalized or normalized in {"pending-booking", "PENDING"}:
            return "pending-booking"
        owned = self.api.select(
            "appointments",
            "id",
            filters={
                "appointment_reference": f"eq.{normalized}",
                "patient_id": f"eq.{patient_id}",
                "deleted_at": "is.null",
            },
            limit=1,
        )
        if owned:
            return normalized
        # Personal accounts often still carry the old seeded APT-DEMO-014 default.
        self.api.update(
            "patient_onboarding_states",
            {"appointment_reference": "pending-booking"},
            filters={"clerk_user_id": f"eq.{subject}"},
        )
        return "pending-booking"

    def _finalize_onboarding_row(
        self, row: dict[str, object], *, subject: str, patient_id: int
    ) -> PatientOnboardingState:
        state = _onboarding_from_row(row, allow_manual_singpass=not self.use_synthetic_singpass)
        resolved_appointment = self._resolve_onboarding_appointment(
            state.appointment_id, subject=subject, patient_id=patient_id
        )
        if resolved_appointment != state.appointment_id:
            state = state.model_copy(update={"appointment_id": resolved_appointment})
        if state.completed or not (state.singpass_authenticated and state.insurance_completed):
            return state
        responses = self.api.select(
            "appointment_questionnaire_responses",
            "status",
            filters={"patient_id": f"eq.{patient_id}", "status": "eq.submitted"},
            limit=1,
        )
        if not responses:
            return state
        updated = self.api.update(
            "patient_onboarding_states",
            {
                "questionnaire_completed": True,
                "current_step": "complete",
                "completed": True,
            },
            filters={"clerk_user_id": f"eq.{subject}"},
        )
        if updated:
            healed = _onboarding_from_row(updated[0], allow_manual_singpass=not self.use_synthetic_singpass)
            return healed.model_copy(update={"appointment_id": resolved_appointment})
        return state

    def advance_onboarding(
        self, request: OnboardingAdvanceRequest, subject: str, patient_id: int | None = None
    ) -> PatientOnboardingState:
        if patient_id is None:
            raise SupabaseDataError("Patient identity is required for onboarding.", code="PT422", status_code=422)
        if request.singpass_fields is not None:
            profile: list[dict[str, object]] = [
                {
                    "field_id": item.field_id,
                    "label": item.label,
                    "value": item.value,
                    "source": item.source,
                    "editable": item.editable,
                }
                for item in request.singpass_fields
            ]
        elif self.use_synthetic_singpass:
            profile = [
                {
                    "field_id": item["field_id"],
                    "label": item["label"],
                    "value": item["value"],
                    "source": "Singpass / Myinfo (synthetic)",
                    "editable": False,
                }
                for item in singpass_dummy_fields()
            ]
        else:
            profile = list(singpass_field_templates(editable=True))
        row = self.api.rpc(
            "epicenter_advance_onboarding",
            {
                "p_clerk_user_id": subject,
                "p_patient_id": patient_id,
                "p_step": request.step.value,
                "p_singpass_authenticated": request.singpass_authenticated,
                "p_insurance_completed": request.insurance_completed,
                "p_questionnaire_completed": request.questionnaire_completed,
                "p_singpass_profile": profile,
                "p_appointment_reference": "",
                "p_actor_reference": subject,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        if request.step == OnboardingStep.SINGPASS and request.singpass_fields:
            self._sync_patient_from_singpass(patient_id, request.singpass_fields)
        return self._finalize_onboarding_row(row, subject=subject, patient_id=patient_id)

    def _sync_patient_from_singpass(self, patient_id: int, fields: list[SingpassProfileField]) -> None:
        values = {item.field_id: item.value.strip() for item in fields if item.value and item.value.strip()}
        if not values:
            return
        payload: dict[str, object] = {"is_synthetic": False}
        if values.get("full_name"):
            payload["full_name"] = values["full_name"]
        if values.get("email"):
            payload["email"] = values["email"]
        if values.get("contact_mobile"):
            payload["contact_mobile"] = values["contact_mobile"]
        if values.get("address"):
            payload["address"] = values["address"]
        if values.get("postal_code"):
            payload["postal_code"] = values["postal_code"]
        if values.get("sex"):
            payload["sex"] = values["sex"]
        if values.get("nationality"):
            payload["nationality"] = values["nationality"]
        if values.get("id_masked"):
            payload["identifier_masked"] = values["id_masked"]
        if values.get("date_of_birth"):
            raw = values["date_of_birth"]
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    payload["date_of_birth"] = datetime.strptime(raw, fmt).date().isoformat()
                    break
                except ValueError:
                    continue
        self.api.update("patients", payload, filters={"id": f"eq.{patient_id}"})

    def submit_onboarding_coverage(
        self,
        *,
        file_name: str,
        actor: str,
        patient_id: int | None,
        idempotency_key: str,
    ) -> PreArrivalSubmissionResult:
        if patient_id is None:
            raise SupabaseDataError("Patient identity is required for coverage upload.", code="PT422", status_code=422)
        row = self.api.rpc(
            "epicenter_submit_onboarding_coverage",
            {
                "p_patient_id": patient_id,
                "p_file_name": file_name,
                "p_clinic_id": self.clinic_id,
                "p_actor_reference": actor,
                "p_idempotency_key": idempotency_key,
            },
        )
        return PreArrivalSubmissionResult(
            processing_reference=str(row.get("processing_reference") or row.get("id") or ""),
            outcome=PatientSubmissionOutcome(str(row.get("outcome") or "under_review")),
            message="Coverage was saved to your profile for staff review. No appointment is required yet.",
            next_action=str(
                row.get("patient_next_action")
                or "Continue onboarding. You can book an appointment after these steps."
            ),
        )

    def get_prior_coverage(
        self, appointment_id: str, patient_id: int | None = None, *, first_visit: bool = False
    ) -> PriorCoverageSummary:
        from app.data.demo_repository import demo_repository

        return demo_repository.get_prior_coverage(appointment_id, patient_id, first_visit=first_visit)

    def get_patient_queue(self, patient_id: int | None = None) -> PatientQueueStatus:
        if patient_id is None:
            raise SupabaseDataError("Patient identity is required for queue.", code="PT422", status_code=422)
        row = self.api.rpc("epicenter_get_patient_queue", {"p_patient_id": patient_id})
        return _patient_queue_from_row(row)

    def get_patient_payment(self, patient_id: int | None = None) -> PatientPaymentSummary:
        if patient_id is None:
            raise SupabaseDataError("Patient identity is required for payment.", code="PT422", status_code=422)
        row = self.api.rpc("epicenter_get_patient_payment", {"p_patient_id": patient_id})
        return _patient_payment_from_row(row)

    def submit_mock_payment(
        self, request: MockPaymentRequest, actor: str, patient_id: int | None = None
    ) -> PatientPaymentSummary:
        if patient_id is None:
            raise SupabaseDataError("Patient identity is required for payment.", code="PT422", status_code=422)
        row = self.api.rpc(
            "epicenter_submit_mock_payment",
            {
                "p_patient_id": patient_id,
                "p_appointment_reference": request.appointment_id,
                "p_expected_version": request.expected_version,
                "p_idempotency_key": request.idempotency_key,
                "p_actor_reference": actor,
            },
        )
        return _patient_payment_from_row(row)

    def get_patient_records(self, patient_id: int | None = None) -> PatientVisitHistory:
        if patient_id is None:
            raise SupabaseDataError("Patient identity is required for records.", code="PT422", status_code=422)
        row = self.api.rpc("epicenter_get_patient_records", {"p_patient_id": patient_id})
        return _patient_records_from_row(row)

    def _singpass_profile_for_patient(self, patient_id: int) -> list[dict[str, object]]:
        rows = self.api.select(
            "patient_onboarding_states",
            "singpass_profile",
            filters={"patient_id": f"eq.{patient_id}"},
            order="updated_at.desc",
            limit=1,
        )
        if not rows:
            return []
        profile = rows[0].get("singpass_profile")
        if not isinstance(profile, list):
            return []
        return [item for item in profile if isinstance(item, dict)]

    def get_patient_questionnaire(
        self, appointment_id: str, patient_id: int | None = None
    ) -> PatientQuestionnaire:
        if patient_id is None:
            raise SupabaseDataError("Patient identity is required for questionnaire.", code="PT422", status_code=422)
        row = self.api.rpc(
            "epicenter_get_questionnaire",
            {
                "p_appointment_reference": appointment_id,
                "p_patient_id": patient_id,
            },
        )
        return _questionnaire_from_row(
            row,
            singpass_profile=self._singpass_profile_for_patient(patient_id),
            use_synthetic_singpass=self.use_synthetic_singpass,
        )

    def save_patient_questionnaire(
        self, request: QuestionnaireSaveRequest, actor: str, patient_id: int | None = None
    ) -> PatientQuestionnaire:
        if patient_id is None:
            raise SupabaseDataError("Patient identity is required for questionnaire.", code="PT422", status_code=422)
        answers = {field_id: value for field_id, value in request.answers.items() if value is not None}
        if request.submit:
            fields = build_general_health_fields(answers)
            missing = missing_required_fields(fields, answers)
            if missing or not request.declaration_acknowledged:
                raise ValueError("Complete the required visible answers and declaration before submitting.")
        row = self.api.rpc(
            "epicenter_save_questionnaire",
            {
                "p_appointment_reference": request.appointment_id,
                "p_patient_id": patient_id,
                "p_answers": answers,
                "p_declaration_acknowledged": request.declaration_acknowledged,
                "p_submit": request.submit,
                "p_expected_version": request.expected_version,
                "p_actor_reference": actor,
                "p_idempotency_key": request.idempotency_key,
            },
        )
        return _questionnaire_from_row(
            row,
            singpass_profile=self._singpass_profile_for_patient(patient_id),
            use_synthetic_singpass=self.use_synthetic_singpass,
        )

    def resolve_upload_link(self, token: str) -> UploadLinkSession:
        from app.data.demo_repository import demo_repository

        return demo_repository.resolve_upload_link(token)
