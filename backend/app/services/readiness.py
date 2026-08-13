from copy import deepcopy

from app.domain.models import QueueTicket, ReadinessState, TicketTransitionRequest


class InvalidTransition(ValueError):
    pass


def transition_ticket(ticket: QueueTicket, request: TicketTransitionRequest) -> QueueTicket:
    if request.expected_version != ticket.version:
        raise InvalidTransition("The ticket changed since it was loaded. Refresh and try again.")
    if request.readiness_state is ReadinessState.READY and not request.staff_confirmed:
        raise InvalidTransition("A ticket cannot become ready without staff confirmation.")

    updated = deepcopy(ticket)
    updated.readiness_state = request.readiness_state
    updated.readiness_reason = request.reason
    updated.staff_confirmed = request.staff_confirmed

    if request.readiness_state is ReadinessState.READY:
        updated.processing_stage = "Waiting to be called"
    elif request.readiness_state is ReadinessState.NEEDS_REVIEW:
        updated.processing_stage = "Assisted review"
    else:
        updated.processing_stage = "First-pass processing"

    if request.visit_phase is not None:
        updated.visit_phase = request.visit_phase

    # The ticket ID and original ordering time are deliberately untouched.
    return updated
