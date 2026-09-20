from datetime import UTC, datetime, timedelta

import fakeredis
import pytest

from backend.app.domain.document import (
    BoundingBox,
    CanonicalDocument,
    DocumentBlock,
    DocumentPage,
    OCRSpan,
)
from backend.app.domain.jobs import JobRecord, JobStage
from backend.app.storage.job_repository import (
    DuplicateJob,
    JobNotFound,
    JobRepository,
    RevisionConflict,
)


def make_record(job_id: str = "job-1") -> JobRecord:
    now = datetime.now(UTC)
    return JobRecord(
        id=job_id,
        source_name="scan.pdf",
        stage=JobStage.queued,
        progress=0,
        total_pages=1,
        created_at=now,
        expires_at=now + timedelta(hours=1),
    )


def make_document() -> CanonicalDocument:
    span = OCRSpan(
        id="p1-s1",
        text="Hello",
        bbox=BoundingBox(x=0.1, y=0.1, width=0.2, height=0.05),
        confidence=0.9,
    )
    block = DocumentBlock(
        id="p1-b1",
        page_number=1,
        kind="paragraph",
        span_ids=[span.id],
        raw_text=span.text,
        bbox=span.bbox,
        confidence=span.confidence,
    )
    return CanonicalDocument(
        schema_version="1.0",
        job_id="job-1",
        source_name="scan.pdf",
        pages=[DocumentPage(number=1, width=100, height=100, spans=[span], blocks=[block])],
    )


def test_create_get_and_duplicate_are_explicit() -> None:
    redis = fakeredis.FakeRedis(decode_responses=True)
    repository = JobRepository(redis, ttl_seconds=120)
    record = make_record()

    repository.create(record)

    assert repository.get(record.id) == record
    with pytest.raises(DuplicateJob):
        repository.create(record)


def test_update_uses_revision_and_refreshes_ttl() -> None:
    redis = fakeredis.FakeRedis(decode_responses=True)
    repository = JobRepository(redis, ttl_seconds=120)
    record = make_record()
    repository.create(record)

    updated = repository.update(
        record.id,
        expected_revision=0,
        changes={"stage": JobStage.ocr, "progress": 0.5, "current_page": 1},
    )

    assert updated.revision == 1
    assert updated.stage is JobStage.ocr
    assert repository.get(record.id) == updated
    assert redis.ttl(f"job:{record.id}") > 0
    with pytest.raises(RevisionConflict):
        repository.update(record.id, expected_revision=0, changes={"progress": 0.6})


def test_document_write_refreshes_ttl_and_delete_removes_state() -> None:
    redis = fakeredis.FakeRedis(decode_responses=True)
    repository = JobRepository(redis, ttl_seconds=120)
    record = make_record()
    repository.create(record)

    document = make_document()
    repository.save_document(document)

    assert repository.get_document(record.id) == document
    assert redis.ttl(f"job:{record.id}") > 0
    assert redis.ttl(f"job:{record.id}:document") > 0

    repository.delete(record.id)

    assert repository.get(record.id) is None
    assert repository.get_document(record.id) is None


def test_missing_jobs_do_not_create_state() -> None:
    redis = fakeredis.FakeRedis(decode_responses=True)
    repository = JobRepository(redis, ttl_seconds=120)

    assert repository.get("missing") is None
    assert repository.get_document("missing") is None
    with pytest.raises(JobNotFound):
        repository.update("missing", expected_revision=0, changes={"progress": 1})
