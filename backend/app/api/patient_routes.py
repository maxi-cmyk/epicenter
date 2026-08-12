from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import (
    ClerkIdentity,
    PatientPrincipal,
    activate_patient_mapping,
    require_clerk_identity,
    require_patient,
)
from app.core.config import Settings, get_settings
from app.data.dependencies import get_operations_repository
from app.data.operations_repository import OperationsRepository
from app.data.supabase_client import SupabaseDataError
from app.domain.models import (
    CoverageAction,
    PatientAccountSession,
    PreArrivalSubmissionRequest,
    PreArrivalSubmissionResult,
    RegistrationValidationRequest,
    RegistrationValidationResult,
)

router = APIRouter(prefix="/patient", tags=["patient"])

Repository = Annotated[OperationsRepository, Depends(get_operations_repository)]
Identity = Annotated[ClerkIdentity, Depends(require_clerk_identity)]
Patient = Annotated[PatientPrincipal, Depends(require_patient)]
Configuration = Annotated[Settings, Depends(get_settings)]


def _raise_patient_persistence_error(exc: SupabaseDataError) -> NoReturn:
    if exc.code == "PT404":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if exc.code == "PT409":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if exc.code == "PT422":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Persistence service unavailable",
    ) from exc


@router.post("/account/activate", response_model=PatientAccountSession)
def activate_account(identity: Identity, settings: Configuration) -> PatientAccountSession:
    principal = activate_patient_mapping(identity, settings)
    if principal.patient_id is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Patient activation failed.")
    return PatientAccountSession(
        patient_id=principal.patient_id,
        source_record_key=principal.source_record_key,
    )


@router.post("/registration/validate", response_model=RegistrationValidationResult)
def validate_registration(
    request: RegistrationValidationRequest,
    repository: Repository,
    principal: Patient,
) -> RegistrationValidationResult:
    try:
        return repository.validate_registration(request, principal.subject, principal.patient_id)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)


@router.post("/pre-arrival/submit", response_model=PreArrivalSubmissionResult)
def submit_pre_arrival(
    request: PreArrivalSubmissionRequest,
    repository: Repository,
    principal: Patient,
) -> PreArrivalSubmissionResult:
    if request.coverage_action is CoverageAction.REPLACE and not request.file_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Choose a coverage document before submitting.",
        )

    try:
        return repository.submit_prearrival(request, principal.subject, principal.patient_id)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
