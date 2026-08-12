from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.data.demo_repository import DemoRepository, demo_repository
from app.data.operations_repository import OperationsRepository, SupabaseOperationsRepository
from app.data.supabase_client import SupabaseDataApi


@lru_cache
def _supabase_repository(url: str, secret_key: str, clinic_id: str) -> SupabaseOperationsRepository:
    return SupabaseOperationsRepository(SupabaseDataApi(url, secret_key), clinic_id=clinic_id)


def get_operations_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OperationsRepository:
    if not settings.use_supabase_persistence:
        return demo_repository
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase persistence is selected but its server credentials are missing.",
        )
    return _supabase_repository(settings.supabase_url, settings.supabase_secret_key, settings.clinic_id)


def get_demo_repository() -> DemoRepository:
    """Stable dependency override target for isolated tests."""
    return demo_repository
