from __future__ import annotations

from datetime import UTC, datetime
from statistics import median
from typing import Protocol

from app.data.supabase_client import SupabaseDataApi, SupabaseDataError
from app.domain.models import (
    ActivityEvent,
    AllocationRecommendation,
    AuditRecord,
    BillingConfirmRequest,
    ChecklistItem,
    ChecklistStatus,
    DashboardSnapshot,
    DocumentConfirmRequest,
    DocumentProcessingRequest,
    FormsConfirmRequest,
    IdentityConfirmRequest,
    KioskCheckInRequest,
    MedicationDispense,
    MedicationDispenseRequest,
    Metric,
    PackageConfirmRequest,
    PatientCreateRequest,
    PatientDeleteRequest,
    PatientList,
    PatientRecord,
    PatientSubmissionOutcome,
    PatientSummary,
    PatientUpdateRequest,
    PhysicalFormsReceivedRequest,
    PreArrivalSubmissionRequest,
    PreArrivalSubmissionResult,
    QueueTicket,
    RecommendationDecisionRequest,
    RecordChecklist,
    RegistrationValidationRequest,
    RegistrationValidationResult,
    ReviewCase,
    SimulatorSnapshot,
    TicketTransitionRequest,
    TpaSubmission,
    TpaSubmissionConfirmRequest,
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

    def transition_ticket(self, ticket_id: str, request: TicketTransitionRequest, actor: str) -> QueueTicket: ...

    def add_walk_in(self, request: KioskCheckInRequest, actor: str) -> QueueTicket: ...

    def process_document(self, ticket_id: str, request: DocumentProcessingRequest, actor: str) -> QueueTicket: ...

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


class SupabaseOperationsRepository:
    def __init__(self, api: SupabaseDataApi, *, clinic_id: str = "clinic_harbourfront") -> None:
        self.api = api
        self.clinic_id = clinic_id

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
                "id,appointment_id,issuer_name,document_type,updated_at",
                filters={"appointment_id": f"in.({','.join(appointment_ids)})", "deleted_at": "is.null"},
                order="updated_at.desc",
            )
            if appointment_ids
            else []
        )
        coverage_by_appointment: dict[str, dict[str, object]] = {}
        for row in coverage_rows:
            coverage_by_appointment.setdefault(str(row["appointment_id"]), row)

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
            eligibility_row = eligibility_by_appointment.get(str(appointment_id)) if appointment_id else None
            matched_rule = rules_by_id.get(str(eligibility_row.get("matched_rule_id"))) if eligibility_row else None
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
        raise NotImplementedError(
            "Document confirmation is only available in the demo repository "
            "pending the deferred production migration (task #13)."
        )

    def confirm_package(self, ticket_id: str, request: PackageConfirmRequest, actor: str) -> QueueTicket:
        raise NotImplementedError(
            "Package confirmation is only available in the demo repository "
            "pending the deferred production migration (task #13)."
        )

    def confirm_billing(self, ticket_id: str, request: BillingConfirmRequest, actor: str) -> QueueTicket:
        raise NotImplementedError(
            "Billing/queue confirmation is only available in the demo repository "
            "pending the deferred production migration (task #13)."
        )

    def confirm_identity(self, ticket_id: str, request: IdentityConfirmRequest, actor: str) -> QueueTicket:
        raise NotImplementedError(
            "Identity confirmation is only available in the demo repository "
            "pending the deferred production migration (task #13)."
        )

    def confirm_forms(self, ticket_id: str, request: FormsConfirmRequest, actor: str) -> QueueTicket:
        raise NotImplementedError(
            "Forms confirmation is only available in the demo repository "
            "pending the deferred production migration (task #13)."
        )

    def mark_physical_forms_received(
        self, ticket_id: str, request: PhysicalFormsReceivedRequest, actor: str
    ) -> QueueTicket:
        raise NotImplementedError(
            "Physical forms receipt is only available in the demo repository "
            "pending the deferred production migration (task #13)."
        )

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
