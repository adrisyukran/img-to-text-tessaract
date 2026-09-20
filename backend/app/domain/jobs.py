from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class JobStage(StrEnum):
    queued = "queued"
    rendering = "rendering"
    preprocessing = "preprocessing"
    ocr = "ocr"
    correction = "correction"
    awaiting_byok = "awaiting_byok"
    intelligence = "intelligence"
    exports = "exports"
    complete = "complete"
    failed = "failed"


class JobRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    source_name: str = Field(min_length=1)
    stage: JobStage
    progress: float = Field(ge=0, le=1)
    current_page: int | None = Field(default=None, ge=1)
    total_pages: int = Field(ge=1)
    revision: int = Field(default=0, ge=0)
    error_code: str | None = None
    error_detail: str | None = None
    artifact_keys: list[str] = Field(default_factory=list)
    created_at: datetime
    expires_at: datetime
