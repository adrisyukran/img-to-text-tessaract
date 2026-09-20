from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any, Literal, cast

import ulid
from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sse_starlette import EventSourceResponse, ServerSentEvent
from starlette.responses import Response

from backend.app.core.config import Settings
from backend.app.core.rate_limit import QuotaExceeded, RedisQuotaLimiter
from backend.app.domain.document import CanonicalDocument, CorrectionPatch, CorrectionStatus
from backend.app.domain.jobs import JobRecord, JobStage
from backend.app.exports.digital import DIGITAL_EXPORTERS
from backend.app.exports.searchable_pdf import SearchablePdfExporter
from backend.app.ingestion.validation import UploadLimits, UploadProblem, validate_upload
from backend.app.pipeline.correction import (
    CorrectionRequest,
    apply_patch_status,
    select_candidates,
    validate_proposals,
)
from backend.app.providers.base import ProviderProblem
from backend.app.storage.job_repository import JobRepository, RevisionConflict
from backend.app.storage.workspaces import JobWorkspace

router = APIRouter(prefix="/jobs", tags=["jobs"])
_JOB_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,80}")


class ProblemDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    code: str
    retryable: bool = False
    stage: JobStage | None = None
    page_number: int | None = Field(default=None, ge=1)


class JobResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_name: str
    stage: JobStage
    progress: float
    current_page: int | None
    total_pages: int
    revision: int
    error_code: str | None
    error_detail: str | None
    artifact_keys: list[str]
    created_at: datetime
    expires_at: datetime
    status_url: str
    events_url: str
    document_url: str


class CorrectionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: CorrectionStatus


class CorrectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patch: CorrectionPatch
    derived_text: str
    job_revision: int


class AIRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["gemini", "openai_compatible"] = "openai_compatible"
    api_key: SecretStr | None = None


class AIRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patches: list[CorrectionPatch]
    job_revision: int
    remaining_hosted_documents: int | None


def problem(
    status: int,
    code: str,
    detail: str,
    *,
    retryable: bool = False,
    stage: JobStage | None = None,
    page_number: int | None = None,
) -> JSONResponse:
    payload = ProblemDetail(
        title=code.replace("_", " ").title(),
        status=status,
        detail=detail,
        code=code,
        retryable=retryable,
        stage=stage,
        page_number=page_number,
    )
    return JSONResponse(status_code=status, content=payload.model_dump(mode="json"))


def _repository(request: Request) -> JobRepository:
    return cast(JobRepository, request.app.state.repository)


def _settings(request: Request) -> Any:
    return request.app.state.settings


def _job_response(request: Request, record: JobRecord) -> JobResponse:
    prefix = f"/api/v1/jobs/{record.id}"
    return JobResponse(
        **record.model_dump(),
        status_url=prefix,
        events_url=f"{prefix}/events",
        document_url=f"{prefix}/document",
    )


def _get_record(request: Request, job_id: str) -> JobRecord | JSONResponse:
    if not _JOB_ID_PATTERN.fullmatch(job_id):
        return problem(404, "job_not_found", "The requested job was not found.")
    record = _repository(request).get(job_id)
    if record is None:
        return problem(404, "job_not_found", "The requested job was not found.")
    return record


