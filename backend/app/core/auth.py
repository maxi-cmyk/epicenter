from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from jwt import PyJWKClient
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

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required.")

    try:
        signing_key = PyJWKClient(settings.clerk_jwks_url).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            audience=settings.clerk_audience,
            options={"verify_aud": bool(settings.clerk_audience)},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Clerk token.") from exc

    return StaffPrincipal(subject=claims["sub"], source="clerk")
