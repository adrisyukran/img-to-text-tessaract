from pathlib import Path

import fakeredis
import pymupdf
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.domain.jobs import JobStage
from backend.app.main import create_app
from backend.app.storage.job_repository import JobRepository


def make_pdf() -> bytes:
    document = pymupdf.open()
    document.new_page(width=72, height=72)
    content = document.tobytes()
    document.close()
    return content


def make_client(tmp_path: Path, enqueue: list[str] | None = None) -> TestClient:
    settings = Settings(
        environment="test",
        workspace_root=tmp_path,
        max_upload_bytes=1_000_000,
        max_pdf_pages=4,
    )
    repository = JobRepository(fakeredis.FakeRedis(decode_responses=True), ttl_seconds=120)
    return TestClient(
        create_app(
            settings,
            repository=repository,
            enqueue_job=(enqueue.append if enqueue is not None else lambda job_id: None),
        )
    )


def test_create_job_returns_queued_status_and_validates_content(tmp_path: Path) -> None:
    enqueued: list[str] = []
    with make_client(tmp_path, enqueued) as client:
        response = client.post(
            "/api/v1/jobs",
            files={"file": ("scan.pdf", make_pdf(), "application/pdf")},
        )

        assert response.status_code == 202
        body = response.json()
        assert body["stage"] == "queued"
        assert body["total_pages"] == 1
        assert body["id"] in enqueued
        assert body["events_url"].endswith(f"/{body['id']}/events")
        assert list((tmp_path / body["id"] / "input").iterdir())

        invalid = client.post(
            "/api/v1/jobs",
            files={"file": ("note.txt", b"not a document", "text/plain")},
        )
        assert invalid.status_code == 422
        assert invalid.json()["code"] == "unsupported_file"


def test_get_document_is_not_ready_and_missing_jobs_are_safe(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        created = client.post(
            "/api/v1/jobs",
            files={"file": ("scan.pdf", make_pdf(), "application/pdf")},
        ).json()

        not_ready = client.get(created["document_url"])
        assert not_ready.status_code == 409
        assert not_ready.json()["code"] == "result_not_ready"

        missing = client.get("/api/v1/jobs/01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert missing.status_code == 404
        assert missing.json()["code"] == "job_not_found"


def test_page_route_is_bounded_and_delete_removes_workspace(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        created = client.post(
            "/api/v1/jobs",
            files={"file": ("scan.pdf", make_pdf(), "application/pdf")},
        ).json()
        job_root = tmp_path / created["id"]
        page_path = job_root / "pages" / "page-0001-original.png"
        page_path.write_bytes(b"not-a-real-png")

        image = client.get(f"/api/v1/jobs/{created['id']}/pages/1/image")
        assert image.status_code == 200
        assert image.headers["x-content-type-options"] == "nosniff"
        assert image.headers["cache-control"] == "private, no-store"

        invalid_page = client.get(f"/api/v1/jobs/{created['id']}/pages/2/image")
        assert invalid_page.status_code == 404
        assert invalid_page.json()["code"] == "page_not_found"

        deleted = client.delete(f"/api/v1/jobs/{created['id']}")
        assert deleted.status_code == 204
        assert not job_root.exists()
        assert client.get(f"/api/v1/jobs/{created['id']}").status_code == 404


def test_completed_job_events_emit_named_progress_event(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        created = client.post(
            "/api/v1/jobs",
            files={"file": ("scan.pdf", make_pdf(), "application/pdf")},
        ).json()
        repository: JobRepository = client.app.state.repository
        record = repository.get(created["id"])
        assert record is not None
        repository.update(
            created["id"],
            record.revision,
            {"stage": JobStage.complete, "progress": 1},
        )

        with client.stream("GET", created["events_url"]) as response:
            body = response.read().decode()
        assert response.status_code == 200
        assert "event: job.progress" in body
        assert '"stage":"complete"' in body
