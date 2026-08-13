import logging
from datetime import datetime
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.auth import StaffPrincipal, require_reverified_staff, require_staff
from app.data.dependencies import get_operations_repository
from app.data.operations_repository import OperationsRepository
from app.data.supabase_client import SupabaseDataError
from app.domain.models import (
    ActionResult,
    AuditRecord,
    BillingConfirmRequest,
    DashboardSnapshot,
    DocumentConfirmRequest,
    DocumentProcessingRequest,
    FormsConfirmRequest,
    IdentityConfirmRequest,
    KioskCheckInRequest,
    MedicationDispenseRequest,
    PackageConfirmRequest,
    PatientCreateRequest,
    PatientDeleteRequest,
    PatientList,
    PatientRecord,
    PatientUpdateRequest,
    PhysicalFormsReceivedRequest,
    QueueTicket,
    RecommendationDecisionRequest,
    SimulatorSnapshot,
    StaffSession,
    TicketTransitionRequest,
    TpaSubmission,
    TpaSubmissionConfirmRequest,
)
from app.services.allocation import InvalidDecision, normalize_decision
from app.services.readiness import InvalidTransition

router = APIRouter()
logger = logging.getLogger(__name__)

Repository = Annotated[OperationsRepository, Depends(get_operations_repository)]
Principal = Annotated[StaffPrincipal, Depends(require_staff)]
ReverifiedPrincipal = Annotated[StaffPrincipal, Depends(require_reverified_staff)]

_AUDIT_REDACTED_KEYS = {
    "access_token",
    "contact_mobile",
    "email",
    "identifier_hash",
    "nric",
    "passport",
    "provider_id",
    "provider_identifier",
    "raw_document_text",
    "refresh_token",
    "secret",
    "token",
}


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


def _safe_audit_record(record: AuditRecord) -> AuditRecord:
    def redact(value: object) -> object:
        if isinstance(value, dict):
            return {
                str(key): redact(item) for key, item in value.items() if str(key).casefold() not in _AUDIT_REDACTED_KEYS
            }
        if isinstance(value, list):
            return [redact(item) for item in value]
        return value

    details = redact(record.details)
    assert isinstance(details, dict)
    return record.model_copy(update={"details": details}, deep=True)


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


@router.post("/tickets/{ticket_id}/documents/{document_id}/confirm", response_model=ActionResult)
def confirm_document(
    ticket_id: str,
    document_id: str,
    request: DocumentConfirmRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "registration", "operations_admin")
    try:
        ticket = repository.confirm_document(ticket_id, document_id, request, principal.subject)
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc) or "Ticket not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return ActionResult(success=True, message="Document confirmed by staff.", ticket=ticket)


@router.post("/tickets/{ticket_id}/package/confirm", response_model=ActionResult)
def confirm_package(
    ticket_id: str,
    request: PackageConfirmRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "registration", "operations_admin")
    try:
        ticket = repository.confirm_package(ticket_id, request, principal.subject)
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc) or "Ticket not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return ActionResult(success=True, message="Package rechecked and confirmed by staff.", ticket=ticket)


@router.post("/tickets/{ticket_id}/billing/confirm", response_model=ActionResult)
def confirm_billing(
    ticket_id: str,
    request: BillingConfirmRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "registration", "operations_admin")
    try:
        ticket = repository.confirm_billing(ticket_id, request, principal.subject)
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc) or "Ticket not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return ActionResult(
        success=True,
        message="Billing and queue number rechecked and confirmed by staff.",
        ticket=ticket,
    )


@router.post("/tickets/{ticket_id}/identity/confirm", response_model=ActionResult)
def confirm_identity(
    ticket_id: str,
    request: IdentityConfirmRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "registration", "operations_admin")
    try:
        ticket = repository.confirm_identity(ticket_id, request, principal.subject)
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc) or "Ticket not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return ActionResult(success=True, message="Identity and e-card verification confirmed by staff.", ticket=ticket)


@router.post("/tickets/{ticket_id}/forms/confirm", response_model=ActionResult)
def confirm_forms(
    ticket_id: str,
    request: FormsConfirmRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "registration", "operations_admin")
    try:
        ticket = repository.confirm_forms(ticket_id, request, principal.subject)
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc) or "Ticket not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return ActionResult(success=True, message="Electronic forms confirmed by staff.", ticket=ticket)


