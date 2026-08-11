from typing import Annotated

from clerk_backend_api import AuthenticateRequestOptions, authenticate_request
from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.config import Settings, get_settings


class StaffPrincipal(BaseModel):
    subject: str
    source: str


def require_staff(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> StaffPrincipal:
    """Verify Clerk JWTs in production while keeping the synthetic demo runnable."""
    if settings.demo_mode:
        return StaffPrincipal(subject="synthetic-staff", source="demo")

    if not settings.clerk_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk authentication is not configured.",
        )

    try:
        request_state = authenticate_request(
            request,
            AuthenticateRequestOptions(
                secret_key=settings.clerk_secret_key,
                jwt_key=settings.clerk_jwt_key,
                authorized_parties=[settings.frontend_origin],
                accepts_token=["session_token"],
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Clerk session.") from exc

    if not request_state.is_signed_in or not request_state.payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valid Clerk session required.")

    return StaffPrincipal(subject=request_state.payload["sub"], source="clerk")
