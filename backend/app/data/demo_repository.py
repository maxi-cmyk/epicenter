from copy import deepcopy
from datetime import UTC, date, datetime
from hashlib import sha256
from threading import RLock

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
    PatientSummary,
    PhysicalFormsReceivedRequest,
    PatientSubmissionOutcome,
    PatientUpdateRequest,
    PatientVisitHistory,
    PatientVisitRecord,
    PreArrivalSubmissionRequest,
    PreArrivalSubmissionResult,
    PriorCoverageSummary,
    QueueTicket,
    QuestionnaireSaveRequest,
    ReadinessState,
    RecommendationDecisionRequest,
    RecordChecklist,
    RegistrationValidationRequest,
    RegistrationValidationResult,
    ReviewCase,
    ServiceTarget,
    SimulatorSnapshot,
    SingpassProfileField,
    TicketTransitionRequest,
    TpaSubmission,
    TpaSubmissionConfirmRequest,
    TpaSubmissionStatus,
    UploadLinkSession,
    VisitPhase,
)
from app.services.questionnaire_catalog import (
    build_general_health_fields,
    build_general_health_prefill,
    missing_required_fields,
    singpass_dummy_fields,
)


def _at(hour: int, minute: int) -> datetime:
    return datetime(2026, 8, 12, hour, minute, tzinfo=UTC)


