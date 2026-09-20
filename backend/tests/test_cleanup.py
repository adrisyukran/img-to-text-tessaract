from datetime import UTC, datetime, timedelta
from pathlib import Path

import fakeredis

from backend.app.cleanup import cleanup_expired_jobs
from backend.app.domain.jobs import JobRecord, JobStage
from backend.app.storage.job_repository import JobRepository
from backend.app.storage.workspaces import JobWorkspace


def record(job_id: str, expires_at: datetime) -> JobRecord:
    return JobRecord(
        id=job_id,
        source_name="scan.pdf",
        stage=JobStage.complete,
        progress=1,
        total_pages=1,
        created_at=expires_at - timedelta(hours=1),
        expires_at=expires_at,
    )


def test_cleanup_deletes_only_expired_jobs_and_old_orphans(tmp_path: Path) -> None:
    redis = fakeredis.FakeRedis(decode_responses=True)
    repository = JobRepository(redis, ttl_seconds=120)
    now = datetime(2026, 9, 20, 12, tzinfo=UTC)
    repository.create(record("expired", now - timedelta(seconds=1)))
    repository.create(record("active", now + timedelta(hours=1)))
    expired_workspace = JobWorkspace.create(tmp_path, "expired")
    active_workspace = JobWorkspace.create(tmp_path, "active")
    orphan_workspace = JobWorkspace.create(tmp_path, "orphan")
    (orphan_workspace.root / "state" / "marker").write_text("x", encoding="utf-8")
    old_time = (now - timedelta(seconds=500)).timestamp()
    import os

    os.utime(orphan_workspace.root, (old_time, old_time))

    result = cleanup_expired_jobs(repository, tmp_path, now=now, orphan_grace_seconds=300)

    assert result == {"expired_jobs": 1, "orphaned_workspaces": 1}
    assert repository.get("expired") is None
    assert repository.get("active") is not None
    assert not expired_workspace.root.exists()
    assert active_workspace.root.exists()
    assert not orphan_workspace.root.exists()
