import json
from pathlib import Path

import fakeredis
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.storage.job_repository import JobRepository


def make_client(tmp_path: Path, result: dict[str, object]) -> TestClient:
    result_path = tmp_path / "public-results.json"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    settings = Settings(
        environment="test",
        workspace_root=tmp_path / "jobs",
        evaluation_results_path=result_path,
    )
    repository = JobRepository(fakeredis.FakeRedis(decode_responses=True), ttl_seconds=120)
    return TestClient(create_app(settings, repository=repository, enqueue_job=lambda job_id: None))


def test_public_evaluation_returns_validated_metrics(tmp_path: Path) -> None:
    result = {
        "schema_version": "1.0",
        "measured": True,
        "generated_from_manifest_sha256": "abc123",
        "engine": "Tesseract 5",
        "preprocessing_profile": "deskew-v1",
        "correction_provider": "fixture-provider",
        "run_environment": "test",
        "aggregate": {
            "raw": {"cer": 0.2, "wer": 0.3},
            "corrected": {"cer": 0.1, "wer": 0.2},
        },
        "samples": [],
        "methodology": ["Synthetic corpus"],
        "limitations": ["Printed English only"],
    }
    with make_client(tmp_path, result) as client:
        response = client.get("/api/v1/evaluation")

    assert response.status_code == 200
    assert response.json()["aggregate"]["corrected"]["cer"] == 0.1


def test_public_evaluation_rejects_invalid_metric(tmp_path: Path) -> None:
    result = {
        "schema_version": "1.0",
        "measured": True,
        "generated_from_manifest_sha256": "abc123",
        "engine": "Tesseract 5",
        "preprocessing_profile": "deskew-v1",
        "correction_provider": "fixture-provider",
        "run_environment": "test",
        "aggregate": {"raw": {"cer": 1.2, "wer": 0.3}, "corrected": None},
        "samples": [],
        "methodology": [],
        "limitations": [],
    }
    with make_client(tmp_path, result) as client:
        response = client.get("/api/v1/evaluation")

    assert response.status_code == 503
    assert response.json()["code"] == "evaluation_unavailable"
