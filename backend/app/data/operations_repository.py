from __future__ import annotations

from datetime import UTC, datetime
from statistics import median
from typing import Protocol

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
    PatientCreateRequest,
    PatientDeleteRequest,
    PatientList,
    PatientRecord,
    PatientSubmissionOutcome,
    PatientUpdateRequest,
    PreArrivalSubmissionRequest,
    PreArrivalSubmissionResult,
    QueueTicket,
    RecommendationDecisionRequest,
    RegistrationValidationRequest,
    RegistrationValidationResult,
    ReviewCase,
    SimulatorSnapshot,
    TicketTransitionRequest,
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
