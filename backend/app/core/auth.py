from typing import Annotated, Any

from clerk_backend_api import AuthenticateRequestOptions, authenticate_request
from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.data.supabase_client import SupabaseDataApi, SupabaseDataError


class ClerkIdentity(BaseModel):
    subject: str
    source: str
    factor_verification_age: tuple[int, int] | None = None


class StaffPrincipal(ClerkIdentity):
    role: str
    clinic_id: str


class PatientPrincipal(ClerkIdentity):
    patient_id: int | None
    source_record_key: str


class ReverificationRequired(Exception):
    """Signal Clerk's standard client-side reverification flow."""

    def __init__(self, configuration: str = "strict") -> None:
        self.configuration = configuration
        super().__init__("Fresh credential verification is required.")


def _parse_factor_verification_age(payload: dict[str, Any]) -> tuple[int, int] | None:
    raw_age = payload.get("fva")
    if (
        not isinstance(raw_age, (list, tuple))
        or len(raw_age) != 2
        or any(not isinstance(value, int) or value < -1 for value in raw_age)
    ):
        return None
    return int(raw_age[0]), int(raw_age[1])


def _has_fresh_verification(identity: ClerkIdentity, *, after_minutes: int = 10) -> bool:
    """Match Clerk's strict graceful downgrade when no second factor exists."""
    if identity.source == "demo":
        return True
    if identity.factor_verification_age is None:
        return False
    first_factor_age, second_factor_age = identity.factor_verification_age
    if second_factor_age != -1:
        return second_factor_age < after_minutes
    return first_factor_age != -1 and first_factor_age < after_minutes


