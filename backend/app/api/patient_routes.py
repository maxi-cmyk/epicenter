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
    MockPaymentRequest,
    OnboardingAdvanceRequest,
    OnboardingCoverageRequest,
    PatientAccountSession,
    PatientHome,
    PatientOnboardingState,
    PatientPaymentSummary,
    PatientQuestionnaire,
    PatientQueueStatus,
    PatientVisitHistory,
    PreArrivalSubmissionRequest,
    PreArrivalSubmissionResult,
    PriorCoverageSummary,
    QuestionnaireSaveRequest,
    RegistrationValidationRequest,
    RegistrationValidationResult,
    UploadLinkSession,
)

router = APIRouter(prefix="/patient", tags=["patient"])

Repository = Annotated[OperationsRepository, Depends(get_operations_repository)]
Identity = Annotated[ClerkIdentity, Depends(require_clerk_identity)]
Patient = Annotated[PatientPrincipal, Depends(require_patient)]
Configuration = Annotated[Settings, Depends(get_settings)]


def _raise_patient_persistence_error(exc: SupabaseDataError) -> NoReturn:
    message = str(exc)
    if exc.code == "PT404" or "not_found" in message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
    if exc.code == "PT409" or "payment_version_conflict" in message:
        detail = (
            "The payment record changed since it was loaded. Refresh and try again."
            if "payment_version_conflict" in message
            else (
                "Payment is not ready yet."
                if "payment_not_ready" in message
                else message
            )
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
    if exc.code == "PT422":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=message) from exc
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Persistence service unavailable",
    ) from exc


def _raise_domain_error(exc: Exception) -> NoReturn:
    if isinstance(exc, KeyError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found for this patient.") from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    raise exc


@router.post("/account/activate", response_model=PatientAccountSession)
def activate_account(
    identity: Identity,
    settings: Configuration,
    repository: Repository,
) -> PatientAccountSession:
    principal = activate_patient_mapping(identity, settings)
    if principal.patient_id is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Patient activation failed.")
    try:
        onboarding = repository.get_onboarding_state(principal.subject, principal.patient_id)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)
    return PatientAccountSession(
        patient_id=principal.patient_id,
        source_record_key=principal.source_record_key,
        onboarding_completed=onboarding.completed,
        onboarding_step=onboarding.current_step.value,
    )


@router.get("/onboarding", response_model=PatientOnboardingState)
def get_onboarding(repository: Repository, principal: Patient) -> PatientOnboardingState:
    try:
        return repository.get_onboarding_state(principal.subject, principal.patient_id)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)


@router.post("/onboarding/advance", response_model=PatientOnboardingState)
def advance_onboarding(
    request: OnboardingAdvanceRequest,
    repository: Repository,
    principal: Patient,
) -> PatientOnboardingState:
    try:
        return repository.advance_onboarding(request, principal.subject, principal.patient_id)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)


@router.get("/home", response_model=PatientHome)
def get_home(repository: Repository, principal: Patient) -> PatientHome:
    try:
        return repository.get_patient_home(principal.patient_id)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)


@router.get("/coverage/prior", response_model=PriorCoverageSummary)
def get_prior_coverage(
    appointment_id: str,
    repository: Repository,
    principal: Patient,
    first_visit: bool = False,
) -> PriorCoverageSummary:
    try:
        return repository.get_prior_coverage(
            appointment_id,
            principal.patient_id,
            first_visit=first_visit,
        )
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)


@router.get("/queue", response_model=PatientQueueStatus)
def get_queue(repository: Repository, principal: Patient) -> PatientQueueStatus:
    try:
        return repository.get_patient_queue(principal.patient_id)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)


@router.get("/payment", response_model=PatientPaymentSummary)
def get_payment(repository: Repository, principal: Patient) -> PatientPaymentSummary:
    try:
        return repository.get_patient_payment(principal.patient_id)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)


@router.post("/payment/mock-pay", response_model=PatientPaymentSummary)
def mock_pay(
    request: MockPaymentRequest,
    repository: Repository,
    principal: Patient,
) -> PatientPaymentSummary:
    try:
        return repository.submit_mock_payment(request, principal.subject, principal.patient_id)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)


@router.get("/records", response_model=PatientVisitHistory)
def get_records(repository: Repository, principal: Patient) -> PatientVisitHistory:
    try:
        return repository.get_patient_records(principal.patient_id)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)


@router.get("/questionnaire", response_model=PatientQuestionnaire)
def get_questionnaire(
    appointment_id: str,
    repository: Repository,
    principal: Patient,
) -> PatientQuestionnaire:
    try:
        return repository.get_patient_questionnaire(appointment_id, principal.patient_id)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)


@router.post("/questionnaire", response_model=PatientQuestionnaire)
def save_questionnaire(
    request: QuestionnaireSaveRequest,
    repository: Repository,
    principal: Patient,
) -> PatientQuestionnaire:
    try:
        return repository.save_patient_questionnaire(request, principal.subject, principal.patient_id)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)


@router.get("/upload-links/{token}", response_model=UploadLinkSession)
def resolve_upload_link(token: str, repository: Repository) -> UploadLinkSession:
    """Appointment-scoped upload session. Does not create a patient account."""
    try:
        return repository.resolve_upload_link(token)
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)


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


@router.post("/onboarding/coverage", response_model=PreArrivalSubmissionResult)
def submit_onboarding_coverage(
    request: OnboardingCoverageRequest,
    repository: Repository,
    principal: Patient,
) -> PreArrivalSubmissionResult:
    try:
        return repository.submit_onboarding_coverage(
            file_name=request.file_name,
            actor=principal.subject,
            patient_id=principal.patient_id,
            idempotency_key=request.idempotency_key,
        )
    except SupabaseDataError as exc:
        _raise_patient_persistence_error(exc)
    except Exception as exc:
        _raise_domain_error(exc)


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
