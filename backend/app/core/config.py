from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OCR_", env_file=".env", extra="ignore")

    environment: str = "development"
    redis_url: str = "redis://localhost:6379/0"
    workspace_root: Path = Path(".data/jobs")
    frontend_dist: Path | None = None
    evaluation_results_path: Path = Path("evaluation/public-results.json")
    artifact_ttl_seconds: int = Field(default=3600, ge=300, le=86400)
    max_upload_bytes: int = Field(default=15_000_000, ge=1_000_000)
    max_pdf_pages: int = Field(default=12, ge=1, le=50)
    hosted_provider_enabled: bool = False
    hosted_provider_base_url: str | None = None
    hosted_provider_model: str | None = None
    hosted_provider_api_key: SecretStr | None = Field(default=None, repr=False)
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_model: str = "gemini-2.0-flash"
    hosted_quota_limit: int = Field(default=20, ge=0, le=1000)
    hosted_quota_window_seconds: int = Field(default=86400, ge=60, le=604800)


@lru_cache
def get_settings() -> Settings:
    return Settings()
