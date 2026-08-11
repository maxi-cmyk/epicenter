from datetime import UTC, datetime

from app.domain.models import IntakeType, KioskCheckInRequest, QueueTicket, ReadinessState, VisitPhase


def create_walk_in_ticket(ticket_id: str, request: KioskCheckInRequest) -> QueueTicket:
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
        actual_counter="Kiosk intake",
        processing_stage="Nurse-supervised registration",
        clinical_escalation=request.clinical_escalation,
    )
