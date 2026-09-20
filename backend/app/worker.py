from __future__ import annotations

from pathlib import Path

from redis import Redis
from rq import Queue

from backend.app.core.config import Settings, get_settings
from backend.app.domain.jobs import JobRecord
from backend.app.ingestion.validation import (
    UploadLimits,
    UploadProblem,
    ValidatedUpload,
    validate_upload,
)
from backend.app.pipeline.intelligence import build_basic_report
from backend.app.pipeline.ocr import TesseractEngine
from backend.app.pipeline.orchestrator import (
    CanonicalArtifactBuilder,
    PipelineServices,
    process_document,
)
from backend.app.pipeline.preprocess import preprocess_page
from backend.app.pipeline.render import render_pages
from backend.app.storage.job_repository import JobRepository
from backend.app.storage.workspaces import JobWorkspace


def _redis(settings: Settings) -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def enqueue_job(job_id: str) -> None:
    settings = get_settings()
    queue = Queue("ocr", connection=_redis(settings))
    queue.enqueue(process_hosted_job, job_id, job_timeout=900)


def _workspace(settings: Settings, job_id: str) -> JobWorkspace:
    return JobWorkspace(Path(settings.workspace_root).resolve() / job_id)


def _load_upload(
    record: JobRecord,
    workspace: JobWorkspace,
    settings: Settings,
) -> ValidatedUpload:
    files = [path for path in workspace.input_dir.iterdir() if path.is_file()]
    if len(files) != 1:
        raise UploadProblem("input_missing", "The uploaded document is unavailable.")
    path = files[0]
    return validate_upload(
        path.read_bytes(),
        path.name,
        "application/octet-stream",
        UploadLimits(settings.max_upload_bytes, settings.max_pdf_pages),
    )


def process_hosted_job(job_id: str) -> None:
    settings = get_settings()
    redis_client = _redis(settings)
    repository = JobRepository(redis_client, settings.artifact_ttl_seconds)
    services = PipelineServices(
        repository=repository,
        workspace_factory=lambda current_job_id: _workspace(settings, current_job_id),
        upload_loader=lambda record, workspace: _load_upload(record, workspace, settings),
        renderer=render_pages,
        preprocessor=preprocess_page,
        ocr_engine=TesseractEngine(),
        correction_service=None,
        artifact_builder=CanonicalArtifactBuilder(),
        intelligence_service=build_basic_report,
    )
    process_document(job_id, services)