@router.post("", status_code=202, response_model=JobResponse)
async def create_job(
    request: Request,
    file: Annotated[UploadFile | None, File()] = None,
    sample_id: Annotated[str | None, Form()] = None,
) -> Any:
    if file is not None and sample_id is not None:
        return problem(
            422,
            "ambiguous_job_source",
            "Provide either an upload or a sample, not both.",
        )
    if file is None and sample_id is None:
        return problem(422, "missing_source", "Choose a PDF, PNG, or JPEG file.")
    settings = _settings(request)
    if sample_id is not None:
        sample = request.app.state.samples.get(sample_id)
        if sample is None:
            return problem(404, "sample_not_found", "The requested sample was not found.")
        try:
            content = sample.pdf_path.read_bytes()
        except OSError:
            return problem(404, "sample_not_found", "The requested sample was not found.")
        filename = f"{sample.public.id}.pdf"
        declared_type = "application/pdf"
    else:
        assert file is not None
        content = await file.read(settings.max_upload_bytes + 1)
        filename = file.filename or "document"
        declared_type = file.content_type or ""
    try:
        validated = validate_upload(
            content,
            filename,
            declared_type,
            UploadLimits(settings.max_upload_bytes, settings.max_pdf_pages),
        )
    except UploadProblem as error:
        return problem(422, error.code, error.detail)

    job_id = str(ulid.new())
    settings.workspace_root.mkdir(parents=True, exist_ok=True)
    try:
        workspace = JobWorkspace.create(settings.workspace_root, job_id)
        workspace.write_input(validated.safe_name, validated.content)
    except OSError:
        return problem(
            500,
            "workspace_unavailable",
            "A temporary job workspace could not be created.",
        )

    now = datetime.now(UTC)
    record = JobRecord(
        id=job_id,
        source_name=validated.safe_name,
        stage=JobStage.queued,
        progress=0,
        total_pages=validated.page_count,
        created_at=now,
        expires_at=now + timedelta(seconds=settings.artifact_ttl_seconds),
    )
    repository = _repository(request)
    repository.create(record)
    try:
        request.app.state.enqueue_job(job_id)
    except Exception:
        repository.update(
            job_id,
            expected_revision=0,
            changes={
                "stage": JobStage.failed,
                "error_code": "queue_unavailable",
                "error_detail": "The document could not be queued.",
            },
        )
        return problem(
            503,
            "queue_unavailable",
            "The document could not be queued.",
            retryable=True,
        )
    return _job_response(request, record)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(request: Request, job_id: str) -> Any:
    record = _get_record(request, job_id)
    if isinstance(record, JSONResponse):
        return record
    return _job_response(request, record)


@router.get("/{job_id}/document", response_model=CanonicalDocument)
def get_document(request: Request, job_id: str) -> Any:
    record = _get_record(request, job_id)
    if isinstance(record, JSONResponse):
        return record
    document = _repository(request).get_document(job_id)
    if document is None:
        return problem(
            409,
            "result_not_ready",
            "The document result is not ready yet.",
            retryable=True,
            stage=record.stage,
        )
    return document


@router.patch(
    "/{job_id}/corrections/{patch_id}",
    response_model=CorrectionResponse,
)
def decide_correction(
    request: Request,
    job_id: str,
    patch_id: str,
    decision: CorrectionDecision,
) -> Any:
    record = _get_record(request, job_id)
    if isinstance(record, JSONResponse):
        return record
    repository = _repository(request)
    document = repository.get_document(job_id)
    if document is None:
        return problem(
            409,
            "result_not_ready",
            "The document result is not ready yet.",
            retryable=True,
            stage=record.stage,
        )
    patch = next((item for item in document.corrections if item.id == patch_id), None)
    if patch is None:
        return problem(404, "correction_not_found", "The requested correction was not found.")
    if patch.status is decision.status:
        return CorrectionResponse(
            patch=patch,
            derived_text=document.accepted_text_for_block(patch.block_id),
            job_revision=record.revision,
        )

    updated_document = apply_patch_status(document, patch_id, decision.status)
    stale_artifacts = [
        key
        for key in record.artifact_keys
        if key not in {"document_json", "report_json"}
    ]
    try:
        updated_record = repository.update_document(
            updated_document,
            expected_revision=record.revision,
            changes={
                "artifact_keys": [
                    key for key in record.artifact_keys if key not in stale_artifacts
                ]
            },
        )
    except RevisionConflict:
        return problem(
            409,
            "document_changed",
            "The document changed before this decision was saved.",
            retryable=True,
        )
    updated_patch = next(item for item in updated_document.corrections if item.id == patch_id)
    return CorrectionResponse(
        patch=updated_patch,
        derived_text=updated_document.accepted_text_for_block(updated_patch.block_id),
        job_revision=updated_record.revision,
    )