@router.post("/tickets/{ticket_id}/physical-forms/received", response_model=ActionResult)
def mark_physical_forms_received(
    ticket_id: str,
    request: PhysicalFormsReceivedRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "registration", "operations_admin")
    try:
        ticket = repository.mark_physical_forms_received(ticket_id, request, principal.subject)
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc) or "Ticket not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return ActionResult(success=True, message="Physical forms received from patient.", ticket=ticket)


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


@router.get("/pharmacy/queue", response_model=list[QueueTicket])
def get_pharmacy_queue(repository: Repository, principal: Principal) -> list[QueueTicket]:
    _require_roles(principal, "pharmacist", "operations_admin")
    try:
        snapshot = repository.snapshot()
    except (SupabaseDataError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase operational schema and seed are not ready.",
        ) from exc
    return [ticket for ticket in snapshot.tickets if ticket.visit_phase in ("ongoing", "finished")]


@router.post("/tickets/{ticket_id}/medication", response_model=ActionResult, status_code=status.HTTP_201_CREATED)
def record_medication_dispense(
    ticket_id: str,
    request: MedicationDispenseRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "pharmacist", "operations_admin")
    try:
        dispense = repository.record_medication_dispense(ticket_id, request, principal.subject)
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found") from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return ActionResult(success=True, message="Medication dispense recorded.", medication=dispense)


@router.get("/tickets/{ticket_id}/tpa-submission", response_model=TpaSubmission)
def get_tpa_submission(
    ticket_id: str,
    repository: Repository,
    principal: Principal,
) -> TpaSubmission:
    _require_roles(principal, "pharmacist", "operations_admin")
    try:
        submission = repository.draft_tpa_submission(ticket_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return submission


@router.post("/tickets/{ticket_id}/tpa-submission/confirm", response_model=ActionResult)
def confirm_tpa_submission(
    ticket_id: str,
    request: TpaSubmissionConfirmRequest,
    repository: Repository,
    principal: ReverifiedPrincipal,
) -> ActionResult:
    _require_roles(principal, "pharmacist", "operations_admin")
    try:
        submission = repository.confirm_tpa_submission(ticket_id, request, principal.subject)
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
    return ActionResult(
        success=True,
        message="TPA submission confirmed and marked processed.",
        tpa_submission=submission,
    )


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
    contact_filter: str = Query(default="all", pattern="^(all|email|mobile|complete)$"),
    sort: str = Query(default="name", pattern="^(name|reference|dob)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
) -> PatientList:
    _require_roles(principal, "registration", "pharmacist", "operations_admin", "auditor")
    try:
        return repository.list_patients(
            search=search, contact_filter=contact_filter, sort=sort, offset=offset, limit=limit
        )
    except SupabaseDataError as exc:
        _raise_repository_error(exc)


@router.get("/patients/{patient_id}", response_model=PatientRecord)
def get_patient(patient_id: int, repository: Repository, principal: Principal) -> PatientRecord:
    _require_roles(principal, "registration", "pharmacist", "operations_admin", "auditor")
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
    principal: Principal,
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
    response: Response,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=10_000),
    search: str | None = Query(default=None, min_length=1, max_length=120),
    actor: str | None = Query(default=None, min_length=1, max_length=120),
    actor_role: str | None = Query(default=None, pattern="^(nurse|pharmacist|administrator|system)$"),
    outcome: str | None = Query(default=None, min_length=1, max_length=80),
    action_type: str | None = Query(default=None, min_length=1, max_length=80),
    target_table: str | None = Query(default=None, min_length=1, max_length=80),
    occurred_from: Annotated[datetime | None, Query()] = None,
    occurred_to: Annotated[datetime | None, Query()] = None,
) -> list[AuditRecord]:
    _require_roles(principal, "registration", "pharmacist", "operations_admin", "auditor")
    if occurred_from and occurred_to and occurred_from > occurred_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Start date must be before end date.",
        )
    response.headers["Cache-Control"] = "no-store"
    try:
        records = repository.list_audit(
            limit=limit,
            offset=offset,
            search=search,
            actor=actor,
            actor_role=actor_role,
            outcome=outcome,
            action_type=action_type,
            target_table=target_table,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
        )
        return [_safe_audit_record(record) for record in records]
    except SupabaseDataError as exc:
        _raise_repository_error(exc)
