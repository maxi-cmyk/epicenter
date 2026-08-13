from copy import deepcopy
from datetime import UTC, date, datetime
from hashlib import sha256
from threading import Lock

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
    IntakeType,
    KioskCheckInRequest,
    MedicationDispense,
    MedicationDispenseRequest,
    MedicationItem,
    Metric,
    PackageConfirmRequest,
    PatientCreateRequest,
    PatientDeleteRequest,
    PatientList,
    PatientRecord,
    PatientSummary,
    PatientUpdateRequest,
    PhysicalFormsReceivedRequest,
    PreArrivalSubmissionRequest,
    PreArrivalSubmissionResult,
    QueueTicket,
    ReadinessState,
    RecommendationDecisionRequest,
    RecordChecklist,
    RegistrationValidationRequest,
    RegistrationValidationResult,
    ReviewCase,
    ServiceTarget,
    SimulatorSnapshot,
    TicketTransitionRequest,
    TpaSubmission,
    TpaSubmissionConfirmRequest,
    TpaSubmissionStatus,
    VisitPhase,
)


def _at(hour: int, minute: int) -> datetime:
    return datetime(2026, 8, 12, hour, minute, tzinfo=UTC)


def _checklist(
    *,
    patient: PatientSummary,
    coverage_status: ChecklistStatus,
    coverage_detail: str | None,
    eligibility_status: ChecklistStatus,
    eligibility_detail: str | None,
    general_status: ChecklistStatus = ChecklistStatus.NOT_REQUIRED,
    general_detail: str | None = None,
    occupational_status: ChecklistStatus = ChecklistStatus.NOT_REQUIRED,
    occupational_detail: str | None = None,
) -> RecordChecklist:
    return RecordChecklist(
        patient=patient,
        items=[
            ChecklistItem(label="Patient details", status=ChecklistStatus.PASS, detail=patient.identifier_masked),
            ChecklistItem(label="Coverage document", status=coverage_status, detail=coverage_detail),
            ChecklistItem(label="Eligibility match", status=eligibility_status, detail=eligibility_detail),
            ChecklistItem(label="General health questionnaire", status=general_status, detail=general_detail),
            ChecklistItem(
                label="Occupational health questionnaire", status=occupational_status, detail=occupational_detail
            ),
        ],
    )


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
                expected_room="Room 2 · Dr Farah",
                processing_stage="Ready before arrival",
                staff_confirmed=True,
                is_checkup=True,
                matched_package="WELL2 — Comprehensive Screen",
                billing_code="WELL2-STD",
                uncovered_cost=0.0,
                queue_number="Q014",
                record_checklist=_checklist(
                    patient=PatientSummary(
                        full_name="Loh Wei Ming",
                        identifier_masked="S***946C",
                        date_of_birth=date(1988, 3, 15),
                        contact_mobile="9**1 234",
                        address="12 Function Place",
                    ),
                    coverage_status=ChecklistStatus.PASS,
                    coverage_detail="Meridian (MRDEB) · voucher",
                    eligibility_status=ChecklistStatus.PASS,
                    eligibility_detail="WELL2 — Comprehensive Screen",
                    general_status=ChecklistStatus.PASS,
                    general_detail="Verified",
                ),
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
                expected_room="Review 1",
                processing_stage="Awaiting coverage document",
                service_target=ServiceTarget.APPROACHING,
                record_checklist=_checklist(
                    patient=PatientSummary(
                        full_name="Tan Kai Xuan",
                        identifier_masked="S***398D",
                        date_of_birth=date(1991, 7, 2),
                        contact_mobile="8**4 552",
                        address="88 Harbour Rise",
                    ),
                    coverage_status=ChecklistStatus.FAIL,
                    coverage_detail="No coverage document received",
                    eligibility_status=ChecklistStatus.FAIL,
                    eligibility_detail=None,
                    general_status=ChecklistStatus.PENDING,
                    general_detail="Not yet submitted",
                ),
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
                actual_room="Kiosk A",
                processing_stage="Document extraction",
                record_checklist=_checklist(
                    patient=PatientSummary(
                        full_name="Mei Chen",
                        identifier_masked="S***442F",
                        date_of_birth=date(1995, 11, 20),
                        contact_mobile="9**7 108",
                        address="4 Riverwalk Avenue",
                    ),
                    coverage_status=ChecklistStatus.PENDING,
                    coverage_detail="Extraction in progress",
                    eligibility_status=ChecklistStatus.PENDING,
                    eligibility_detail=None,
                ),
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
                actual_room="Review 2",
                processing_stage="Voucher review",
                service_target=ServiceTarget.APPROACHING,
                matched_package="Executive screening",
                billing_code="EXEC-STD",
                uncovered_cost=45.0,
                queue_number="Q018",
                record_checklist=_checklist(
                    patient=PatientSummary(
                        full_name="Amir Loh",
                        identifier_masked="S***451A",
                        date_of_birth=date(1983, 1, 9),
                        contact_mobile="9**3 671",
                        address="21 Bluepeak Lane",
                    ),
                    coverage_status=ChecklistStatus.FAIL,
                    coverage_detail="Bluepeak (BLPHS) · voucher — expired 10 Aug 2026",
                    eligibility_status=ChecklistStatus.PENDING,
                    eligibility_detail="Executive screening",
                    general_status=ChecklistStatus.PASS,
                    general_detail="Verified",
                ),
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
                actual_room="Room 3 · Dr Wong",
                processing_stage="Waiting to be called",
                staff_confirmed=True,
                matched_package="PEE226 — Basic Screen",
                billing_code="PEE226-CHAS",
                uncovered_cost=8.5,
                queue_number="Q019",
                record_checklist=_checklist(
                    patient=PatientSummary(
                        full_name="Priya Nair",
                        identifier_masked="S***458G",
                        date_of_birth=date(1990, 5, 30),
                        contact_mobile="8**9 214",
                        address="17 Coral Drive",
                    ),
                    coverage_status=ChecklistStatus.PASS,
                    coverage_detail="CHAS · referral letter",
                    eligibility_status=ChecklistStatus.PASS,
                    eligibility_detail="PEE226 — Basic Screen",
                    general_status=ChecklistStatus.PASS,
                    general_detail="Verified",
                ),
            ),
            QueueTicket(
                id="Q-020",
                patient_id="P-0463",
                patient_name="Marcus Lim",
                intake_type=IntakeType.WALK_IN,
                visit_phase=VisitPhase.ONGOING,
                readiness_state=ReadinessState.READY,
                readiness_reason="all_prerequisites_passed",
                checked_in_at=_at(9, 20),
                original_ordering_at=_at(9, 20),
                waiting_minutes=22,
                actual_room="Room 2 · Dr Farah",
                processing_stage="Consultation in progress",
                staff_confirmed=True,
                matched_package="TPA-GP01 — GP Consultation",
                billing_code="TPA-GP01",
                uncovered_cost=0.0,
                queue_number="Q020",
                record_checklist=_checklist(
                    patient=PatientSummary(
                        full_name="Marcus Lim",
                        identifier_masked="S***463B",
                        date_of_birth=date(1985, 4, 2),
                        contact_mobile="9**2 640",
                        address="30 Northshore Drive",
                    ),
                    coverage_status=ChecklistStatus.PASS,
                    coverage_detail="Meridian TPA (MRD-TPA) · membership card",
                    eligibility_status=ChecklistStatus.PASS,
                    eligibility_detail="TPA-GP01 — GP Consultation",
                    general_status=ChecklistStatus.PASS,
                    general_detail="Verified",
                ),
                documents=[
                    Document(
                        id="TPADOC-Q020-BEN",
                        category=DocumentCategory.BENEFIT_STRUCTURE,
                        issuer_code="MRD-TPA",
                        issuer_name="Meridian TPA",
                        document_type="Benefit Schedule 2026",
                        reference_number="BEN-2026-0417",
                        valid_from=date(2026, 1, 1),
                        valid_to=date(2026, 12, 31),
                        facts={
                            "membership_number": "MTP-88213045",
                            "plan_tier": "Standard",
                            "annual_limit": "2000.00",
                            "copay_percentage": "10",
                        },
                    ),
                    Document(
                        id="TPADOC-Q020-AUTH",
                        category=DocumentCategory.AUTHORISATION_LETTER,
                        issuer_code="MRD-TPA",
                        issuer_name="Meridian TPA",
                        document_type="Pre-authorisation letter",
                        reference_number="AUTH-88213-GP01",
                        valid_from=date(2026, 8, 1),
                        valid_to=date(2026, 8, 31),
                        facts={
                            "authorising_officer": "Grace Lim",
                            "approval_number": "AUTH-88213-GP01",
                            "scope": "GP Consultation",
                        },
                    ),
                    Document(
                        id="TPADOC-Q020-CODE",
                        category=DocumentCategory.CODING_SCHEME,
                        issuer_code="MRD-TPA",
                        issuer_name="Meridian TPA",
                        document_type="Procedure code reference",
                        reference_number="TPA-GP01",
                        facts={
                            "procedure_code": "TPA-GP01",
                            "code_scheme": "Meridian TPA coding table v3",
                            "package_name": "GP Consultation",
                        },
                    ),
                    Document(
                        id="TPADOC-Q020-FORM",
                        category=DocumentCategory.FORM,
                        issuer_code="NORTHSHORE-LOGISTICS",
                        issuer_name="Northshore Logistics",
                        document_type="Employer claim form",
                        reference_number="CLAIM-0463",
                        facts={
                            "employer_code": "NORTHSHORE-LOGISTICS",
                            "billing_arrangement": "Direct billing to employer",
                        },
                    ),
                ],
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
                completed_at=_at(9, 8),
                original_ordering_at=_at(8, 30),
                waiting_minutes=0,
                actual_room="Room 1 · Dr Tan",
                processing_stage="Completed 09:08",
                staff_confirmed=True,
                matched_package="WELL2 — Comprehensive Screen",
                package_confirmed=True,
                package_confirmed_by="Nurse Aisyah",
                package_confirmed_at=_at(8, 25),
                billing_code="WELL2-STD",
                uncovered_cost=0.0,
                queue_number="Q011",
                billing_confirmed=True,
                billing_confirmed_by="Nurse Aisyah",
                billing_confirmed_at=_at(8, 26),
                record_checklist=_checklist(
                    patient=PatientSummary(
                        full_name="Siti Rahman",
                        identifier_masked="S***371K",
                        date_of_birth=date(1979, 9, 14),
                        contact_mobile="9**5 830",
                        address="6 Meridian Court",
                    ),
                    coverage_status=ChecklistStatus.PASS,
                    coverage_detail="Meridian (MRDEB) · voucher",
                    eligibility_status=ChecklistStatus.PASS,
                    eligibility_detail="WELL2 — Comprehensive Screen",
                    general_status=ChecklistStatus.PASS,
                    general_detail="Verified",
                ),
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
        completed_visit = next(ticket for ticket in self._snapshot.tickets if ticket.id == "Q-011")
        self._record_audit(
            actor="synthetic-system",
            action_type="visit_completed",
            target_table="queue_entries",
            target_id=completed_visit.id,
            details={
                "ticket_id": completed_visit.id,
                "visit_phase": completed_visit.visit_phase.value,
                "outcome": "completed",
                "visit_times": self._visit_times(completed_visit),
            },
            occurred_at=completed_visit.completed_at,
        )
        self._medication_dispenses: dict[str, MedicationDispense] = {
            "Q-020": MedicationDispense(
                id="MED-Q-020",
                ticket_id="Q-020",
                items=[
                    MedicationItem(name="Paracetamol 500mg", quantity=20, unit_cost=0.15),
                    MedicationItem(name="Amoxicillin 250mg", quantity=15, unit_cost=0.40),
                ],
                total_cost=9.0,
                dispensed_by="Pharmacist Nur Aisyah",
                dispensed_at=_at(9, 55),
            )
        }
        seeded_medication = self._medication_dispenses["Q-020"]
        medication_visit = next(ticket for ticket in self._snapshot.tickets if ticket.id == "Q-020")
        self._record_audit(
            actor=seeded_medication.dispensed_by,
            action_type="medication_dispensed",
            target_table="medication_dispenses",
            target_id=seeded_medication.id,
            details={
                "ticket_id": seeded_medication.ticket_id,
                "medication": [item.model_dump(mode="json") for item in seeded_medication.items],
                "total_cost": seeded_medication.total_cost,
                "currency": "SGD",
                "dispensed_at": seeded_medication.dispensed_at.isoformat(),
                "visit_times": self._visit_times(medication_visit),
                "version": seeded_medication.version,
            },
            occurred_at=seeded_medication.dispensed_at,
        )
        self._record_audit(
            actor=completed_visit.billing_confirmed_by or "synthetic-system",
            action_type="payment_details_confirmed",
            target_table="queue_entries",
            target_id=completed_visit.id,
            details={
                "ticket_id": completed_visit.id,
                "payment": {
                    "mode": "synthetic_demo",
                    "status": "amount_due_confirmed",
                    "currency": "SGD",
                    "billing_code": completed_visit.billing_code,
                    "amount_due": completed_visit.uncovered_cost,
                    "queue_number": completed_visit.queue_number,
                    "confirmed_at": completed_visit.billing_confirmed_at.isoformat()
                    if completed_visit.billing_confirmed_at
                    else None,
                },
                "visit_times": self._visit_times(completed_visit),
                "version": completed_visit.version,
            },
            occurred_at=completed_visit.billing_confirmed_at,
        )
        self._tpa_submissions: dict[str, TpaSubmission] = {}

    @staticmethod
    def _visit_times(ticket: QueueTicket) -> dict[str, str | None]:
        return {
            "scheduled_at": ticket.scheduled_at.isoformat() if ticket.scheduled_at else None,
            "checked_in_at": ticket.checked_in_at.isoformat() if ticket.checked_in_at else None,
            "completed_at": ticket.completed_at.isoformat() if ticket.completed_at else None,
        }

    def _record_audit(
        self,
        *,
        actor: str,
        action_type: str,
        target_table: str,
        target_id: str,
        details: dict[str, object],
        occurred_at: datetime | None = None,
    ) -> None:
        actor_value = actor.casefold()
        if action_type in {"medication_dispensed", "tpa_submission_confirmed"}:
            actor_role = "pharmacist"
        elif "system" in actor_value or "worker" in actor_value:
            actor_role = "system"
        elif "admin" in actor_value:
            actor_role = "administrator"
        else:
            actor_role = "nurse"
        next_id = max((record.id for record in self._audit_records), default=0) + 1
        self._audit_records.append(
            AuditRecord(
                id=next_id,
                actor_reference=actor,
                actor_role=actor_role,
                action_type=action_type,
                target_table=target_table,
                target_id=target_id,
                details=details,
                occurred_at=occurred_at or datetime.now(UTC),
            )
        )
        self._audit_records.sort(key=lambda record: (record.occurred_at, record.id), reverse=True)

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
            self._record_audit(
                actor=actor,
                action_type="visit_checked_in",
                target_table="queue_entries",
                target_id=ticket.id,
                details={
                    "ticket_id": ticket.id,
                    "intake_type": ticket.intake_type.value,
                    "nurse_supervisor": request.nurse_supervisor,
                    "clinical_escalation": request.clinical_escalation,
                    "visit_times": self._visit_times(ticket),
                },
                occurred_at=ticket.checked_in_at,
            )
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

    def confirm_document(
        self, ticket_id: str, document_id: str, request: DocumentConfirmRequest, actor: str = "synthetic-staff"
    ) -> QueueTicket:
        with self._lock:
            key = ("document_confirm", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, QueueTicket):
                return deepcopy(existing)
            index = next(index for index, ticket in enumerate(self._snapshot.tickets) if ticket.id == ticket_id)
            current = self._snapshot.tickets[index]
            if current.version != request.expected_version:
                raise ValueError("The ticket changed since it was loaded. Refresh and try again.")
            doc_index = next(
                (i for i, doc in enumerate(current.documents) if doc.id == document_id),
                None,
            )
            if doc_index is None:
                raise KeyError(f"No document {document_id} on file for {ticket_id}")
            current_doc = current.documents[doc_index]
            corrected_doc = current_doc.model_copy(
                update={
                    "facts": {**current_doc.facts, **request.facts} if request.facts is not None else current_doc.facts,
                    "reference_number": request.reference_number
                    if request.reference_number is not None
                    else current_doc.reference_number,
                    "valid_from": request.valid_from if request.valid_from is not None else current_doc.valid_from,
                    "valid_to": request.valid_to if request.valid_to is not None else current_doc.valid_to,
                    "confirmed": True,
                    "confirmed_by": actor,
                    "confirmed_at": datetime.now(UTC),
                    "version": current_doc.version + 1,
                }
            )
            updated_documents = list(current.documents)
            updated_documents[doc_index] = corrected_doc
            updated = current.model_copy(update={"documents": updated_documents, "version": current.version + 1})
            self._snapshot.tickets[index] = updated
            self._idempotent_results[key] = deepcopy(updated)
            return deepcopy(updated)

    def confirm_package(
        self, ticket_id: str, request: PackageConfirmRequest, actor: str = "synthetic-staff"
    ) -> QueueTicket:
        with self._lock:
            key = ("package_confirm", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, QueueTicket):
                return deepcopy(existing)
            index = next(index for index, ticket in enumerate(self._snapshot.tickets) if ticket.id == ticket_id)
            current = self._snapshot.tickets[index]
            if current.version != request.expected_version:
                raise ValueError("The ticket changed since it was loaded. Refresh and try again.")
            if current.matched_package is None and request.corrected_package is None:
                raise KeyError(f"No matched package on file for {ticket_id}")
            updated = current.model_copy(
                update={
                    "matched_package": request.corrected_package or current.matched_package,
                    "package_confirmed": True,
                    "package_confirmed_by": actor,
                    "package_confirmed_at": datetime.now(UTC),
                    "version": current.version + 1,
                }
            )
            self._snapshot.tickets[index] = updated
            self._idempotent_results[key] = deepcopy(updated)
            return deepcopy(updated)

    def confirm_billing(
        self, ticket_id: str, request: BillingConfirmRequest, actor: str = "synthetic-staff"
    ) -> QueueTicket:
        with self._lock:
            key = ("billing_confirm", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, QueueTicket):
                return deepcopy(existing)
            index = next(index for index, ticket in enumerate(self._snapshot.tickets) if ticket.id == ticket_id)
            current = self._snapshot.tickets[index]
            if current.version != request.expected_version:
                raise ValueError("The ticket changed since it was loaded. Refresh and try again.")
            has_billing = current.billing_code is not None or current.uncovered_cost is not None
            has_correction = (
                request.corrected_billing_code is not None
                or request.corrected_uncovered_cost is not None
                or request.corrected_queue_number is not None
            )
            if not has_billing and not has_correction:
                raise KeyError(f"No billing/queue information on file for {ticket_id}")
            confirmed_at = datetime.now(UTC)
            updated = current.model_copy(
                update={
                    "billing_code": request.corrected_billing_code or current.billing_code,
                    "uncovered_cost": (
                        request.corrected_uncovered_cost
                        if request.corrected_uncovered_cost is not None
                        else current.uncovered_cost
                    ),
                    "queue_number": request.corrected_queue_number or current.queue_number,
                    "billing_confirmed": True,
                    "billing_confirmed_by": actor,
                    "billing_confirmed_at": confirmed_at,
                    "version": current.version + 1,
                }
            )
            self._snapshot.tickets[index] = updated
            self._idempotent_results[key] = deepcopy(updated)
            self._record_audit(
                actor=actor,
                action_type="payment_details_confirmed",
                target_table="queue_entries",
                target_id=updated.id,
                details={
                    "ticket_id": updated.id,
                    "payment": {
                        "mode": "synthetic_demo",
                        "status": "amount_due_confirmed",
                        "currency": "SGD",
                        "billing_code": updated.billing_code,
                        "amount_due": updated.uncovered_cost,
                        "queue_number": updated.queue_number,
                        "confirmed_at": confirmed_at.isoformat(),
                    },
                    "before": {
                        "billing_code": current.billing_code,
                        "amount_due": current.uncovered_cost,
                        "queue_number": current.queue_number,
                    },
                    "visit_times": self._visit_times(updated),
                    "version": updated.version,
                },
                occurred_at=confirmed_at,
            )
            return deepcopy(updated)

    def confirm_identity(
        self, ticket_id: str, request: IdentityConfirmRequest, actor: str = "synthetic-staff"
    ) -> QueueTicket:
        with self._lock:
            key = ("identity_confirm", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, QueueTicket):
                return deepcopy(existing)
            index = next(index for index, ticket in enumerate(self._snapshot.tickets) if ticket.id == ticket_id)
            current = self._snapshot.tickets[index]
            if current.version != request.expected_version:
                raise ValueError("The ticket changed since it was loaded. Refresh and try again.")
            updated = current.model_copy(
                update={
                    "identity_confirmed": True,
                    "identity_confirmed_by": actor,
                    "identity_confirmed_at": datetime.now(UTC),
                    "ecard_verified": not request.ecard_not_applicable,
                    "ecard_not_applicable": request.ecard_not_applicable,
                    "ecard_na_reason": request.ecard_na_reason if request.ecard_not_applicable else None,
                    "version": current.version + 1,
                }
            )
            self._snapshot.tickets[index] = updated
            self._idempotent_results[key] = deepcopy(updated)
            return deepcopy(updated)

    def confirm_forms(
        self, ticket_id: str, request: FormsConfirmRequest, actor: str = "synthetic-staff"
    ) -> QueueTicket:
        with self._lock:
            key = ("forms_confirm", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, QueueTicket):
                return deepcopy(existing)
            index = next(index for index, ticket in enumerate(self._snapshot.tickets) if ticket.id == ticket_id)
            current = self._snapshot.tickets[index]
            if current.version != request.expected_version:
                raise ValueError("The ticket changed since it was loaded. Refresh and try again.")
            unconfirmed_electronic = [
                doc for doc in current.documents if doc.category != DocumentCategory.FORM and not doc.confirmed
            ]
            if unconfirmed_electronic:
                raise ValueError("All electronic forms must be confirmed before approving.")
            updated = current.model_copy(
                update={
                    "forms_confirmed": True,
                    "forms_confirmed_by": actor,
                    "forms_confirmed_at": datetime.now(UTC),
                    "version": current.version + 1,
                }
            )
            self._snapshot.tickets[index] = updated
            self._idempotent_results[key] = deepcopy(updated)
            return deepcopy(updated)

    def mark_physical_forms_received(
        self, ticket_id: str, request: PhysicalFormsReceivedRequest, actor: str = "synthetic-staff"
    ) -> QueueTicket:
        with self._lock:
            key = ("physical_forms_received", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, QueueTicket):
                return deepcopy(existing)
            index = next(index for index, ticket in enumerate(self._snapshot.tickets) if ticket.id == ticket_id)
            current = self._snapshot.tickets[index]
            if current.version != request.expected_version:
                raise ValueError("The ticket changed since it was loaded. Refresh and try again.")
            updated = current.model_copy(
                update={
                    "physical_forms_received": True,
                    "physical_forms_received_by": actor,
                    "physical_forms_received_at": datetime.now(UTC),
                    "version": current.version + 1,
                }
            )
            self._snapshot.tickets[index] = updated
            self._idempotent_results[key] = deepcopy(updated)
            return deepcopy(updated)

    def record_medication_dispense(
        self, ticket_id: str, request: MedicationDispenseRequest, actor: str = "synthetic-pharmacist"
    ) -> MedicationDispense:
        with self._lock:
            key = ("medication_dispense", request.idempotency_key)
            existing = self._idempotent_results.get(key)
            if isinstance(existing, MedicationDispense):
                return deepcopy(existing)
            if not any(ticket.id == ticket_id for ticket in self._snapshot.tickets):
                raise KeyError(ticket_id)
            ticket = next(ticket for ticket in self._snapshot.tickets if ticket.id == ticket_id)
            total_cost = sum(item.quantity * item.unit_cost for item in request.items)
            dispensed_at = datetime.now(UTC)
            dispense = MedicationDispense(
                id=f"MED-{ticket_id}",
                ticket_id=ticket_id,
                items=list(request.items),
                total_cost=total_cost,
                dispensed_by=actor,
                dispensed_at=dispensed_at,
            )
            self._medication_dispenses[ticket_id] = dispense
            self._idempotent_results[key] = deepcopy(dispense)
            self._record_audit(
                actor=actor,
                action_type="medication_dispensed",
                target_table="medication_dispenses",
                target_id=dispense.id,
                details={
                    "ticket_id": ticket_id,
                    "medication": [item.model_dump(mode="json") for item in dispense.items],
                    "total_cost": dispense.total_cost,
                    "currency": "SGD",
                    "dispensed_at": dispensed_at.isoformat(),
                    "visit_times": self._visit_times(ticket),
                    "version": dispense.version,
                },
                occurred_at=dispensed_at,
            )
            return deepcopy(dispense)

    def draft_tpa_submission(self, ticket_id: str) -> TpaSubmission:
        with self._lock:
            ticket = next((ticket for ticket in self._snapshot.tickets if ticket.id == ticket_id), None)
            if ticket is None:
                raise KeyError(ticket_id)
            if not ticket.documents:
                raise KeyError(f"No documents on file for {ticket_id}")
            existing = self._tpa_submissions.get(ticket_id)
            if existing is not None and existing.status is TpaSubmissionStatus.SUBMITTED:
                return deepcopy(existing)
            checkup_summary = (
                f"{ticket.record_checklist.items[2].detail} · {ticket.processing_stage}"
                if ticket.record_checklist and len(ticket.record_checklist.items) > 2
                else ticket.processing_stage
            )
            draft = TpaSubmission(
                id=f"TPA-{ticket_id}",
                ticket_id=ticket_id,
                status=TpaSubmissionStatus.DRAFT,
                documents=ticket.documents,
                checkup_summary=checkup_summary,
                medication=self._medication_dispenses.get(ticket_id),
                version=existing.version if existing else 1,
            )
            self._tpa_submissions[ticket_id] = draft
            return deepcopy(draft)

    def confirm_tpa_submission(
        self, ticket_id: str, request: TpaSubmissionConfirmRequest, actor: str = "synthetic-pharmacist"
    ) -> TpaSubmission:
        with self._lock:
            key = ("tpa_submission_confirm", request.idempotency_key)
            existing_result = self._idempotent_results.get(key)
            if isinstance(existing_result, TpaSubmission):
                return deepcopy(existing_result)
            submission = self._tpa_submissions.get(ticket_id)
            if submission is None:
                raise KeyError(ticket_id)
            if submission.version != request.expected_version:
                raise ValueError("The submission changed since it was loaded. Refresh and try again.")
            external_reference = (
                "CLAIM-" + sha256(f"{ticket_id}:{request.idempotency_key}".encode()).hexdigest()[:10].upper()
            )
            updated = submission.model_copy(
                update={
                    "status": TpaSubmissionStatus.SUBMITTED,
                    "submitted_by": actor,
                    "submitted_at": datetime.now(UTC),
                    "external_reference": external_reference,
                    "version": submission.version + 1,
                }
            )
            self._tpa_submissions[ticket_id] = updated
            self._idempotent_results[key] = deepcopy(updated)
            ticket = next(ticket for ticket in self._snapshot.tickets if ticket.id == ticket_id)
            self._record_audit(
                actor=actor,
                action_type="tpa_submission_confirmed",
                target_table="tpa_submissions",
                target_id=updated.id,
                details={
                    "ticket_id": ticket_id,
                    "mode": "synthetic_demo",
                    "status": updated.status.value,
                    "external_reference": updated.external_reference,
                    "submitted_at": updated.submitted_at.isoformat() if updated.submitted_at else None,
                    "documents": [
                        {
                            "id": document.id,
                            "category": document.category.value,
                            "issuer_code": document.issuer_code,
                            "document_type": document.document_type,
                        }
                        for document in updated.documents
                    ],
                    "medication_dispense_id": updated.medication.id if updated.medication else None,
                    "visit_times": self._visit_times(ticket),
                    "version": updated.version,
                },
                occurred_at=updated.submitted_at,
            )
            return deepcopy(updated)

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
        with self._lock:
            records = self._audit_records
            if action_type:
                records = [record for record in records if record.action_type == action_type]
            if target_table:
                records = [record for record in records if record.target_table == target_table]
            if occurred_from:
                records = [record for record in records if record.occurred_at >= occurred_from]
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
                            str(record.details),
                        )
                    ).casefold()
                ]
            if actor:
                records = [record for record in records if actor.casefold() in record.actor_reference.casefold()]
            if actor_role:
                role = actor_role.casefold()
                records = [record for record in records if record.actor_role == role]
            if outcome:
                records = [
                    record
                    for record in records
                    if outcome.casefold()
                    in str(record.details.get("outcome") or record.details.get("status") or "committed").casefold()
                ]
            return deepcopy(records[offset : offset + limit])


demo_repository = DemoRepository()
