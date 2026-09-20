from datetime import UTC, datetime, timedelta
from pathlib import Path

import fakeredis
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.app.core.config import Settings
from backend.app.core.rate_limit import RedisQuotaLimiter
from backend.app.domain.jobs import JobRecord, JobStage
from backend.app.main import create_app
from backend.app.pipeline.correction import CorrectionProposal, CorrectionRequest
from backend.app.storage.job_repository import JobRepository
from backend.tests.api.test_corrections import make_document


class FakeHostedProvider:
    async def propose(
        self,
        request: CorrectionRequest,
        api_key: SecretStr,
    ) -> list[CorrectionProposal]:
        candidate = request.candidates[0]
        return [
            CorrectionProposal(
                candidate_id=str(candidate["id"]),
                original_text=str(candidate["original_text"]),
                replacement_text="Invoice",
                rationale="deterministic test provider",
                confidence=0.99,
            )
        ]


def test_hosted_ai_is_server_keyed_and_rate_limited(tmp_path: Path) -> None:
    redis = fakeredis.FakeRedis(decode_responses=True)
    repository = JobRepository(redis, ttl_seconds=120)
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
    settings = Settings(
        environment="test",
        workspace_root=tmp_path,
        hosted_provider_enabled=True,
        hosted_provider_api_key=SecretStr("server-secret"),
        hosted_quota_limit=1,
    )
    limiter = RedisQuotaLimiter(redis, limit=1, window_seconds=60)
    provider = FakeHostedProvider()
    with TestClient(
        create_app(
            settings,
            repository=repository,
            quota_limiter=limiter,
            provider_factory=lambda name, current_settings: provider,
            enqueue_job=lambda job_id: None,
        )
    ) as client:
        first = client.post(
            "/api/v1/jobs/job-1/ai-correction",
            json={"provider": "openai_compatible"},
        )
        second = client.post(
            "/api/v1/jobs/job-1/ai-correction",
            json={"provider": "openai_compatible"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["code"] == "hosted_quota_exhausted"
