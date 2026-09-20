from pathlib import Path

import fakeredis
import pymupdf
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.ingestion.samples import SampleRegistry
from backend.app.main import create_app
from backend.app.storage.job_repository import JobRepository


def make_pdf() -> bytes:
    document = pymupdf.open()
    document.new_page()
    content = document.tobytes()
    document.close()
    return content


def make_client(tmp_path: Path) -> TestClient:
    settings = Settings(environment="test", workspace_root=tmp_path)
    repository = JobRepository(fakeredis.FakeRedis(decode_responses=True), ttl_seconds=120)
    return TestClient(
        create_app(
            settings,
            repository=repository,
            enqueue_job=lambda job_id: None,
            sample_registry=SampleRegistry.default(),
        )
    )


def test_public_samples_are_safe_and_previews_are_allowlisted(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/v1/samples")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 3
        assert body[0]["id"] == "clean-letter"
        assert "pdf_path" not in body[0]
        assert "ground_truth" not in body[0]

        preview = client.get(body[0]["preview_url"])
        assert preview.status_code == 200
        assert preview.headers["content-type"].startswith("application/pdf")


def test_sample_job_source_is_exclusive_and_allowlisted(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        created = client.post(
            "/api/v1/jobs",
            data={"sample_id": "clean-letter"},
        )
        assert created.status_code == 202
        assert created.json()["source_name"] == "clean-letter.pdf"

        unknown = client.post("/api/v1/jobs", data={"sample_id": "missing"})
        assert unknown.status_code == 404
        assert unknown.json()["code"] == "sample_not_found"

        ambiguous = client.post(
            "/api/v1/jobs",
            data={"sample_id": "clean-letter"},
            files={"file": ("upload.pdf", make_pdf(), "application/pdf")},
        )
        assert ambiguous.status_code == 422
        assert ambiguous.json()["code"] == "ambiguous_job_source"
