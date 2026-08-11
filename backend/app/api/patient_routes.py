from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import require_synthetic_patient_flow
from app.domain.models import CoverageAction, PreArrivalSubmissionRequest, PreArrivalSubmissionResult

router = APIRouter(
    prefix="/patient",
    tags=["patient"],
    dependencies=[Depends(require_synthetic_patient_flow)],
)


@router.post("/pre-arrival/submit", response_model=PreArrivalSubmissionResult)
def submit_pre_arrival(request: PreArrivalSubmissionRequest) -> PreArrivalSubmissionResult:
    if request.coverage_action is CoverageAction.REPLACE and not request.file_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Choose a coverage document before submitting.",
        )

    reference_source = f"{request.appointment_id}:{request.coverage_action}:{request.file_name or 'existing'}"
    reference = f"PRE-{sha256(reference_source.encode()).hexdigest()[:10].upper()}"
    message = (
        "Existing coverage was submitted for current validity and eligibility checks."
        if request.coverage_action is CoverageAction.REUSE
        else "The replacement document was received for extraction and current checks."
    )
    return PreArrivalSubmissionResult(
        processing_reference=reference,
        message=message,
        next_action="Clinic staff will confirm the result before it becomes final.",
    )
