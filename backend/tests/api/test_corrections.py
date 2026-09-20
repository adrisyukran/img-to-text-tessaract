from datetime import UTC, datetime, timedelta
from pathlib import Path

import fakeredis
import pymupdf
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.domain.document import (
    BoundingBox,
    CanonicalDocument,
    DocumentBlock,
    DocumentPage,
    OCRSpan,
)
from backend.app.domain.jobs import JobRecord, JobStage
from backend.app.main import create_app
from backend.app.pipeline.correction import (
    CorrectionProposal,
    CorrectionRequest,
    select_candidates,
    validate_proposals,
)
from backend.app.storage.job_repository import JobRepository


def make_document() -> CanonicalDocument:
    span = OCRSpan(
        id="p1-s1",
        text="lnvoice",
        bbox=BoundingBox(x=0.1, y=0.1, width=0.2, height=0.04),
        confidence=0.5,
    )
    block = DocumentBlock(
        id="p1-b1",
        page_number=1,
        kind="paragraph",
        span_ids=[span.id],
        raw_text=span.text,
        bbox=span.bbox,
        confidence=0.5,
    )
    document = CanonicalDocument(
        schema_version="1.0",
        job_id="job-1",
        source_name="scan.pdf",
        pages=[DocumentPage(number=1, width=100, height=100, spans=[span], blocks=[block])],
    )
    candidate = select_candidates(document)[0]
    patch = validate_proposals(
        document,
        [candidate],
        [
            CorrectionProposal(
                candidate_id=candidate.id,
                original_text="lnvoice",
                replacement_text="Invoice",
                rationale="OCR confusion",
                confidence=0.98,
            )
        ],
    )
    return document.model_copy(update={"corrections": patch})


def make_source_pdf() -> bytes:
    source = pymupdf.open()
    source.new_page(width=200, height=200)
    payload = source.tobytes()
    source.close()
    return payload


def make_client(tmp_path: Path) -> tuple[TestClient, JobRepository]:
    settings = Settings(environment="test", workspace_root=tmp_path)
    repository = JobRepository(fakeredis.FakeRedis(decode_responses=True), ttl_seconds=120)
    now = datetime.now(UTC)
    repository.create(
        JobRecord(
            id="job-1",
            source_name="scan.pdf",
            stage=JobStage.complete,
            progress=1,
            total_pages=1,
            created_at=now,
            expires_at=now + timedelta(hours=1),
        )
    )
    repository.save_document(make_document())
    return (
        TestClient(
            create_app(settings, repository=repository, enqueue_job=lambda job_id: None)
        ),
        repository,
    )


def test_correction_decision_is_reversible_and_idempotent(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        document = client.app.state.repository.get_document("job-1")
        assert document is not None
        patch_id = document.corrections[0].id

        accepted = client.patch(
            f"/api/v1/jobs/job-1/corrections/{patch_id}",
            json={"status": "accepted"},
        )
        assert accepted.status_code == 200
        assert accepted.json()["patch"]["status"] == "accepted"
        assert accepted.json()["derived_text"] == "Invoice"
        first_revision = accepted.json()["job_revision"]

        repeated = client.patch(
            f"/api/v1/jobs/job-1/corrections/{patch_id}",
            json={"status": "accepted"},
        )
        assert repeated.status_code == 200
        assert repeated.json()["job_revision"] == first_revision

        rejected = client.patch(
            f"/api/v1/jobs/job-1/corrections/{patch_id}",
            json={"status": "rejected"},
        )
        assert rejected.status_code == 200
        assert rejected.json()["derived_text"] == "lnvoice"


def test_correction_unknown_ids_are_distinct(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        missing_job = client.patch(
            "/api/v1/jobs/missing/corrections/p-missing",
            json={"status": "accepted"},
        )
        assert missing_job.status_code == 404
        assert missing_job.json()["code"] == "job_not_found"

        missing_patch = client.patch(
            "/api/v1/jobs/job-1/corrections/p-missing",
            json={"status": "accepted"},
        )
        assert missing_patch.status_code == 404
        assert missing_patch.json()["code"] == "correction_not_found"


def test_exports_are_fixed_attachments(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        response = client.get("/api/v1/jobs/job-1/exports/markdown")

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="document.md"'
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "Invoice" not in response.text
    assert "lnvoice" in response.text


def test_searchable_pdf_export_preserves_source_and_adds_text_layer(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    input_dir = tmp_path / "job-1" / "input"
    input_dir.mkdir(parents=True)
    (input_dir / "scan.pdf").write_bytes(make_source_pdf())

    with client:
        response = client.get("/api/v1/jobs/job-1/exports/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == 'attachment; filename="document.pdf"'
    exported = pymupdf.open(stream=response.content, filetype="pdf")
    assert "lnvoice" in exported[0].get_text()
    exported.close()


class FakeProvider:
    def __init__(self) -> None:
        self.seen_key = ""

    async def propose(
        self,
        request: CorrectionRequest,
        api_key: object,
    ) -> list[CorrectionProposal]:
        self.seen_key = str(api_key)
        candidate = request.candidates[0]
        return [
            CorrectionProposal(
                candidate_id=str(candidate["id"]),
                original_text=str(candidate["original_text"]),
                replacement_text="Invoice",
                rationale="Fake contract provider",
                confidence=0.99,
            )
        ]


def test_byok_key_is_request_scoped_and_never_persisted(tmp_path: Path) -> None:
    client, repository = make_client(tmp_path)
    provider = FakeProvider()
    client.app.state.provider_factory = lambda name, settings: provider
    with client:
        response = client.post(
            "/api/v1/jobs/job-1/ai-correction",
            json={"provider": "openai_compatible", "api_key": "secret-byok-key"},
        )

    assert response.status_code == 200
    assert "secret-byok-key" not in response.text
    assert provider.seen_key.endswith("**********")
    values = [
        value.decode() if isinstance(value, bytes) else value
        for key in ("job:job-1", "job:job-1:document")
        if (value := repository.redis.get(key)) is not None
    ]
    assert all("secret-byok-key" not in value for value in values)
