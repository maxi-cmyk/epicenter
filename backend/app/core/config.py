from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Epicenter API"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    clinic_id: str = "clinic_harbourfront"
    patient_demo_source_record_key: str = "registration:0107"
    # Comma-separated. Defaults cover both split-screen dev processes: the
    # patient screen (port 3000) and the nurse/staff screen (port 3001).
    frontend_origins: str = Field(
        default=(
            "http://localhost:3000,http://127.0.0.1:3000,"
            "http://localhost:3001,http://127.0.0.1:3001"
        ),
        validation_alias=AliasChoices("EPICENTER_FRONTEND_ORIGINS", "EPICENTER_FRONTEND_ORIGIN"),
    )
    demo_mode: bool = True
    persistence_mode: str = Field(default="auto", pattern="^(auto|demo|supabase)$")
    supabase_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("EPICENTER_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
    )
    supabase_publishable_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "EPICENTER_SUPABASE_PUBLISHABLE_KEY",
            "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        ),
    )
    supabase_secret_key: str | None = None
    clerk_secret_key: str | None = Field(default=None, validation_alias="CLERK_SECRET_KEY")
    clerk_jwt_key: str | None = Field(default=None, validation_alias="CLERK_JWT_KEY")

    @property
    def frontend_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_secret_key)

    @property
    def use_supabase_persistence(self) -> bool:
        if self.persistence_mode == "demo":
            return False
        return self.persistence_mode == "supabase" or self.supabase_configured

    @property
    def clerk_configured(self) -> bool:
        return bool(self.clerk_secret_key)

    model_config = SettingsConfigDict(env_file=".env", env_prefix="EPICENTER_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
