from copy import deepcopy
from datetime import UTC, datetime
from threading import Lock

from app.domain.models import (
    ActivityEvent,
    AllocationRecommendation,
    DashboardSnapshot,
    IntakeType,
    Metric,
    QueueTicket,
    ReadinessState,
    ReviewCase,
    ServiceTarget,
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

    def snapshot(self) -> DashboardSnapshot:
        with self._lock:
            return deepcopy(self._snapshot)

    def find_ticket(self, ticket_id: str) -> QueueTicket | None:
        with self._lock:
            return next((ticket for ticket in self._snapshot.tickets if ticket.id == ticket_id), None)

    def save_ticket(self, updated: QueueTicket) -> QueueTicket:
        with self._lock:
            index = next(index for index, ticket in enumerate(self._snapshot.tickets) if ticket.id == updated.id)
            self._snapshot.tickets[index] = updated
            self._snapshot.generated_at = datetime.now(UTC)
            return deepcopy(updated)

    def add_ticket(self, ticket: QueueTicket) -> QueueTicket:
        with self._lock:
            self._snapshot.tickets.insert(0, ticket)
            self._snapshot.generated_at = datetime.now(UTC)
            return deepcopy(ticket)

    def decide_recommendation(self, status: str) -> AllocationRecommendation:
        with self._lock:
            self._snapshot.recommendation.status = status
            self._snapshot.generated_at = datetime.now(UTC)
            return deepcopy(self._snapshot.recommendation)

    def next_ticket_id(self) -> str:
        with self._lock:
            highest = max(int(ticket.id.removeprefix("Q-")) for ticket in self._snapshot.tickets)
            return f"Q-{highest + 1:03d}"


demo_repository = DemoRepository()
