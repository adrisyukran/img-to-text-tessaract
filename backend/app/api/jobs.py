from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any, cast

import ulid
from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sse_starlette import EventSourceResponse, ServerSentEvent

from backend.app.domain.document import CanonicalDocument
from backend.app.domain.jobs import JobRecord, JobStage
from backend.app.ingestion.validation import UploadLimits, UploadProblem, validate_upload
from backend.app.storage.job_repository import JobRepository
from backend.app.storage.workspaces import JobWorkspace

router = APIRouter(prefix="/jobs", tags=["jobs"])
_JOB_ID_PATTERN = re.compile(r"[0-9A-HJKMNP-TV-Z]{26}")


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
