from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Falcon AI Job Hunter"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = Field(
        default="postgresql+asyncpg://falcon:falcon@db:5432/falcon"
    )
    log_level: str = "INFO"
    jwt_secret_key: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    cv_storage_path: Path = Path("backend/app/storage/cvs")
    max_cv_size_mb: int = 10
    local_password_reset_enabled: bool = False
    remoteok_api_url: str = "https://remoteok.com/api"
    remoteok_timeout_seconds: float = Field(default=20, ge=1, le=60)
    real_job_refresh_minutes: int = Field(default=60, ge=15, le=1440)
    smartrecruiters_application_token: SecretStr | None = None
    smartrecruiters_application_company: str | None = None

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+asyncpg://" + value[len(prefix):]
        return value

    def validate_production(self) -> None:
        if self.app_env != "production":
            return
        if self.debug or self.local_password_reset_enabled:
            raise RuntimeError(
                "Production requires DEBUG=false and LOCAL_PASSWORD_RESET_ENABLED=false"
            )
        if (
            len(self.jwt_secret_key) < 32
            or self.jwt_secret_key == "change-this-secret-in-production"
        ):
            raise RuntimeError(
                "Production requires a securely generated JWT_SECRET_KEY"
            )
        if not self.database_url.startswith("postgresql+asyncpg://"):
            raise RuntimeError("Production requires a PostgreSQL DATABASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()
