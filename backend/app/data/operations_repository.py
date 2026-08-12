from __future__ import annotations

from datetime import UTC, date, datetime
from statistics import median
from typing import Any, Protocol

from app.data.supabase_client import SupabaseDataApi, SupabaseDataError
from app.domain.models import (
    ActivityEvent,
    AllocationRecommendation,
    AuditRecord,
    CounterAssignmentRequest,
    DashboardSnapshot,
    DocumentProcessingRequest,
    KioskCheckInRequest,
    Metric,
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
    PatientUpdateRequest,
    PatientVisitHistory,
    PatientVisitRecord,
    PreArrivalSubmissionRequest,
    PreArrivalSubmissionResult,
    PriorCoverageSummary,
    QueueTicket,
    QuestionnaireSaveRequest,
    RecommendationDecisionRequest,
    RegistrationValidationRequest,
    RegistrationValidationResult,
    ReviewCase,
    SimulatorSnapshot,
    SingpassProfileField,
    TicketTransitionRequest,
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

    def process_document(
        self, ticket_id: str, request: DocumentProcessingRequest, actor: str
    ) -> QueueTicket: ...

    def assign_counter(self, ticket_id: str, request: CounterAssignmentRequest, actor: str) -> QueueTicket: ...

    def decide_recommendation(
        self,
        recommendation_id: str,
        request: RecommendationDecisionRequest,
        actor: str,
    ) -> AllocationRecommendation: ...

    def list_patients(self, *, search: str | None, offset: int, limit: int) -> PatientList: ...

    def get_patient(self, patient_id: int) -> PatientRecord | None: ...

    def create_patient(self, request: PatientCreateRequest, actor: str) -> PatientRecord: ...

    def update_patient(self, patient_id: int, request: PatientUpdateRequest, actor: str) -> PatientRecord: ...

    def delete_patient(self, patient_id: int, request: PatientDeleteRequest, actor: str) -> PatientRecord: ...

    def list_audit(self, *, limit: int) -> list[AuditRecord]: ...


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
        original_ordering_at=row["original_ordering_at"],
        waiting_minutes=int(row.get("waiting_minutes") or 0),
        expected_counter=row.get("expected_counter_number"),
        actual_counter=row.get("counter_number"),
        processing_stage=str(row["processing_stage"]),
        service_target=str(row.get("service_target") or "on_track"),
        staff_confirmed=bool(row.get("staff_confirmed")),
        clinical_escalation=bool(row.get("clinical_escalation")),
        version=int(row.get("version") or 1),
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

    def process_document(
        self, ticket_id: str, request: DocumentProcessingRequest, actor: str
    ) -> QueueTicket:
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

    def assign_counter(self, ticket_id: str, request: CounterAssignmentRequest, actor: str) -> QueueTicket:
        row = self.api.rpc(
            "epicenter_assign_counter",
            {
                "p_ticket_id": ticket_id,
                "p_expected_version": request.expected_version,
                "p_counter_number": request.counter_number,
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

    def list_patients(self, *, search: str | None, offset: int, limit: int) -> PatientList:
        filters = {"deleted_at": "is.null"}
        if search:
            safe_search = search.replace("%", "").replace("*", "").strip()
            if safe_search:
                filters["full_name"] = f"ilike.*{safe_search}*"
        rows = self.api.select(
            "patients",
            "id,source_record_key,identifier_masked,full_name,date_of_birth,email,contact_mobile,version,deleted_at",
            filters=filters,
            order="full_name.asc",
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

    def list_audit(self, *, limit: int) -> list[AuditRecord]:
        rows = self.api.select(
            "audit_log",
            "id,actor_reference,action_type,target_table,target_id,details,occurred_at",
            filters={"clinic_id": f"eq.{self.clinic_id}"},
            order="occurred_at.desc",
            limit=limit,
        )
        return [AuditRecord(**row) for row in rows]

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

    def _finalize_onboarding_row(
        self, row: dict[str, object], *, subject: str, patient_id: int
    ) -> PatientOnboardingState:
        state = _onboarding_from_row(row, allow_manual_singpass=not self.use_synthetic_singpass)
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
            return _onboarding_from_row(updated[0], allow_manual_singpass=not self.use_synthetic_singpass)
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