def _ticket_assignment(ticket: QueueTicket) -> tuple[str, str | None]:
    return ticket.queue_number or ticket.id, ticket.actual_room or ticket.expected_room


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
                readiness_state=ReadinessState.NEEDS_REVIEW,
                readiness_reason="ambiguous_match",
                scheduled_at=_at(10, 0),
                original_ordering_at=_at(10, 0),
                waiting_minutes=0,
                expected_room="S2",
                processing_stage="Insurance eligibility review",
                service_target=ServiceTarget.APPROACHING,
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
                    coverage_detail="Meridian (MRDEB) · referral letter",
                    eligibility_status=ChecklistStatus.PENDING,
                    eligibility_detail="WELL2 booked · Meridian referral on file",
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
                expected_room="S1",
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
                actual_room="S2",
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
                actual_room="S3",
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
                actual_room="S4",
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
                actual_room="S1",
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
                actual_room="F1",
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
                id="R-014",
                ticket_id="Q-014",
                patient_name="Loh Wei Ming",
                reason_code="ambiguous_match",
                reason_label="Insurance eligibility needs confirmation",
                document_name="Meridian_referral.pdf",
                evidence_summary="WELL2 booked · Meridian referral letter on file — cover does not match automatically",
                waiting_minutes=0,
                service_target=ServiceTarget.APPROACHING,
                next_action="Confirm insurer cover at the slow counter",
            ),
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
                "while S1 has been idle for 7 minutes."
            ),
            qualified_resource="S1 · Nur Aisyah",
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
        self._lock = RLock()
        self._snapshot = build_demo_snapshot()
        self._idempotent_results: dict[tuple[str, str], object] = {}
        self._patient_identifier_hashes = {
            1: "4e487c99807bebe1c81bf3cded10ceb92f1c8d3ed0d48cbe822ad578a45854b5"
        }
        self._patients = {
            1: PatientRecord(
                id=1,
                source_record_key="registration:0107",
                identifier_masked="*****946C",
                full_name="Loh Wei Ming",
                date_of_birth=date(1952, 7, 26),
                email="wei.loh43@hotmail.com",
                contact_mobile="92800206",
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
        self._onboarding_by_subject: dict[str, dict[str, object]] = {}
        self._journey = {
            "appointment_id": "APT-DEMO-014",
            "coverage_status": PatientCoverageStatus.CHECK_FIRST,
            "questionnaire_status": PatientQuestionnaireStatus.NOT_STARTED,
            "questionnaire_answers": {},
            "declaration_acknowledged": False,
            "questionnaire_version": 1,
            "outcome": None,
            "outcome_message": None,
            "force_upload": False,
            "notification": None,
            "payment_status": PatientPaymentStatus.NOT_READY,
            "payment_version": 1,
            "receipt_reference": None,
            "paid_at": None,
            "failure_reason": None,
        }

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
                outcome=PatientSubmissionOutcome.UNDER_REVIEW,
                message="Document received for staff review. This does not confirm eligibility or queue placement.",
                next_action="Complete the required questionnaire while staff confirm your coverage.",
            )
            self._journey["coverage_status"] = PatientCoverageStatus.SUBMITTED
            self._journey["outcome"] = PatientSubmissionOutcome.UNDER_REVIEW
            self._journey["outcome_message"] = result.message
            self._journey["force_upload"] = False
            self._journey["notification"] = None
            if self._journey["questionnaire_status"] == PatientQuestionnaireStatus.SUBMITTED:
                self._journey["outcome"] = PatientSubmissionOutcome.ACCEPTED
                self._journey["outcome_message"] = (
                    "Your pre-arrival steps are complete. Clinic staff will confirm the final result on arrival."
                )
                result = PreArrivalSubmissionResult(
                    processing_reference=result.processing_reference,
                    outcome=PatientSubmissionOutcome.ACCEPTED,
                    message=self._journey["outcome_message"],
                    next_action="You can check queue status after staff check-in.",
                )
            self._idempotent_results[key] = deepcopy(result)
            return result

    def submit_onboarding_coverage(
        self,
        *,
        file_name: str,
        actor: str = "synthetic-patient",
        patient_id: int | None = None,
        idempotency_key: str,
    ) -> PreArrivalSubmissionResult:
        key = ("onboarding_coverage", idempotency_key)
        with self._lock:
            existing = self._idempotent_results.get(key)
            if isinstance(existing, PreArrivalSubmissionResult):
                return deepcopy(existing)
            if not file_name.strip():
                raise ValueError("Choose a coverage document before submitting.")
            result = PreArrivalSubmissionResult(
                processing_reference=f"ONB-{sha256(idempotency_key.encode()).hexdigest()[:10].upper()}",
                outcome=PatientSubmissionOutcome.UNDER_REVIEW,
                message="Coverage was saved to your profile for staff review. No appointment is required yet.",
                next_action="Continue onboarding. You can book an appointment after these steps.",
            )
            self._journey["coverage_status"] = PatientCoverageStatus.SUBMITTED
            self._journey["outcome"] = PatientSubmissionOutcome.UNDER_REVIEW
            self._journey["outcome_message"] = result.message
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
            ticket = create_walk_in_ticket(
                f"Q-{highest + 1:03d}",
                request,
                occupied_counters=[
                    room
                    for existing in self._snapshot.tickets
                    for room in (existing.actual_room, existing.expected_room)
                    if room
                ],
            )
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

    def list_patients(
        self, *, search: str | None, offset: int, limit: int, contact_filter: str = "all", sort: str = "name"
    ) -> PatientList:
        with self._lock:
            records = [patient for patient in self._patients.values() if patient.deleted_at is None]
            if search:
                records = [patient for patient in records if search.casefold() in patient.full_name.casefold()]
            if contact_filter == "email":
                records = [patient for patient in records if patient.email]
            elif contact_filter == "mobile":
                records = [patient for patient in records if patient.contact_mobile]
            elif contact_filter == "complete":
                records = [patient for patient in records if patient.email and patient.contact_mobile]
            if sort == "reference":
                records.sort(key=lambda patient: patient.source_record_key)
            elif sort == "dob":
                records.sort(key=lambda patient: patient.date_of_birth or date.min, reverse=True)
            else:
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

    def _primary_action(self) -> tuple[PatientNextAction, str, str]:
        coverage = self._journey["coverage_status"]
        questionnaire = self._journey["questionnaire_status"]
        payment = self._journey["payment_status"]
        if self._journey["force_upload"] or coverage in {
            PatientCoverageStatus.CHECK_FIRST,
            PatientCoverageStatus.NOT_STARTED,
            PatientCoverageStatus.ACTION_REQUIRED,
        }:
            return (
                PatientNextAction.CONFIRM_COVERAGE,
                "Confirm coverage for this visit",
                "/coverage",
            )
        if questionnaire != PatientQuestionnaireStatus.SUBMITTED:
            return (
                PatientNextAction.COMPLETE_QUESTIONNAIRE,
                "Complete the required questionnaire",
                "/questionnaire",
            )
        if payment == PatientPaymentStatus.READY:
            return PatientNextAction.PAY, "Complete demo payment", "/payment"
        if payment == PatientPaymentStatus.MOCK_FAILED:
            return PatientNextAction.PAY, "Retry demo payment", "/payment"
        if self._journey["outcome"] == PatientSubmissionOutcome.UNDER_REVIEW:
            return PatientNextAction.WAIT_FOR_REVIEW, "See your current status", "/queue"
        return PatientNextAction.VIEW_QUEUE, "View queue status", "/queue"

    def get_patient_home(self, patient_id: int | None = None) -> PatientHome:
        with self._lock:
            patient = self._patients[1]
            action, label, href = self._primary_action()
            coverage = self._journey["coverage_status"]
            coverage_summary = {
                PatientCoverageStatus.CHECK_FIRST: "Prior Meridian coverage on file — confirm or replace",
                PatientCoverageStatus.NOT_STARTED: "Coverage document still needed",
                PatientCoverageStatus.ACTION_REQUIRED: "Please upload a clearer coverage document",
                PatientCoverageStatus.SUBMITTED: "Coverage received for staff confirmation",
            }[coverage]
            questionnaire = self._journey["questionnaire_status"]
            questionnaire_summary = {
                PatientQuestionnaireStatus.NOT_STARTED: "General health questionnaire not started",
                PatientQuestionnaireStatus.DRAFT: "Questionnaire draft saved — finish and submit",
                PatientQuestionnaireStatus.SUBMITTED: "Questionnaire submitted",
                PatientQuestionnaireStatus.NOT_REQUIRED: "No questionnaire required",
            }[questionnaire]
            payment = self._journey["payment_status"]
            payment_summary = {
                PatientPaymentStatus.NOT_READY: "Not ready — staff still finalising billing",
                PatientPaymentStatus.READY: "Demo payment ready",
                PatientPaymentStatus.MOCK_PROCESSING: "Demo payment processing",
                PatientPaymentStatus.MOCKED_PAID: "Demo payment recorded",
                PatientPaymentStatus.MOCK_FAILED: "Demo payment failed — retry available",
            }[payment]
            ticket = next(item for item in self._snapshot.tickets if item.id == "Q-014")
            queue_number, counter_label = _ticket_assignment(ticket)
            queue_summary = (
                f"{queue_number} · Counter {counter_label}" if counter_label else queue_number
            )
            return PatientHome(
                patient_display_name=patient.full_name,
                appointment=PatientAppointmentSummary(
                    appointment_id="APT-DEMO-014",
                    scheduled_at=_at(10, 0),
                    clinic_name="Parkway Shenton · HarbourFront",
                    location="HarbourFront clinic",
                    appointment_type="insurance_medical",
                    questionnaire_type="general_health",
                ),
                coverage_status=coverage,
                coverage_summary=coverage_summary,
                questionnaire_status=questionnaire,
                queue_summary=queue_summary,
                payment_status=payment,
                payment_summary=payment_summary,
                primary_action=action,
                primary_action_label=label,
                primary_action_href=href,
                outcome=self._journey["outcome"],
                outcome_message=self._journey["outcome_message"],
                notification=self._journey["notification"],
                recent_visit_summary="03 Feb 2026 · GP Consultation",
            )

    def get_prior_coverage(
        self,
        appointment_id: str,
        patient_id: int | None = None,
        *,
        first_visit: bool = False,
    ) -> PriorCoverageSummary:
        with self._lock:
            if appointment_id != self._journey["appointment_id"]:
                raise KeyError(appointment_id)
            if first_visit:
                return PriorCoverageSummary(
                    appointment_id=appointment_id,
                    has_prior_coverage=False,
                    issuer_name=None,
                    document_date=None,
                    prompt="No coverage is on file yet. Upload your insurance or medical coverage document for this visit.",
                    force_upload=True,
                )
            notification = self._journey["notification"]
            force_upload = bool(self._journey["force_upload"])
            if force_upload and notification is not None:
                return PriorCoverageSummary(
                    appointment_id=appointment_id,
                    has_prior_coverage=True,
                    issuer_name="Meridian",
                    document_date=date(2026, 2, 12),
                    prompt=notification.message,
                    force_upload=True,
                    notification=notification,
                )
            return PriorCoverageSummary(
                appointment_id=appointment_id,
                has_prior_coverage=True,
                issuer_name="Meridian",
                document_date=date(2026, 2, 12),
                prompt="We have your Meridian coverage on file from 12 February 2026. Still the same?",
                force_upload=False,
            )

    def get_patient_queue(self, patient_id: int | None = None) -> PatientQueueStatus:
        with self._lock:
            ticket = next(ticket for ticket in self._snapshot.tickets if ticket.id == "Q-014")
            queue_number, counter_label = _ticket_assignment(ticket)
            checked_in = ticket.checked_in_at is not None or ticket.visit_phase != VisitPhase.INCOMING
            if ticket.readiness_state == ReadinessState.NEEDS_REVIEW:
                detail = "A staff member is reviewing your registration."
                label = "Additional review needed"
            elif ticket.readiness_state == ReadinessState.PROCESSING:
                detail = "We are checking your registration details."
                label = "Processing"
            elif ticket.visit_phase == VisitPhase.FINISHED:
                detail = "Your visit is complete."
                label = "Finished"
            elif not checked_in:
                detail = "Your queue number and counter are ready. Keep this ticket for arrival."
                label = "Ticket reserved"
            else:
                detail = "Waiting to be called. Keep this ticket — you will not take another number."
                label = "Waiting"
            return PatientQueueStatus(
                available=True,
                ticket_id=ticket.id,
                visit_phase=ticket.visit_phase,
                status_label=label,
                status_detail=detail,
                queue_number=queue_number,
                counter_label=counter_label,
                patients_ahead=2 if ticket.visit_phase == VisitPhase.ONGOING else 0,
                updated_at=self._snapshot.generated_at,
                payment_ready=self._journey["payment_status"]
                in {PatientPaymentStatus.READY, PatientPaymentStatus.MOCKED_PAID, PatientPaymentStatus.MOCK_FAILED},
            )

    def get_patient_payment(self, patient_id: int | None = None) -> PatientPaymentSummary:
        with self._lock:
            status = self._journey["payment_status"]
            detail = {
                PatientPaymentStatus.NOT_READY: "Staff are still finalising billing for this visit.",
                PatientPaymentStatus.READY: "Demo payment is ready. No live gateway is used.",
                PatientPaymentStatus.MOCK_PROCESSING: "Recording the demo payment…",
                PatientPaymentStatus.MOCKED_PAID: "Demo payment recorded. Download remains local to this demo.",
                PatientPaymentStatus.MOCK_FAILED: self._journey["failure_reason"]
                or "The demo payment could not be recorded. Try again.",
            }[status]
            return PatientPaymentSummary(
                appointment_id=self._journey["appointment_id"],
                package_label="WELL2 — Comprehensive Screen",
                amount_covered="$180.00",
                amount_patient_payable="$35.00",
                status=status,
                status_detail=detail,
                receipt_reference=self._journey["receipt_reference"],
                paid_at=self._journey["paid_at"],
                failure_reason=self._journey["failure_reason"],
                version=self._journey["payment_version"],
            )

    def submit_mock_payment(
        self, request: MockPaymentRequest, actor: str = "synthetic-patient", patient_id: int | None = None
    ) -> PatientPaymentSummary:
        key = ("mock_payment", request.idempotency_key)
        with self._lock:
            existing = self._idempotent_results.get(key)
            if isinstance(existing, PatientPaymentSummary):
                return deepcopy(existing)
            if request.appointment_id != self._journey["appointment_id"]:
                raise KeyError(request.appointment_id)
            if self._journey["payment_version"] != request.expected_version:
                raise ValueError("The payment record changed since it was loaded. Refresh and try again.")
            if self._journey["payment_status"] == PatientPaymentStatus.MOCKED_PAID:
                return self.get_patient_payment(patient_id)
            if self._journey["payment_status"] == PatientPaymentStatus.NOT_READY:
                raise ValueError("Payment is not ready yet.")
            # Deterministic demo: keys ending in "fail" simulate gateway failure.
            if request.idempotency_key.lower().endswith("fail"):
                self._journey["payment_status"] = PatientPaymentStatus.MOCK_FAILED
                self._journey["failure_reason"] = "Demo payment provider returned a recoverable failure."
                self._journey["receipt_reference"] = None
                self._journey["paid_at"] = None
            else:
                self._journey["payment_status"] = PatientPaymentStatus.MOCKED_PAID
                self._journey["failure_reason"] = None
                self._journey["receipt_reference"] = (
                    f"MOCK-{sha256(request.idempotency_key.encode()).hexdigest()[:10].upper()}"
                )
                self._journey["paid_at"] = datetime.now(UTC)
            self._journey["payment_version"] += 1
            result = self.get_patient_payment(patient_id)
            self._idempotent_results[key] = deepcopy(result)
            return result

    def get_patient_records(self, patient_id: int | None = None) -> PatientVisitHistory:
        with self._lock:
            return PatientVisitHistory(
                visits=[
                    PatientVisitRecord(
                        appointment_id="APT-DEMO-014",
                        visited_on=date(2026, 8, 12),
                        visit_label="Health Screening",
                        package_label="WELL2 — Comprehensive Screen",
                        coverage_label="Meridian",
                        questionnaire_summary=(
                            "General health · Submitted"
                            if self._journey["questionnaire_status"] == PatientQuestionnaireStatus.SUBMITTED
                            else "General health · Pending"
                        ),
                        outcome=self._journey["outcome"],
                    ),
                    PatientVisitRecord(
                        appointment_id="APT-HISTORY-001",
                        visited_on=date(2026, 2, 3),
                        visit_label="GP Consultation",
                        package_label=None,
                        coverage_label="Meridian",
                        questionnaire_summary="General health · Submitted 03 Feb",
                        outcome=PatientSubmissionOutcome.ACCEPTED,
                    ),
                ]
            )

    def get_patient_questionnaire(
        self, appointment_id: str, patient_id: int | None = None
    ) -> PatientQuestionnaire:
        with self._lock:
            if appointment_id != self._journey["appointment_id"]:
                raise KeyError(appointment_id)
            answers = self._journey["questionnaire_answers"]
            if "gender" not in answers:
                answers = {
                    **answers,
                    "gender": next(
                        (item["value"] for item in singpass_dummy_fields() if item["field_id"] == "sex"),
                        "Male",
                    ),
                }
            return PatientQuestionnaire(
                appointment_id=appointment_id,
                questionnaire_type="general_health",
                title="General Health Screening Questionnaire",
                status=self._journey["questionnaire_status"],
                prefill=build_general_health_prefill(),
                fields=build_general_health_fields(answers),
                declaration_acknowledged=bool(self._journey["declaration_acknowledged"]),
                version=self._journey["questionnaire_version"],
            )

    def save_patient_questionnaire(
        self,
        request: QuestionnaireSaveRequest,
        actor: str = "synthetic-patient",
        patient_id: int | None = None,
    ) -> PatientQuestionnaire:
        key = ("questionnaire", request.idempotency_key)
        with self._lock:
            existing = self._idempotent_results.get(key)
            if isinstance(existing, PatientQuestionnaire):
                return deepcopy(existing)
            if request.appointment_id != self._journey["appointment_id"]:
                raise KeyError(request.appointment_id)
            if self._journey["questionnaire_version"] != request.expected_version:
                raise ValueError("The questionnaire changed since it was loaded. Refresh and try again.")
            self._journey["questionnaire_answers"] = {
                field_id: value for field_id, value in request.answers.items() if value is not None
            }
            self._journey["declaration_acknowledged"] = request.declaration_acknowledged
            if request.submit:
                fields = build_general_health_fields(self._journey["questionnaire_answers"])
                missing = missing_required_fields(fields, self._journey["questionnaire_answers"])
                if missing or not request.declaration_acknowledged:
                    raise ValueError("Complete the required visible answers and declaration before submitting.")
                self._journey["questionnaire_status"] = PatientQuestionnaireStatus.SUBMITTED
                if self._journey["coverage_status"] == PatientCoverageStatus.SUBMITTED:
                    self._journey["outcome"] = PatientSubmissionOutcome.ACCEPTED
                    self._journey["outcome_message"] = (
                        "Your pre-arrival steps are complete. Clinic staff will confirm the final result on arrival."
                    )
                    self._journey["payment_status"] = PatientPaymentStatus.READY
            else:
                self._journey["questionnaire_status"] = PatientQuestionnaireStatus.DRAFT
            self._journey["questionnaire_version"] += 1
            result = self.get_patient_questionnaire(request.appointment_id, patient_id)
            self._idempotent_results[key] = deepcopy(result)
            return result

    def _onboarding_state(self, subject: str) -> dict[str, object]:
        existing = self._onboarding_by_subject.get(subject)
        if existing is None:
            existing = {
                "completed": False,
                "current_step": OnboardingStep.SINGPASS,
                "singpass_authenticated": False,
                "insurance_completed": False,
                "questionnaire_completed": False,
            }
            self._onboarding_by_subject[subject] = existing
        return existing

    def get_onboarding_state(self, subject: str, patient_id: int | None = None) -> PatientOnboardingState:
        with self._lock:
            state = self._onboarding_state(subject)
            completed = bool(state["completed"])
            return PatientOnboardingState(
                completed=completed,
                current_step=OnboardingStep(str(state["current_step"])),
                appointment_id=str(self._journey["appointment_id"]),
                singpass_authenticated=bool(state["singpass_authenticated"]),
                singpass_fields=[
                    SingpassProfileField(
                        field_id=item["field_id"],
                        label=item["label"],
                        value=item["value"] if state["singpass_authenticated"] else "",
                    )
                    for item in singpass_dummy_fields()
                ],
                insurance_completed=bool(state["insurance_completed"]),
                questionnaire_completed=bool(state["questionnaire_completed"]),
                next_href="/" if completed else "/onboarding",
            )

    def advance_onboarding(
        self,
        request: OnboardingAdvanceRequest,
        subject: str,
        patient_id: int | None = None,
    ) -> PatientOnboardingState:
        key = ("onboarding_advance", request.idempotency_key)
        with self._lock:
            existing = self._idempotent_results.get(key)
            if isinstance(existing, PatientOnboardingState):
                return deepcopy(existing)
            state = self._onboarding_state(subject)
            was_singpass_authenticated = bool(state["singpass_authenticated"])
            was_insurance_completed = bool(state["insurance_completed"])
            was_questionnaire_completed = bool(state["questionnaire_completed"])
            if request.singpass_authenticated is not None:
                state["singpass_authenticated"] = request.singpass_authenticated
            if request.insurance_completed is not None:
                state["insurance_completed"] = request.insurance_completed
                if request.insurance_completed:
                    self._journey["coverage_status"] = PatientCoverageStatus.SUBMITTED
                    self._journey["outcome"] = PatientSubmissionOutcome.UNDER_REVIEW
                    self._journey["outcome_message"] = (
                        "Coverage details received for staff review during onboarding."
                    )
            if request.questionnaire_completed is not None:
                state["questionnaire_completed"] = request.questionnaire_completed
                if request.questionnaire_completed:
                    self._journey["questionnaire_status"] = PatientQuestionnaireStatus.SUBMITTED

            if request.step is OnboardingStep.SINGPASS:
                if not state["singpass_authenticated"]:
                    raise ValueError("Authenticate the synthetic Singpass profile before continuing.")
                # First click autofills; second confirm advances.
                if was_singpass_authenticated:
                    state["current_step"] = OnboardingStep.INSURANCE
            elif request.step is OnboardingStep.INSURANCE:
                if not state["insurance_completed"]:
                    raise ValueError("Confirm or upload coverage before continuing.")
                if was_insurance_completed or request.insurance_completed:
                    state["current_step"] = OnboardingStep.QUESTIONNAIRE
            elif request.step is OnboardingStep.QUESTIONNAIRE:
                if not state["questionnaire_completed"]:
                    raise ValueError("Submit the required questionnaire before finishing onboarding.")
                if was_questionnaire_completed or request.questionnaire_completed:
                    state["current_step"] = OnboardingStep.COMPLETE
                    state["completed"] = True
                    self._journey["outcome"] = PatientSubmissionOutcome.ACCEPTED
                    self._journey["outcome_message"] = (
                        "Onboarding complete. Clinic staff will confirm your record on arrival."
                    )
                    self._journey["payment_status"] = PatientPaymentStatus.READY
            elif request.step is OnboardingStep.COMPLETE:
                if not (
                    state["singpass_authenticated"]
                    and state["insurance_completed"]
                    and state["questionnaire_completed"]
                ):
                    raise ValueError("Finish Singpass, insurance, and questionnaire before completing onboarding.")
                state["completed"] = True
                state["current_step"] = OnboardingStep.COMPLETE

            result = self.get_onboarding_state(subject, patient_id)
            self._idempotent_results[key] = deepcopy(result)
            return result

    def resolve_upload_link(self, token: str) -> UploadLinkSession:
        normalized = token.strip().lower()
        with self._lock:
            if normalized in {"expired", "used", "invalid"}:
                return UploadLinkSession(
                    valid=False,
                    message="This upload link is no longer valid.",
                    next_action="Contact the clinic for a new appointment link.",
                )
            if normalized in {"demo", "apt-demo-014", "valid"}:
                return UploadLinkSession(
                    valid=True,
                    appointment_id="APT-DEMO-014",
                    scheduled_at=_at(10, 0),
                    message="This link is scoped to one appointment upload only.",
                    next_action="Confirm prior coverage or upload a replacement document.",
                )
            return UploadLinkSession(
                valid=False,
                message="This upload link is no longer valid.",
                next_action="Contact the clinic for a new appointment link.",
            )


demo_repository = DemoRepository()
