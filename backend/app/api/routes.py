from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import require_staff
from app.data.demo_repository import demo_repository
from app.domain.models import (
    ActionResult,
    DashboardSnapshot,
    KioskCheckInRequest,
    RecommendationDecisionRequest,
    TicketTransitionRequest,
)
from app.services.allocation import InvalidDecision, normalize_decision
from app.services.kiosk import create_walk_in_ticket
from app.services.readiness import InvalidTransition, transition_ticket

router = APIRouter(dependencies=[Depends(require_staff)])


@router.get("/dashboard", response_model=DashboardSnapshot)
def get_dashboard() -> DashboardSnapshot:
    return demo_repository.snapshot()


@router.post("/tickets/{ticket_id}/transition", response_model=ActionResult)
def update_ticket(ticket_id: str, request: TicketTransitionRequest) -> ActionResult:
    ticket = demo_repository.find_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    try:
        updated = transition_ticket(ticket, request)
    except InvalidTransition as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    saved = demo_repository.save_ticket(updated)
    return ActionResult(success=True, message=f"{ticket_id} updated without changing its queue identity.", ticket=saved)


@router.post("/kiosk/check-in", response_model=ActionResult, status_code=status.HTTP_201_CREATED)
def kiosk_check_in(request: KioskCheckInRequest) -> ActionResult:
    ticket = create_walk_in_ticket(demo_repository.next_ticket_id(), request)
    saved = demo_repository.add_ticket(ticket)
    message = (
        "Clinical escalation recorded; follow the clinic urgent-care pathway."
        if saved.clinical_escalation
        else "Walk-in registered on one persistent ticket."
    )
    return ActionResult(success=True, message=message, ticket=saved)


@router.post("/recommendations/{recommendation_id}/decision", response_model=ActionResult)
def decide_recommendation(recommendation_id: str, request: RecommendationDecisionRequest) -> ActionResult:
    current = demo_repository.snapshot().recommendation
    if current.id != recommendation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    try:
        decision = normalize_decision(request)
    except InvalidDecision as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    recommendation = demo_repository.decide_recommendation(decision)
    return ActionResult(
        success=True,
        message=f"Recommendation {decision}; no change was applied silently.",
        recommendation=recommendation,
    )
