from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from backend.app.domain.document import (
    CanonicalDocument,
    CorrectionPatch,
    DocumentPage,
)
from backend.app.domain.jobs import JobRecord, JobStage
from backend.app.ingestion.validation import UploadProblem, ValidatedUpload
from backend.app.pipeline.layout import group_spans
from backend.app.pipeline.ocr import OCREngine, OCRProblem
from backend.app.pipeline.preprocess import PreprocessedPage
from backend.app.pipeline.render import RenderedPage
from backend.app.providers.base import ProviderProblem
from backend.app.storage.job_repository import JobNotFound
from backend.app.storage.workspaces import JobWorkspace


class JobStore(Protocol):
    def get(self, job_id: str) -> JobRecord | None:
        ...

    def update(
        self,
        job_id: str,
        expected_revision: int,
        changes: Mapping[str, Any],
    ) -> JobRecord:
        ...

    def save_document(self, document: CanonicalDocument) -> None:
        ...


class ArtifactBuilder(Protocol):
    def build(self, document: CanonicalDocument, workspace: JobWorkspace) -> list[str]:
        ...


class CanonicalArtifactBuilder:
    def build(self, document: CanonicalDocument, workspace: JobWorkspace) -> list[str]:
        target = workspace.artifact_path("document_json")
        target.write_text(document.model_dump_json(indent=2), encoding="utf-8")
        return ["document_json"]


UploadLoader = Callable[[JobRecord, JobWorkspace], ValidatedUpload]
Renderer = Callable[[ValidatedUpload, JobWorkspace], list[RenderedPage]]
Preprocessor = Callable[[RenderedPage, Path], PreprocessedPage]
CorrectionService = Callable[[CanonicalDocument], list[CorrectionPatch]]


@dataclass(frozen=True)
class PipelineServices:
    repository: JobStore
    workspace_factory: Callable[[str], JobWorkspace]
    upload_loader: UploadLoader
    renderer: Renderer
    preprocessor: Preprocessor
    ocr_engine: OCREngine
    correction_service: CorrectionService | None
    artifact_builder: ArtifactBuilder


def _update(
    services: PipelineServices,
    record: JobRecord,
    *,
    stage: JobStage,
    progress: float,
    current_page: int | None = None,
    artifact_keys: list[str] | None = None,
    error_code: str | None = None,
    error_detail: str | None = None,
) -> JobRecord:
    changes: dict[str, Any] = {
        "stage": stage,
        "progress": max(record.progress, min(1.0, progress)),
    }
    if current_page is not None:
        changes["current_page"] = current_page
    if artifact_keys is not None:
        changes["artifact_keys"] = artifact_keys
    if error_code is not None:
        changes["error_code"] = error_code
    if error_detail is not None:
        changes["error_detail"] = error_detail
    return services.repository.update(record.id, record.revision, changes)


def _failure_details(error: Exception) -> tuple[str, str]:
    if isinstance(error, (UploadProblem, OCRProblem, ProviderProblem)):
        return error.code, error.detail
    return "processing_failed", "The document could not be processed."


def _mark_failed(services: PipelineServices, record: JobRecord, error: Exception) -> None:
    current = services.repository.get(record.id)
    if current is None or current.stage is JobStage.failed:
        return
    code, detail = _failure_details(error)
    services.repository.update(
        current.id,
        current.revision,
        {
            "stage": JobStage.failed,
            "progress": current.progress,
            "error_code": code,
            "error_detail": detail,
        },
    )


def process_document(job_id: str, services: PipelineServices) -> CanonicalDocument:
    record = services.repository.get(job_id)
    if record is None:
        raise JobNotFound(job_id)
    workspace = services.workspace_factory(job_id)

    try:
        record = _update(
            services,
            record,
            stage=JobStage.rendering,
            progress=0.05,
        )
        upload = services.upload_loader(record, workspace)
        rendered = sorted(
            services.renderer(upload, workspace),
            key=lambda page: page.page_number,
        )
        if not rendered:
            raise ValueError("no_pages_rendered")

        record = _update(
            services,
            record,
            stage=JobStage.preprocessing,
            progress=0.2,
        )
        preprocessed: list[PreprocessedPage] = [
            services.preprocessor(page, workspace.pages_dir)
            for page in rendered
        ]

        page_models: list[DocumentPage] = []
        for index, page in enumerate(preprocessed, start=1):
            progress = 0.3 + 0.35 * (index / len(preprocessed))
            record = _update(
                services,
                record,
                stage=JobStage.ocr,
                progress=progress,
                current_page=page.rendered.page_number,
            )
            spans = services.ocr_engine.recognize(page)
            page_models.append(
                DocumentPage(
                    number=page.rendered.page_number,
                    width=page.rendered.pixel_width,
                    height=page.rendered.pixel_height,
                    spans=spans,
                    blocks=group_spans(page.rendered.page_number, spans),
                )
            )

        page_models.sort(key=lambda page: page.number)
        document = CanonicalDocument(
            schema_version="1.0",
            job_id=record.id,
            source_name=record.source_name,
            pages=page_models,
        )
        record = _update(
            services,
            record,
            stage=JobStage.correction,
            progress=0.75,
        )
        if services.correction_service is not None:
            patches = services.correction_service(document)
            document = CanonicalDocument.model_validate(
                document.model_copy(update={"corrections": patches})
            )
        services.repository.save_document(document)

        record = _update(
            services,
            record,
            stage=JobStage.exports,
            progress=0.9,
        )
        artifact_keys = services.artifact_builder.build(document, workspace)
        services.repository.save_document(document)
        _update(
            services,
            record,
            stage=JobStage.complete,
            progress=1,
            current_page=len(page_models),
            artifact_keys=artifact_keys,
        )
        return document
    except Exception as error:
        _mark_failed(services, record, error)
        raise
