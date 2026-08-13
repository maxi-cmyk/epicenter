"""MCP endpoint authentication and per-call authorization.

Every MCP tool call re-checks:
- actor identity (API key in demo mode, Clerk JWT in production)
- actor role and clinic scope
- record-level boundaries (clinic_id must match the request)

This module does NOT contain business logic — it only validates who may call
what and raises HTTPException on violation so FastAPI handles the response.
"""

from __future__ import annotations

import logging
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.core.auth import StaffPrincipal
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# API key scheme (demo/synthetic environments)
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-MCP-API-Key", auto_error=False)

# Roles permitted to call MCP tools at all
_MCP_ALLOWED_ROLES = {
    "registration_staff",
    "operations_admin",
    "auditor",
}

# Operations that require operations_admin or higher
_OPERATIONS_ADMIN_TOOLS = {
    "epicenter_get_allocation_recommendation",
    "epicenter_run_simulation",
    "epicenter_compare_simulation_runs",
}

# Registry tools require at least operations_admin
_REGISTRY_ALLOWED_ROLES = {"operations_admin"}


def _verify_api_key(provided: str | None, expected: str | None) -> bool:
    """Constant-time API key comparison to avoid timing side-channels."""
    if not expected or not provided:
        return False
    return secrets.compare_digest(provided.encode(), expected.encode())


def require_mcp_identity(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    api_key: Annotated[str | None, Security(_api_key_header)],
) -> StaffPrincipal:
    """Authenticate an MCP caller.

    A configured MCP key may authenticate a separately approved machine client
    in any environment. Without that header, demo mode uses a synthetic principal
    and production requires a Clerk session.
    """
    if api_key is not None:
        if not _verify_api_key(api_key, settings.mcp_api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Valid MCP API key required.",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        return StaffPrincipal(
            subject="mcp-api-key",
            source="api_key",
            factor_verification_age=(0, -1),
            role="operations_admin",
            clinic_id=settings.clinic_id,
        )

    if settings.demo_mode:
        if settings.mcp_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Valid MCP API key required.",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        return StaffPrincipal(
            subject="mcp-demo-key",
            source="demo",
            factor_verification_age=(0, -1),
            role="operations_admin",
            clinic_id=settings.clinic_id,
        )

    # Production browser/staff clients require a valid Clerk JWT + active mapping.
    if not settings.clerk_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCP authentication is not configured.",
        )
    from clerk_backend_api import AuthenticateRequestOptions, authenticate_request

    from app.core.auth import (
        ClerkIdentity,
        _parse_factor_verification_age,
    )

    try:
        request_state = authenticate_request(
            request,
            AuthenticateRequestOptions(
                secret_key=settings.clerk_secret_key,
                jwt_key=settings.clerk_jwt_key,
                authorized_parties=settings.frontend_origin_list,
                accepts_token=["session_token"],
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Clerk session.") from exc

    if not request_state.is_signed_in or not request_state.payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valid Clerk session required.")

    identity = ClerkIdentity(
        subject=str(request_state.payload["sub"]),
        source="clerk",
        factor_verification_age=_parse_factor_verification_age(request_state.payload),
    )
    # Reuse the existing staff lookup
    from app.data.supabase_client import SupabaseDataApi, SupabaseDataError

    if not settings.supabase_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Staff authorization storage not configured.",
        )

    api = SupabaseDataApi(settings.supabase_url, settings.supabase_secret_key)
    try:
        rows = api.select(
            "staff_accounts",
            "id,clerk_user_id,clinic_id,role,active",
            filters={"clerk_user_id": f"eq.{identity.subject}", "active": "eq.true", "deleted_at": "is.null"},
            limit=2,
        )
    except SupabaseDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Staff authorization could not be verified.",
        ) from exc
    finally:
        api.close()

    if len(rows) != 1 or rows[0]["clinic_id"] != settings.clinic_id or rows[0].get("active") is not True:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nurse access required for this clinic.")

    return StaffPrincipal(
        subject=identity.subject,
        source=identity.source,
        factor_verification_age=identity.factor_verification_age,
        role=str(rows[0]["role"]),
        clinic_id=str(rows[0]["clinic_id"]),
    )


def authorize_operations_tool(
    tool_name: str,
    principal: StaffPrincipal,
    *,
    clinic_id: str | None = None,
) -> None:
    """Re-authorize a specific Operations MCP tool call.

    Raises HTTPException if the principal's role does not permit the tool,
    or if clinic_id does not match the principal's scope.

    This is called inside each tool handler, not just at the route level.
    """
    if principal.role not in _MCP_ALLOWED_ROLES:
        logger.warning(
            "MCP tool %s denied: role %s not in allowlist", tool_name, principal.role
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{principal.role}' is not permitted to call MCP tools.",
        )

    if tool_name in _OPERATIONS_ADMIN_TOOLS and principal.role not in {"operations_admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tool '{tool_name}' requires operations_admin role.",
        )

    if clinic_id is not None and clinic_id != principal.clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clinic scope mismatch.",
        )


def authorize_registry_tool(
    tool_name: str,
    principal: StaffPrincipal,
) -> None:
    """Re-authorize an Insurance Format Registry MCP tool call.

    Registry tools are restricted to operations_admin and above.
    """
    if principal.role not in _REGISTRY_ALLOWED_ROLES:
        logger.warning(
            "Registry MCP tool %s denied: role %s not permitted", tool_name, principal.role
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Role '{principal.role}' is not permitted to call Insurance Format Registry tools."
            ),
        )
