import logging
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import StaffPrincipal, require_reverified_staff, require_staff
from app.data.dependencies import get_operations_repository
from app.data.operations_repository import OperationsRepository
from app.data.supabase_client import SupabaseDataError
from app.domain.models import (
    ActionResult,
    AuditRecord,
    CounterAssignmentRequest,
    DashboardSnapshot,
    DocumentProcessingRequest,
    KioskCheckInRequest,
    PatientCreateRequest,
    PatientDeleteRequest,
    PatientList,
    PatientRecord,
    PatientUpdateRequest,
    RecommendationDecisionRequest,
    SimulatorSnapshot,
    StaffSession,
    TicketTransitionRequest,
)
from app.services.allocation import InvalidDecision, normalize_decision
from app.services.readiness import InvalidTransition

router = APIRouter()
logger = logging.getLogger(__name__)

Repository = Annotated[OperationsRepository, Depends(get_operations_repository)]
Principal = Annotated[StaffPrincipal, Depends(require_staff)]
ReverifiedPrincipal = Annotated[StaffPrincipal, Depends(require_reverified_staff)]


def _require_roles(principal: StaffPrincipal, *allowed_roles: str) -> None:
    if principal.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff role is not permitted for this action.",
        )


def _raise_repository_error(exc: SupabaseDataError) -> NoReturn:
    if exc.code in {"P0002", "PT404"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found") from exc
    if exc.code in {"PT409", "40001", "23514"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if exc.code in {"22023", "PT422"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    logger.error("Supabase persistence error: code=%s status=%s", exc.code, exc.status_code)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Persistence service unavailable",
    ) from exc


@router.get("/dashboard", response_model=DashboardSnapshot)
def get_dashboard(repository: Repository, principal: Principal) -> DashboardSnapshot:
    try:
        return repository.snapshot()
    except (SupabaseDataError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase operational schema and seed are not ready.",
        ) from exc


@router.get("/staff/session", response_model=StaffSession)
def get_staff_session(principal: Principal) -> StaffSession:
    return StaffSession(role=principal.role, clinic_id=principal.clinic_id)


@router.get("/simulator/snapshots", response_model=list[SimulatorSnapshot])
def get_simulator_snapshots(repository: Repository, principal: Principal) -> list[SimulatorSnapshot]:
    _require_roles(principal, "operations_admin", "auditor")
    try:
        return repository.list_simulator_snapshots()
    except SupabaseDataError as exc:
        _raise_repository_error(exc)


@router.post("/tickets/{ticket_id}/document-result", response_model=ActionResult)
def process_document(
    ticket_id: str,
    request: DocumentProcessingRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "registration", "operations_admin")
    try:
        ticket = repository.process_document(ticket_id, request, principal.subject)
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return ActionResult(success=True, message="Document result committed with its audit evidence.", ticket=ticket)


@router.post("/tickets/{ticket_id}/counter", response_model=ActionResult)
def assign_counter(
    ticket_id: str,
    request: CounterAssignmentRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "registration", "operations_admin")
    try:
        ticket = repository.assign_counter(ticket_id, request, principal.subject)
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return ActionResult(
        success=True,
        message="Counter assignment committed without replacing the ticket.",
        ticket=ticket,
    )


@router.post("/tickets/{ticket_id}/transition", response_model=ActionResult)
def update_ticket(
    ticket_id: str,
    request: TicketTransitionRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "registration", "operations_admin")
    try:
        saved = repository.transition_ticket(ticket_id, request, principal.subject)
    except (InvalidTransition, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found") from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return ActionResult(success=True, message=f"{ticket_id} updated without changing its queue identity.", ticket=saved)


@router.post("/kiosk/check-in", response_model=ActionResult, status_code=status.HTTP_201_CREATED)
def kiosk_check_in(
    request: KioskCheckInRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "registration", "operations_admin")
    try:
        saved = repository.add_walk_in(request, principal.subject)
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    message = (
        "Clinical escalation recorded; follow the clinic urgent-care pathway."
        if saved.clinical_escalation
        else "Walk-in registered on one persistent ticket."
    )
    return ActionResult(success=True, message=message, ticket=saved)


@router.post("/recommendations/{recommendation_id}/decision", response_model=ActionResult)
def decide_recommendation(
    recommendation_id: str,
    request: RecommendationDecisionRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "operations_admin")
    try:
        decision = normalize_decision(request)
    except InvalidDecision as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    request.decision = decision
    try:
        recommendation = repository.decide_recommendation(recommendation_id, request, principal.subject)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return ActionResult(
        success=True,
        message=f"Recommendation {decision}; no change was applied silently.",
        recommendation=recommendation,
    )


@router.get("/patients", response_model=PatientList)
def list_patients(
    repository: Repository,
    principal: Principal,
    search: str | None = Query(default=None, max_length=80),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
) -> PatientList:
    _require_roles(principal, "registration", "operations_admin", "auditor")
    try:
        return repository.list_patients(search=search, offset=offset, limit=limit)
    except SupabaseDataError as exc:
        _raise_repository_error(exc)


@router.get("/patients/{patient_id}", response_model=PatientRecord)
def get_patient(patient_id: int, repository: Repository, principal: Principal) -> PatientRecord:
    _require_roles(principal, "registration", "operations_admin", "auditor")
    try:
        patient = repository.get_patient(patient_id)
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.post("/patients", response_model=PatientRecord, status_code=status.HTTP_201_CREATED)
def create_patient(
    request: PatientCreateRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> PatientRecord:
    _require_roles(principal, "registration", "operations_admin")
    try:
        return repository.create_patient(request, principal.subject)
    except SupabaseDataError as exc:
        _raise_repository_error(exc)


@router.patch("/patients/{patient_id}", response_model=PatientRecord)
def update_patient(
    patient_id: int,
    request: PatientUpdateRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> PatientRecord:
    _require_roles(principal, "registration", "operations_admin")
    try:
        return repository.update_patient(patient_id, request, principal.subject)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)


@router.delete("/patients/{patient_id}", response_model=PatientRecord)
def delete_patient(
    patient_id: int,
    request: PatientDeleteRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> PatientRecord:
    _require_roles(principal, "registration", "operations_admin")
    try:
        return repository.delete_patient(patient_id, request, principal.subject)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)


@router.get("/audit", response_model=list[AuditRecord])
def list_audit(
    repository: Repository,
    principal: Principal,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[AuditRecord]:
    _require_roles(principal, "operations_admin", "auditor")
    try:
        return repository.list_audit(limit=limit)
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
