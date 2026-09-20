from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from backend.app.domain.document import BoundingBox, CanonicalDocument, OCRSpan
from backend.app.domain.jobs import JobRecord, JobStage
from backend.app.ingestion.validation import ValidatedUpload
from backend.app.pipeline.ocr import OCRProblem
from backend.app.pipeline.orchestrator import (
    ArtifactBuilder,
    PipelineServices,
    process_document,
)
from backend.app.pipeline.preprocess import PreprocessedPage, PreprocessMetadata
from backend.app.pipeline.render import RenderedPage
from backend.app.storage.workspaces import JobWorkspace


def make_record() -> JobRecord:
    now = datetime.now(UTC)
    return JobRecord(
        id="job-1",
        source_name="scan.pdf",
        stage=JobStage.queued,
        progress=0,
        total_pages=2,
        created_at=now,
        expires_at=now + timedelta(hours=1),
    )


@dataclass
class FakeRepository:
    record: JobRecord
    updates: list[JobRecord] = field(default_factory=list)
    document: CanonicalDocument | None = None
    document_seen_before_complete: bool = False

    def get(self, job_id: str) -> JobRecord | None:
        return self.record if self.record.id == job_id else None

    def update(
        self,
        job_id: str,
        expected_revision: int,
        changes: dict[str, Any],
    ) -> JobRecord:
        assert job_id == self.record.id
        assert expected_revision == self.record.revision
        self.record = self.record.model_copy(
            update={**changes, "revision": self.record.revision + 1}
        )
        self.updates.append(self.record)
        if self.record.stage is JobStage.complete:
            self.document_seen_before_complete = self.document is not None
        return self.record

    def save_document(self, document: CanonicalDocument) -> None:
        self.document = document


class FakeRenderer:
    def __call__(self, upload: ValidatedUpload, workspace: JobWorkspace) -> list[RenderedPage]:
        del upload, workspace
        return [
            RenderedPage(2, Path("page-2.png"), 100, 100, 72, 72),
            RenderedPage(1, Path("page-1.png"), 100, 100, 72, 72),
        ]


class FakePreprocessor:
    def __call__(self, page: RenderedPage, output_dir: Path) -> PreprocessedPage:
        return PreprocessedPage(
            page,
            output_dir / f"page-{page.page_number}.png",
            PreprocessMetadata(
                rotation_degrees=0,
                deskew_degrees=0,
                contrast_applied=False,
                denoise_applied=False,
                threshold_method="none",
                operations=["grayscale"],
            ),
        )


class FakeOCR:
    def __init__(self, fail_page: int | None = None) -> None:
        self.fail_page = fail_page

    def recognize(self, page: PreprocessedPage) -> list[OCRSpan]:
        if page.rendered.page_number == self.fail_page:
            raise OCRProblem("ocr_unavailable", "internal OCR detail")
        return [
            OCRSpan(
                id=f"p{page.rendered.page_number}-s0001",
                text=f"Page {page.rendered.page_number}",
                bbox=BoundingBox(x=0.1, y=0.1, width=0.3, height=0.1),
                confidence=0.94,
                source={"block_num": 1, "par_num": 1, "line_num": 1, "word_num": 1},
            )
        ]


@dataclass
class FakeArtifacts(ArtifactBuilder):
    built: list[CanonicalDocument] = field(default_factory=list)

    def build(self, document: CanonicalDocument, workspace: JobWorkspace) -> list[str]:
        del workspace
        self.built.append(document)
        return ["document_json"]


def make_services(
    repository: FakeRepository,
    workspace: JobWorkspace,
    *,
    fail_page: int | None = None,
) -> PipelineServices:
    return PipelineServices(
        repository=repository,
        workspace_factory=lambda job_id: workspace,
        upload_loader=lambda record, current_workspace: ValidatedUpload(
            "application/pdf",
            record.source_name,
            record.total_pages,
            b"%PDF-test",
        ),
        renderer=FakeRenderer(),
        preprocessor=FakePreprocessor(),
        ocr_engine=FakeOCR(fail_page),
        correction_service=lambda document: [],
        artifact_builder=FakeArtifacts(),
    )


def test_process_document_tracks_order_progress_and_persists_raw_ocr(tmp_path: Path) -> None:
    repository = FakeRepository(make_record())
    workspace = JobWorkspace.create(tmp_path, "job-1")

    result = process_document("job-1", make_services(repository, workspace))

    assert result.pages[0].number == 1
    assert result.pages[1].number == 2
    assert [span.text for span in result.pages[0].spans] == ["Page 1"]
    assert list(dict.fromkeys(record.stage for record in repository.updates)) == [
        JobStage.rendering,
        JobStage.preprocessing,
        JobStage.ocr,
        JobStage.correction,
        JobStage.exports,
        JobStage.complete,
    ]
    assert [record.progress for record in repository.updates] == sorted(
        record.progress for record in repository.updates
    )
    assert [
        record.current_page
        for record in repository.updates
        if record.stage is JobStage.ocr
    ] == [1, 2]
    assert repository.record.progress == 1
    assert repository.document_seen_before_complete is True


def test_process_document_maps_stage_failure_without_leaking_text(tmp_path: Path) -> None:
    repository = FakeRepository(make_record())
    workspace = JobWorkspace.create(tmp_path, "job-1")

    with pytest.raises(OCRProblem):
        process_document(
            "job-1",
            make_services(repository, workspace, fail_page=2),
        )

    assert repository.record.stage is JobStage.failed
    assert repository.record.error_code == "ocr_unavailable"
    assert "Page 2" not in (repository.record.error_detail or "")