@router.post("/{job_id}/ai-correction", response_model=AIRunResponse)
async def run_ai_correction(
    request: Request,
    job_id: str,
    run_request: AIRunRequest,
) -> Any:
    record = _get_record(request, job_id)
    if isinstance(record, JSONResponse):
        return record
    repository = _repository(request)
    document = repository.get_document(job_id)
    if document is None:
        return problem(
            409,
            "result_not_ready",
            "The document result is not ready yet.",
            retryable=True,
            stage=record.stage,
        )

    settings = cast(Settings, request.app.state.settings)
    limiter = cast(RedisQuotaLimiter, request.app.state.quota_limiter)
    remaining: int | None = None
    api_key = run_request.api_key
    if api_key is None:
        if not settings.hosted_provider_enabled:
            return problem(
                503,
                "hosted_provider_disabled",
                "Hosted AI is disabled. Supply a supported provider key to continue.",
            )
        if settings.hosted_provider_api_key is None:
            return problem(
                503,
                "hosted_provider_unavailable",
                "Hosted AI is not configured for this deployment.",
                retryable=True,
            )
        identifier = request.client.host if request.client else "anonymous"
        try:
            remaining = limiter.consume(identifier)
        except QuotaExceeded as error:
            return problem(
                429,
                "hosted_quota_exhausted",
                "The hosted AI quota is exhausted until " + error.reset_at.isoformat(),
                retryable=True,
            )
        api_key = settings.hosted_provider_api_key

    candidates = select_candidates(document)
    if not candidates:
        return AIRunResponse(
            patches=[],
            job_revision=record.revision,
            remaining_hosted_documents=remaining,
        )
    correction_request = CorrectionRequest(
        job_id=job_id,
        candidates=[
            {
                "id": candidate.id,
                "page_number": candidate.page_number,
                "block_id": candidate.block_id,
                "span_ids": candidate.span_ids,
                "original_text": candidate.original_text,
                "left_context": candidate.left_context,
                "right_context": candidate.right_context,
                "ocr_confidence": candidate.ocr_confidence,
            }
            for candidate in candidates
        ],
    )
    try:
        provider = request.app.state.provider_factory(run_request.provider, settings)
        proposals = await provider.propose(correction_request, api_key)
        patches = validate_proposals(document, candidates, proposals)
    except ProviderProblem as error:
        return problem(
            429 if error.code == "provider_rate_limited" else 502,
            error.code,
            error.detail,
            retryable=error.retryable,
            stage=JobStage.correction,
        )
    except ValueError:
        return problem(
            502,
            "invalid_provider_response",
            "The provider returned unusable correction data.",
            stage=JobStage.correction,
        )

    existing = {patch.id: patch for patch in document.corrections}
    for patch in patches:
        if patch.id not in existing or existing[patch.id].status is CorrectionStatus.proposed:
            existing[patch.id] = patch
    updated_document = document.model_copy(update={"corrections": list(existing.values())})
    stale_artifacts = [
        key
        for key in record.artifact_keys
        if key not in {"document_json", "report_json"}
    ]
    try:
        updated_record = repository.update_document(
            CanonicalDocument.model_validate(updated_document),
            expected_revision=record.revision,
            changes={
                "artifact_keys": [
                    key for key in record.artifact_keys if key not in stale_artifacts
                ]
            },
        )
    except RevisionConflict:
        return problem(
            409,
            "document_changed",
            "The document changed before the AI result was saved.",
            retryable=True,
        )
    return AIRunResponse(
        patches=patches,
        job_revision=updated_record.revision,
        remaining_hosted_documents=remaining,
    )