def require_synthetic_patient_flow(
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Keep fixture-only unauthenticated adapters out of production."""
    if not settings.demo_mode:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The production patient-token adapter is not configured.",
        )


def require_clerk_identity(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClerkIdentity:
    auth_header = request.headers.get("authorization", "")
    has_bearer = auth_header.lower().startswith("bearer ")
    # Fixture mode still accepts anonymous calls, but a real Clerk session is preferred
    # so first-time onboarding can be keyed to a fresh email identity.
    if settings.demo_mode and not (has_bearer and settings.clerk_configured):
        return ClerkIdentity(subject="synthetic-user", source="demo")
    if not settings.clerk_configured:
        if settings.demo_mode:
            return ClerkIdentity(subject="synthetic-user", source="demo")
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
                authorized_parties=settings.frontend_origin_list,
                accepts_token=["session_token"],
            ),
        )
    except Exception as exc:
        if settings.demo_mode and not has_bearer:
            return ClerkIdentity(subject="synthetic-user", source="demo")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Clerk session.") from exc

    if not request_state.is_signed_in or not request_state.payload:
        if settings.demo_mode and not has_bearer:
            return ClerkIdentity(subject="synthetic-user", source="demo")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valid Clerk session required.")
    return ClerkIdentity(
        subject=str(request_state.payload["sub"]),
        source="clerk",
        factor_verification_age=_parse_factor_verification_age(request_state.payload),
    )


def require_staff(
    identity: Annotated[ClerkIdentity, Depends(require_clerk_identity)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StaffPrincipal:
    """Authorize a verified Clerk identity through the active clinic staff mapping."""
    if settings.demo_mode:
        return StaffPrincipal(
            subject="synthetic-staff",
            source="demo",
            factor_verification_age=(0, -1),
            role="operations_admin",
            clinic_id=settings.clinic_id,
        )
    if not settings.supabase_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Staff authorization storage is not configured.",
        )

    api = SupabaseDataApi(settings.supabase_url, settings.supabase_secret_key)
    try:
        rows = api.select(
            "staff_accounts",
            "id,clerk_user_id,clinic_id,role,active",
            filters={
                "clerk_user_id": f"eq.{identity.subject}",
                "active": "eq.true",
                "deleted_at": "is.null",
            },
            limit=2,
        )
    except SupabaseDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Staff authorization could not be verified.",
        ) from exc
    finally:
        api.close()

    if (
        len(rows) != 1
        or rows[0]["clinic_id"] != settings.clinic_id
        or rows[0].get("active") is not True
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nurse access required for this clinic.",
        )
    return StaffPrincipal(
        subject=identity.subject,
        source=identity.source,
        factor_verification_age=identity.factor_verification_age,
        role=str(rows[0]["role"]),
        clinic_id=str(rows[0]["clinic_id"]),
    )


def require_reverified_staff(
    principal: Annotated[StaffPrincipal, Depends(require_staff)],
) -> StaffPrincipal:
    """Require a first/strongest available factor verified within ten minutes."""
    if not _has_fresh_verification(principal):
        raise ReverificationRequired("strict")
    return principal


def _clerk_primary_email(settings: Settings, clerk_user_id: str) -> str | None:
    if not settings.clerk_secret_key or clerk_user_id.startswith("synthetic"):
        return None
    try:
        from clerk_backend_api import Clerk

        user = Clerk(bearer_auth=settings.clerk_secret_key).users.get(user_id=clerk_user_id)
    except Exception:
        return None
    addresses = getattr(user, "email_addresses", None) or []
    for address in addresses:
        email = getattr(address, "email_address", None)
        if email:
            return str(email)
    return None


def _upsert_patient_account(
    api: SupabaseDataApi,
    *,
    clerk_user_id: str,
    patient_id: int,
    email: str | None,
) -> None:
    existing = api.select(
        "patient_accounts",
        "id,patient_id,email,active",
        filters={"clerk_user_id": f"eq.{clerk_user_id}"},
        limit=1,
    )
    if existing:
        payload: dict[str, object] = {"patient_id": patient_id, "active": True}
        if email:
            payload["email"] = email
        api.update("patient_accounts", payload, filters={"clerk_user_id": f"eq.{clerk_user_id}"})
        return
    try:
        api.insert(
            "patient_accounts",
            {
                "clerk_user_id": clerk_user_id,
                "patient_id": patient_id,
                "email": email,
                "active": True,
            },
        )
    except SupabaseDataError as exc:
        if exc.code != "23505":
            raise


def _synthetic_demo_principal(identity: ClerkIdentity, settings: Settings) -> PatientPrincipal:
    """Map demo auth to the seeded synthetic patient when Supabase is available."""
    if not settings.supabase_configured:
        return PatientPrincipal(
            subject=identity.subject,
            source=identity.source,
            patient_id=1,
            source_record_key=settings.patient_demo_source_record_key,
        )

    api = SupabaseDataApi(settings.supabase_url, settings.supabase_secret_key)
    try:
        patients = api.select(
            "patients",
            "id,source_record_key",
            filters={
                "source_record_key": f"eq.{settings.patient_demo_source_record_key}",
                "deleted_at": "is.null",
            },
            limit=2,
        )
        if len(patients) != 1:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Demo patient scenario is unavailable.",
            )
        patient_id = int(patients[0]["id"])
        if identity.source == "clerk":
            email = _clerk_primary_email(settings, identity.subject)
            _upsert_patient_account(
                api,
                clerk_user_id=identity.subject,
                patient_id=patient_id,
                email=email,
            )
    except SupabaseDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Demo patient scenario could not be resolved.",
        ) from exc
    finally:
        api.close()

    return PatientPrincipal(
        subject=identity.subject,
        source=identity.source,
        patient_id=patient_id,
        source_record_key=str(patients[0]["source_record_key"]),
    )


def require_patient(
    identity: Annotated[ClerkIdentity, Depends(require_clerk_identity)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PatientPrincipal:
    """Authorize a verified Clerk identity through exactly one active patient mapping."""
    if settings.demo_mode:
        return _synthetic_demo_principal(identity, settings)
    if not settings.supabase_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Patient authorization storage is not configured.",
        )

    api = SupabaseDataApi(settings.supabase_url, settings.supabase_secret_key)
    try:
        accounts = api.select(
            "patient_accounts",
            "patient_id",
            filters={"clerk_user_id": f"eq.{identity.subject}", "active": "eq.true"},
            limit=2,
        )
        if len(accounts) != 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patient account activation required.",
            )
        patients = api.select(
            "patients",
            "id,source_record_key",
            filters={"id": f"eq.{accounts[0]['patient_id']}", "deleted_at": "is.null"},
            limit=2,
        )
    except SupabaseDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Patient authorization could not be verified.",
        ) from exc
    finally:
        api.close()

    if len(patients) != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient access is unavailable.")
    return PatientPrincipal(
        subject=identity.subject,
        source=identity.source,
        patient_id=int(patients[0]["id"]),
        source_record_key=str(patients[0]["source_record_key"]),
    )


def _provision_clerk_patient(
    api: SupabaseDataApi,
    *,
    clerk_user_id: str,
    email: str | None,
) -> dict[str, object]:
    from hashlib import sha256

    source_record_key = f"clerk:{clerk_user_id}"
    existing = api.select(
        "patients",
        "id,source_record_key",
        filters={"source_record_key": f"eq.{source_record_key}", "deleted_at": "is.null"},
        limit=1,
    )
    if existing:
        return existing[0]

    display = (email.split("@")[0] if email and "@" in email else "New patient").replace(".", " ").strip()
    display = display.title() if display else "New patient"
    identifier_hash = sha256(f"clerk:{clerk_user_id}".encode("utf-8")).hexdigest()
    return api.insert(
        "patients",
        {
            "source_record_key": source_record_key,
            "identifier_hash": identifier_hash,
            "identifier_masked": "••••",
            "full_name": display,
            "email": email,
            "is_synthetic": False,
        },
    )


def activate_patient_mapping(identity: ClerkIdentity, settings: Settings) -> PatientPrincipal:
    """Attach a Clerk identity to one patient row, creating a personal patient when needed."""
    if settings.demo_mode:
        return _synthetic_demo_principal(identity, settings)
    if not settings.supabase_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Patient authorization storage is not configured.",
        )

    api = SupabaseDataApi(settings.supabase_url, settings.supabase_secret_key)
    try:
        existing = api.select(
            "patient_accounts",
            "patient_id",
            filters={"clerk_user_id": f"eq.{identity.subject}", "active": "eq.true"},
            limit=2,
        )
        if len(existing) > 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Multiple patient mappings found.")
        email = _clerk_primary_email(settings, identity.subject)
        if existing:
            patients = api.select(
                "patients",
                "id,source_record_key",
                filters={"id": f"eq.{existing[0]['patient_id']}", "deleted_at": "is.null"},
                limit=2,
            )
            if len(patients) != 1:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Patient account mapping is unavailable.",
                )
            if email:
                _upsert_patient_account(
                    api,
                    clerk_user_id=identity.subject,
                    patient_id=int(patients[0]["id"]),
                    email=email,
                )
        else:
            patients = [_provision_clerk_patient(api, clerk_user_id=identity.subject, email=email)]
            _upsert_patient_account(
                api,
                clerk_user_id=identity.subject,
                patient_id=int(patients[0]["id"]),
                email=email,
            )
    except SupabaseDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Patient activation could not be completed.",
        ) from exc
    finally:
        api.close()

    return PatientPrincipal(
        subject=identity.subject,
        source=identity.source,
        patient_id=int(patients[0]["id"]),
        source_record_key=str(patients[0]["source_record_key"]),
    )
