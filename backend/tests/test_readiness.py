from datetime import UTC, datetime

import pytest

from app.domain.models import IntakeType, QueueTicket, ReadinessState, TicketTransitionRequest, VisitPhase
from app.services.readiness import InvalidTransition, transition_ticket


def sample_ticket() -> QueueTicket:
    checked_in = datetime(2026, 8, 12, 9, 30, tzinfo=UTC)
    return QueueTicket(
        id="Q-100",
        patient_id="P-100",
        patient_name="Test Patient",
        intake_type=IntakeType.WALK_IN,
        visit_phase=VisitPhase.ONGOING,
        readiness_state=ReadinessState.PROCESSING,
        readiness_reason="processing",
        checked_in_at=checked_in,
        original_ordering_at=checked_in,
        waiting_minutes=4,
        processing_stage="Document extraction",
    )


def test_ready_requires_staff_confirmation() -> None:
    with pytest.raises(InvalidTransition):
        transition_ticket(
            sample_ticket(),
            TicketTransitionRequest(readiness_state=ReadinessState.READY, reason="all_prerequisites_passed"),
        )


def test_transition_preserves_ticket_and_original_waiting_time() -> None:
    ticket = sample_ticket()
    updated = transition_ticket(
        ticket, TicketTransitionRequest(readiness_state=ReadinessState.NEEDS_REVIEW, reason="ambiguous_match")
    )
    assert updated.id == ticket.id
    assert updated.original_ordering_at == ticket.original_ordering_at
    assert updated.waiting_minutes == ticket.waiting_minutes
