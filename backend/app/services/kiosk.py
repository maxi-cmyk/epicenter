from datetime import UTC, datetime

from app.domain.models import IntakeType, KioskCheckInRequest, QueueTicket, ReadinessState, VisitPhase

FAST_COUNTERS = ("F1", "F2")
SLOW_COUNTERS = ("S1", "S2", "S3", "S4")


def next_registration_counter(lane: str, occupied: list[str] | None = None) -> str:
    pool = FAST_COUNTERS if lane == "fast" else SLOW_COUNTERS
    held = occupied or []
    return min(pool, key=lambda counter: (held.count(counter), counter))


def create_walk_in_ticket(
    ticket_id: str, request: KioskCheckInRequest, occupied_counters: list[str] | None = None
) -> QueueTicket:
    now = datetime.now(UTC)
    return QueueTicket(
        id=ticket_id,
        patient_id=f"P-{ticket_id.removeprefix('Q-')}",
        patient_name=request.patient_name,
        intake_type=IntakeType.WALK_IN,
        visit_phase=VisitPhase.ONGOING,
        readiness_state=ReadinessState.PROCESSING,
        readiness_reason="processing",
        checked_in_at=now,
        original_ordering_at=now,
        waiting_minutes=0,
        actual_room=next_registration_counter("slow", occupied_counters),
        processing_stage="Nurse-supervised registration",
        queue_number=ticket_id,
        clinical_escalation=request.clinical_escalation,
        is_checkup=request.is_checkup,
    )