@router.get("/{job_id}/exports/{export_format}", response_model=None)
def export_document(request: Request, job_id: str, export_format: str) -> Response:
    record = _get_record(request, job_id)
    if isinstance(record, JSONResponse):
        return record
    document = _repository(request).get_document(job_id)
    if document is None:
        return problem(
            409,
            "result_not_ready",
            "The document result is not ready yet.",
            retryable=True,
            stage=record.stage,
        )
    if export_format == "pdf":
        workspace_root = Path(_settings(request).workspace_root).resolve()
        input_dir = (workspace_root / job_id / "input").resolve()
        if not input_dir.is_relative_to(workspace_root) or not input_dir.is_dir():
            return problem(
                409,
                "export_unavailable",
                "The original source is no longer available for PDF generation.",
                retryable=True,
            )
        input_files = [path for path in input_dir.iterdir() if path.is_file()]
        if len(input_files) != 1:
            return problem(
                409,
                "export_unavailable",
                "The original source is no longer available for PDF generation.",
                retryable=True,
            )
        try:
            source = validate_upload(
                input_files[0].read_bytes(),
                input_files[0].name,
                "application/octet-stream",
                UploadLimits(
                    _settings(request).max_upload_bytes,
                    _settings(request).max_pdf_pages,
                ),
            )
            payload = SearchablePdfExporter().export(document, source, [])
        except (OSError, UploadProblem):
            return problem(
                409,
                "export_unavailable",
                "The searchable PDF could not be generated.",
                retryable=True,
            )
        return Response(
            content=payload,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="document.pdf"',
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "private, no-store",
            },
        )

    exporter = DIGITAL_EXPORTERS.get(export_format)
    if exporter is None:
        return problem(
            404,
            "export_not_supported",
            "The requested export format is not supported.",
        )
    return Response(
        content=exporter.export(document),
        media_type=exporter.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="document.{exporter.extension}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@router.get("/{job_id}/pages/{page_number}/image")
def get_page_image(request: Request, job_id: str, page_number: int) -> Any:
    record = _get_record(request, job_id)
    if isinstance(record, JSONResponse):
        return record
    if page_number < 1 or page_number > record.total_pages:
        return problem(
            404,
            "page_not_found",
            "The requested page does not exist.",
            page_number=page_number,
        )
    target = (
        Path(_settings(request).workspace_root).resolve()
        / job_id
        / "pages"
        / f"page-{page_number:04d}-original.png"
    ).resolve()
    workspace_root = Path(_settings(request).workspace_root).resolve()
    if not target.is_relative_to(workspace_root) or not target.is_file():
        return problem(
            404,
            "page_not_ready",
            "The requested page image is not ready yet.",
            retryable=True,
            page_number=page_number,
        )
    return FileResponse(
        target,
        media_type="image/png",
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@router.delete("/{job_id}", status_code=204, response_model=None)
def delete_job(request: Request, job_id: str) -> None | JSONResponse:
    record = _get_record(request, job_id)
    if isinstance(record, JSONResponse):
        return record
    _repository(request).delete(job_id)
    workspace = Path(_settings(request).workspace_root).resolve() / job_id
    if workspace.exists():
        JobWorkspace(workspace).delete()
    return None


@router.get("/{job_id}/events")
async def job_events(request: Request, job_id: str) -> Any:
    initial = _get_record(request, job_id)
    if isinstance(initial, JSONResponse):
        return initial
    repository = _repository(request)

    async def stream() -> Any:
        last_revision = -1
        heartbeat_at = asyncio.get_running_loop().time()
        while True:
            if await request.is_disconnected():
                return
            current = repository.get(job_id)
            if current is None:
                yield ServerSentEvent(
                    event="job.progress",
                    data=ProblemDetail(
                        title="Job expired",
                        status=404,
                        detail="The job workspace has expired.",
                        code="job_expired",
                    ).model_dump_json(),
                )
                return
            if current.revision > last_revision:
                last_revision = current.revision
                yield ServerSentEvent(
                    event="job.progress",
                    id=str(current.revision),
                    data=current.model_dump_json(),
                )
                if current.stage in (JobStage.complete, JobStage.failed):
                    return
            now = asyncio.get_running_loop().time()
            if now - heartbeat_at >= 15:
                heartbeat_at = now
                yield ServerSentEvent(comment="heartbeat")
            await asyncio.sleep(0.25)

    return EventSourceResponse(stream(), headers={"Cache-Control": "no-cache"})
