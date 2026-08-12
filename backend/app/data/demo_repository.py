from copy import deepcopy
from datetime import UTC, date, datetime
from hashlib import sha256
from threading import Lock

from app.domain.models import (
    ActivityEvent,
    AllocationRecommendation,
    AuditRecord,
    CounterAssignmentRequest,
    DashboardSnapshot,
    DocumentProcessingRequest,
    IntakeType,
    KioskCheckInRequest,
    Metric,
    PatientCreateRequest,
    PatientDeleteRequest,
    PatientList,
    PatientRecord,
    PatientUpdateRequest,
    PreArrivalSubmissionRequest,
    PreArrivalSubmissionResult,
    QueueTicket,
    ReadinessState,
    RecommendationDecisionRequest,
    RegistrationValidationRequest,
    RegistrationValidationResult,
    ReviewCase,
    ServiceTarget,
    SimulatorSnapshot,
    TicketTransitionRequest,
    VisitPhase,
)


def _at(hour: int, minute: int) -> datetime:
    return datetime(2026, 8, 12, hour, minute, tzinfo=UTC)


def build_demo_snapshot() -> DashboardSnapshot:
    return DashboardSnapshot(
        generated_at=_at(9, 42),
        clinic_name="Parkway Shenton · HarbourFront",
        metrics=[
            Metric(
                label="Ready before arrival", value="78%", detail="18 of 23 booked patients", trend="+9% vs baseline"
            ),
            Metric(label="Oldest review", value="18 min", detail="Q-018 · expired voucher", trend="Approaching target"),
            Metric(label="Median admin wait", value="6 min", detail="P90 14 minutes", trend="−4 min vs baseline"),
            Metric(
                label="Staff confirmations", value="31", detail="Estimated 30 sec each", trend="100% human confirmed"
            ),
        ],
        tickets=[
            QueueTicket(
                id="Q-014",
                patient_id="P-0417",
                patient_name="Loh Wei Ming",
                intake_type=IntakeType.BOOKED,
                visit_phase=VisitPhase.INCOMING,
                readiness_state=ReadinessState.READY,
                readiness_reason="all_prerequisites_passed",
                scheduled_at=_at(10, 0),
                original_ordering_at=_at(10, 0),
                waiting_minutes=0,
                expected_counter="Counter 2",
                processing_stage="Ready before arrival",
                staff_confirmed=True,
            ),
            QueueTicket(
                id="Q-015",
                patient_id="P-0398",
                patient_name="Tan Kai Xuan",
                intake_type=IntakeType.BOOKED,
                visit_phase=VisitPhase.INCOMING,
                readiness_state=ReadinessState.NEEDS_REVIEW,
                readiness_reason="missing_document",
                scheduled_at=_at(10, 15),
                original_ordering_at=_at(10, 15),
                waiting_minutes=0,
                expected_counter="Review 1",
                processing_stage="Awaiting coverage document",
                service_target=ServiceTarget.APPROACHING,
            ),
            QueueTicket(
                id="Q-017",
                patient_id="P-0442",
                patient_name="Mei Chen",
                intake_type=IntakeType.WALK_IN,
                visit_phase=VisitPhase.ONGOING,
                readiness_state=ReadinessState.PROCESSING,
                readiness_reason="processing",
                checked_in_at=_at(9, 34),
                original_ordering_at=_at(9, 34),
                waiting_minutes=8,
                actual_counter="Kiosk A",
                processing_stage="Document extraction",
            ),
            QueueTicket(
                id="Q-018",
                patient_id="P-0451",
                patient_name="Amir Loh",
                intake_type=IntakeType.WALK_IN,
                visit_phase=VisitPhase.ONGOING,
                readiness_state=ReadinessState.NEEDS_REVIEW,
                readiness_reason="expired_document",
                checked_in_at=_at(9, 24),
                original_ordering_at=_at(9, 24),
                waiting_minutes=18,
                actual_counter="Review 2",
                processing_stage="Voucher review",
                service_target=ServiceTarget.APPROACHING,
            ),
            QueueTicket(
                id="Q-019",
                patient_id="P-0458",
                patient_name="Priya Nair",
                intake_type=IntakeType.WALK_IN,
                visit_phase=VisitPhase.ONGOING,
                readiness_state=ReadinessState.READY,
                readiness_reason="all_prerequisites_passed",
                checked_in_at=_at(9, 37),
                original_ordering_at=_at(9, 37),
                waiting_minutes=5,
                actual_counter="Counter 3",
                processing_stage="Waiting to be called",
                staff_confirmed=True,
            ),
            QueueTicket(
                id="Q-011",
                patient_id="P-0371",
                patient_name="Siti Rahman",
                intake_type=IntakeType.BOOKED,
                visit_phase=VisitPhase.FINISHED,
                readiness_state=ReadinessState.READY,
                readiness_reason="completed",
                scheduled_at=_at(8, 30),
                checked_in_at=_at(8, 22),
                original_ordering_at=_at(8, 30),
                waiting_minutes=0,
                actual_counter="Counter 1",
                processing_stage="Completed 09:08",
                staff_confirmed=True,
            ),
        ],
        review_cases=[
            ReviewCase(
                id="R-015",
                ticket_id="Q-015",
                patient_name="Tan Kai Xuan",
                reason_code="missing_document",
                reason_label="Coverage document missing",
                evidence_summary="Reminder sent 08:16 · no upload received",
                waiting_minutes=0,
                service_target=ServiceTarget.APPROACHING,
                next_action="Contact patient",
            ),
            ReviewCase(
                id="R-018",
                ticket_id="Q-018",
                patient_name="Amir Loh",
                reason_code="expired_document",
                reason_label="Voucher validity expired",
                document_name="Bluepeak_voucher.pdf",
                evidence_summary="Valid until 10 Aug 2026 · source page 1",
                waiting_minutes=18,
                service_target=ServiceTarget.APPROACHING,
                next_action="Confirm replacement or self-pay",
            ),
        ],
        recommendation=AllocationRecommendation(
            id="A-009",
            status="pending",
            pressured_workstream="Assisted review",
            rationale=(
                "Two review cases are approaching the 20-minute service target "
                "while Counter 4 has been idle for 7 minutes."
            ),
            qualified_resource="Counter 4 · Nur Aisyah",
            current_wait_minutes=18,
            expected_wait_minutes=9,
            expires_at=_at(9, 48),
            constraints_checked=[
                "Registration-trained",
                "Minimum ready coverage retained",
                "Break window clear",
                "No reassignment in last 30 min",
            ],
        ),
        activity=[
            ActivityEvent(
                id="E-1",
                occurred_at=_at(9, 41),
                label="Q-019 became ready",
                detail="Staff confirmed the rules-matched package; original ticket retained.",
                tone="success",
            ),
            ActivityEvent(
                id="E-2",
                occurred_at=_at(9, 38),
                label="Q-017 document received",
                detail="Walk-in intake captured at nurse-supervised Kiosk A.",
                tone="neutral",
            ),
            ActivityEvent(
                id="E-3",
                occurred_at=_at(9, 35),
                label="Allocation advice created",
                detail="Recommendation A-009 expires at 09:48 and requires approval.",
                tone="attention",
            ),
        ],
    )


class DemoRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._snapshot = build_demo_snapshot()
        self._idempotent_results: dict[tuple[str, str], object] = {}
        self._patient_identifier_hashes = {1: "5f5deb21ad3e0acb62567fa6e14f67db32c094351c3058ca784641d240ec8f59"}
        self._patients = {
            1: PatientRecord(
                id=1,
                source_record_key="registration:0001",
                identifier_masked="*****854C",
                full_name="Tan Kai Xuan",
                date_of_birth=date(1993, 12, 18),
                email="kai.tan78@gmail.com",
                contact_mobile="89478454",
                version=1,
            )
        }
        self._audit_records: list[AuditRecord] = []

    def snapshot(self) -> DashboardSnapshot:
        with self._lock:
            return deepcopy(self._snapshot)

    def find_ticket(self, ticket_id: str) -> QueueTicket | None:
        with self._lock:
            return next((ticket for ticket in self._snapshot.tickets if ticket.id == ticket_id), None)

    def list_simulator_snapshots(self) -> list[SimulatorSnapshot]:
        scenarios = (
            ("snapshot_dynamic", "dynamic_allocation", "Single-ticket flow with human-approved dynamic allocation"),
            ("snapshot_serial", "serial_baseline", "Serial baseline with shared arrivals and service times"),
            ("snapshot_single_ticket", "single_ticket", "Epicenter single-ticket readiness workflow"),
        )
        return [
            SimulatorSnapshot(
                id=snapshot_id,
                scenario_id=scenario_id,
                scenario_version="demo-v1",
                seed=20260809,
                assumptions_version="demo-v1",
                snapshot_hash=f"{scenario_id}-20260809-demo-v1",
                snapshot_payload={"synthetic": True, "description": description},
            )
            for snapshot_id, scenario_id, description in scenarios
        ]

    def validate_registration(
        self,
        request: RegistrationValidationRequest,
        actor: str = "synthetic-patient",
        patient_id: int | None = None,
    ) -> RegistrationValidationResult:
        key = ("registration_validation", request.idempotency_key)
        with self._lock:
            existing = self._idempotent_results.get(key)
            if isinstance(existing, RegistrationValidationResult):
                return deepcopy(existing)
            patient = self._patients[1]
            fields = {
                "identifier": (
                    "source_validated"
                    if request.identifier_hash == self._patient_identifier_hashes[patient.id]
                    else "conflict"
                ),
                "full_name": (
                    "source_validated" if request.full_name.casefold() == patient.full_name.casefold() else "conflict"
                ),
                "date_of_birth": "source_validated" if request.date_of_birth == patient.date_of_birth else "conflict",
                "email": (
                    "source_validated" if request.email.casefold() == (patient.email or "").casefold() else "conflict"
                ),
            }
            accepted = all(result == "source_validated" for result in fields.values())
            result = RegistrationValidationResult(
                id=f"VAL-{sha256(request.idempotency_key.encode()).hexdigest()[:12].upper()}",
                outcome="accepted" if accepted else "rejected",
                field_results=fields,
                patient_reason_code="registration_confirmed" if accepted else "registration_details_mismatch",
                patient_next_action=(
                    "Continue to the required pre-arrival steps."
                    if accepted
                    else "Review your booking details or ask clinic staff for help."
                ),
                version=1,
            )
            self._idempotent_results[key] = deepcopy(result)
            return result

    def submit_prearrival(
        self,
        request: PreArrivalSubmissionRequest,
        actor: str = "synthetic-patient",
        patient_id: int | None = None,
    ) -> PreArrivalSubmissionResult:
        key = ("prearrival_submission", request.idempotency_key)
        with self._lock:
            existing = self._idempotent_results.get(key)
            if isinstance(existing, PreArrivalSubmissionResult):
                return deepcopy(existing)
            result = PreArrivalSubmissionResult(
                processing_reference=f"PRE-{sha256(request.idempotency_key.encode()).hexdigest()[:10].upper()}",
                message="The submission was stored for current administrative checks.",
                next_action="Clinic staff will confirm the result before it becomes final.",
            )
            self._idempotent_results[key] = deepcopy(result)
            return result

    def transition_ticket(
        self, ticket_id: str, request: TicketTransitionRequest, actor: str = "synthetic-staff"
    ) -> QueueTicket:
        from app.services.readiness import transition_ticket

        with self._lock:
            key = ("ticket_transition", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, QueueTicket):
                return deepcopy(existing)
            index = next(index for index, ticket in enumerate(self._snapshot.tickets) if ticket.id == ticket_id)
            updated = transition_ticket(self._snapshot.tickets[index], request)
            updated.version += 1
            self._snapshot.tickets[index] = updated
            self._snapshot.generated_at = datetime.now(UTC)
            self._idempotent_results[key] = deepcopy(updated)
            return deepcopy(updated)

    def add_ticket(self, ticket: QueueTicket) -> QueueTicket:
        with self._lock:
            self._snapshot.tickets.insert(0, ticket)
            self._snapshot.generated_at = datetime.now(UTC)
            return deepcopy(ticket)

    def add_walk_in(self, request: KioskCheckInRequest, actor: str = "synthetic-staff") -> QueueTicket:
        from app.services.kiosk import create_walk_in_ticket

        with self._lock:
            key = ("kiosk_check_in", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, QueueTicket):
                return deepcopy(existing)
            highest = max(int(ticket.id.removeprefix("Q-")) for ticket in self._snapshot.tickets)
            ticket = create_walk_in_ticket(f"Q-{highest + 1:03d}", request)
            self._snapshot.tickets.insert(0, ticket)
            self._snapshot.generated_at = datetime.now(UTC)
            self._idempotent_results[key] = deepcopy(ticket)
            return deepcopy(ticket)

    def process_document(
        self, ticket_id: str, request: DocumentProcessingRequest, actor: str = "synthetic-staff"
    ) -> QueueTicket:
        transition = TicketTransitionRequest(
            readiness_state=(
                ReadinessState.READY
                if request.readiness_status == "pass"
                and request.match_status == "clean"
                and request.all_required_documents_present
                and request.all_documents_valid
                and request.staff_confirmed
                else ReadinessState.NEEDS_REVIEW
            ),
            reason="all_prerequisites_passed" if request.readiness_status == "pass" else request.reason,
            staff_confirmed=request.staff_confirmed,
            expected_version=request.expected_version,
            idempotency_key=request.idempotency_key,
        )
        return self.transition_ticket(ticket_id, transition, actor)

    def assign_counter(
        self, ticket_id: str, request: CounterAssignmentRequest, actor: str = "synthetic-staff"
    ) -> QueueTicket:
        with self._lock:
            key = ("counter_assignment", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, QueueTicket):
                return deepcopy(existing)
            index = next(index for index, ticket in enumerate(self._snapshot.tickets) if ticket.id == ticket_id)
            current = self._snapshot.tickets[index]
            if current.version != request.expected_version:
                raise ValueError("The ticket changed since it was loaded. Refresh and try again.")
            updated = deepcopy(current)
            if updated.visit_phase is VisitPhase.INCOMING:
                updated.expected_counter = request.counter_number
            else:
                updated.actual_counter = request.counter_number
            updated.version += 1
            self._snapshot.tickets[index] = updated
            self._idempotent_results[key] = deepcopy(updated)
            return updated

    def decide_recommendation(
        self,
        recommendation_id: str,
        request: RecommendationDecisionRequest,
        actor: str = "synthetic-staff",
    ) -> AllocationRecommendation:
        with self._lock:
            key = ("allocation_decision", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, AllocationRecommendation):
                return deepcopy(existing)
            if self._snapshot.recommendation.id != recommendation_id:
                raise KeyError(recommendation_id)
            if self._snapshot.recommendation.version != request.expected_version:
                raise ValueError("The recommendation changed since it was loaded. Refresh and try again.")
            self._snapshot.recommendation.status = request.decision
            self._snapshot.recommendation.version += 1
            self._snapshot.generated_at = datetime.now(UTC)
            self._idempotent_results[key] = deepcopy(self._snapshot.recommendation)
            return deepcopy(self._snapshot.recommendation)

    def next_ticket_id(self) -> str:
        with self._lock:
            highest = max(int(ticket.id.removeprefix("Q-")) for ticket in self._snapshot.tickets)
            return f"Q-{highest + 1:03d}"

    def list_patients(self, *, search: str | None, offset: int, limit: int) -> PatientList:
        with self._lock:
            records = [patient for patient in self._patients.values() if patient.deleted_at is None]
            if search:
                records = [patient for patient in records if search.casefold() in patient.full_name.casefold()]
            records.sort(key=lambda patient: patient.full_name)
            return PatientList(records=deepcopy(records[offset : offset + limit]), offset=offset, limit=limit)

    def get_patient(self, patient_id: int) -> PatientRecord | None:
        with self._lock:
            patient = self._patients.get(patient_id)
            return deepcopy(patient) if patient and patient.deleted_at is None else None

    def create_patient(self, request: PatientCreateRequest, actor: str = "synthetic-staff") -> PatientRecord:
        with self._lock:
            key = ("patient_create", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, PatientRecord):
                return deepcopy(existing)
            patient_id = max(self._patients, default=0) + 1
            patient = PatientRecord(
                id=patient_id,
                version=1,
                **request.model_dump(exclude={"identifier_hash", "reason", "idempotency_key"}),
            )
            self._patients[patient_id] = patient
            self._patient_identifier_hashes[patient_id] = request.identifier_hash
            self._idempotent_results[key] = deepcopy(patient)
            return deepcopy(patient)

    def update_patient(
        self, patient_id: int, request: PatientUpdateRequest, actor: str = "synthetic-staff"
    ) -> PatientRecord:
        with self._lock:
            key = ("patient_update", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, PatientRecord):
                return deepcopy(existing)
            current = self._patients.get(patient_id)
            if current is None or current.deleted_at is not None:
                raise KeyError(patient_id)
            if current.version != request.expected_version:
                raise ValueError("The patient changed since it was loaded. Refresh and try again.")
            updated = current.model_copy(
                update={
                    key: value
                    for key, value in request.model_dump().items()
                    if key in {"full_name", "email", "contact_mobile"} and value is not None
                }
            )
            updated.version += 1
            self._patients[patient_id] = updated
            self._idempotent_results[key] = deepcopy(updated)
            return deepcopy(updated)

    def delete_patient(
        self, patient_id: int, request: PatientDeleteRequest, actor: str = "synthetic-staff"
    ) -> PatientRecord:
        with self._lock:
            key = ("patient_delete", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, PatientRecord):
                return deepcopy(existing)
            current = self._patients.get(patient_id)
            if current is None or current.deleted_at is not None:
                raise KeyError(patient_id)
            if current.version != request.expected_version:
                raise ValueError("The patient changed since it was loaded. Refresh and try again.")
            deleted = current.model_copy(update={"deleted_at": datetime.now(UTC), "version": current.version + 1})
            self._patients[patient_id] = deleted
            self._patient_identifier_hashes.pop(patient_id, None)
            self._idempotent_results[key] = deepcopy(deleted)
            return deepcopy(deleted)

    def list_audit(self, *, limit: int) -> list[AuditRecord]:
        with self._lock:
            return deepcopy(self._audit_records[:limit])


demo_repository = DemoRepository()
