from __future__ import annotations

from datetime import datetime
from typing import cast

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from backend.app.core.config import Settings
from backend.app.core.rate_limit import RedisQuotaLimiter

router = APIRouter(prefix="/capabilities", tags=["capabilities"])


class HostedProviderCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    remaining_documents: int = Field(ge=0)
    reset_at: datetime | None


class Capabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted_media_types: list[str]
    max_upload_bytes: int = Field(gt=0)
    max_pdf_pages: int = Field(gt=0)
    artifact_ttl_seconds: int = Field(gt=0)
    hosted_provider: HostedProviderCapabilities
    byok_providers: list[str]


@router.get("", response_model=Capabilities)
def get_capabilities(request: Request) -> Capabilities:
    settings = cast(Settings, request.app.state.settings)
    limiter = cast(RedisQuotaLimiter, request.app.state.quota_limiter)
    identifier = request.client.host if request.client else "anonymous"
    enabled = settings.hosted_provider_enabled
    return Capabilities(
        accepted_media_types=["application/pdf", "image/png", "image/jpeg"],
        max_upload_bytes=settings.max_upload_bytes,
        max_pdf_pages=settings.max_pdf_pages,
        artifact_ttl_seconds=settings.artifact_ttl_seconds,
        hosted_provider=HostedProviderCapabilities(
            enabled=enabled,
            remaining_documents=limiter.remaining(identifier) if enabled else 0,
            reset_at=limiter.reset_at() if enabled else None,
        ),
        byok_providers=["gemini", "openai_compatible"],
    )
