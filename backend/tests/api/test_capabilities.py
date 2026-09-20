from pathlib import Path

import fakeredis
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.storage.job_repository import JobRepository


def test_capabilities_reflect_settings_and_provider_modes(tmp_path: Path) -> None:
    settings = Settings(
        environment="test",
        workspace_root=tmp_path,
        max_upload_bytes=1_234_567,
        max_pdf_pages=7,
        artifact_ttl_seconds=900,
        hosted_provider_enabled=False,
    )
    repository = JobRepository(fakeredis.FakeRedis(decode_responses=True), ttl_seconds=900)
    with TestClient(
        create_app(settings, repository=repository, enqueue_job=lambda job_id: None)
    ) as client:
        response = client.get("/api/v1/capabilities")

    assert response.status_code == 200
    assert response.json() == {
        "accepted_media_types": ["application/pdf", "image/png", "image/jpeg"],
        "max_upload_bytes": 1_234_567,
        "max_pdf_pages": 7,
        "artifact_ttl_seconds": 900,
        "hosted_provider": {
            "enabled": False,
            "remaining_documents": 0,
            "reset_at": None,
        },
        "byok_providers": ["gemini", "openai_compatible"],
    }
