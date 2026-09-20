from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, cast

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.api.jobs import problem
from backend.app.core.config import Settings

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class EvaluationMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cer: float = Field(ge=0, le=1)
    wer: float = Field(ge=0, le=1)


class EvaluationAggregate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw: EvaluationMetrics
    corrected: EvaluationMetrics | None = None


class EvaluationDiff(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original: str
    corrected: str
    label: Literal["improvement", "regression", "unchanged"]


class EvaluationSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    labels: list[str] = Field(default_factory=list)
    page_count: int = Field(ge=1)
    elapsed_ms: float = Field(ge=0)
    raw: EvaluationMetrics
    corrected: EvaluationMetrics | None = None
    correction_count: int = Field(ge=0)
    representative_diffs: list[EvaluationDiff] = Field(default_factory=list)


class PublicEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    measured: bool
    generated_from_manifest_sha256: str = Field(min_length=1)
    engine: str = Field(min_length=1)
    preprocessing_profile: str = Field(min_length=1)
    correction_provider: str = Field(min_length=1)
    run_environment: str = Field(min_length=1)
    aggregate: EvaluationAggregate | None
    samples: list[EvaluationSample]
    methodology: list[str]
    limitations: list[str]

    @model_validator(mode="after")
    def measured_results_have_metrics(self) -> PublicEvaluation:
        if self.measured and self.aggregate is None:
            raise ValueError("measured evaluations require aggregate metrics")
        return self


def _results_path(settings: Settings) -> Path:
    return settings.evaluation_results_path.expanduser().resolve()


@router.get("", response_model=PublicEvaluation)
def get_evaluation(request: Request) -> PublicEvaluation | JSONResponse:
    settings = cast(Settings, request.app.state.settings)
    try:
        payload = json.loads(_results_path(settings).read_text(encoding="utf-8"))
        return PublicEvaluation.model_validate(payload)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return problem(
            503,
            "evaluation_unavailable",
            "The public evaluation result is not available or is invalid.",
            retryable=True,
        )
