from __future__ import annotations

import argparse
import time
from datetime import UTC, datetime
from pathlib import Path

from backend.app.core.config import get_settings
from backend.app.storage.job_repository import JobRepository
from backend.app.storage.workspaces import JobWorkspace
from backend.app.worker import _redis


def cleanup_expired_jobs(
    repository: JobRepository,
    workspace_root: Path,
    *,
    now: datetime | None = None,
    orphan_grace_seconds: int = 300,
) -> dict[str, int]:
    current_time = now or datetime.now(UTC)
    expired_jobs = 0
    orphaned_workspaces = 0
    known_ids = set(repository.job_ids())
    for job_id in list(known_ids):
        record = repository.get(job_id)
        if record is not None and record.expires_at <= current_time:
            repository.delete(job_id)
            workspace = (workspace_root.resolve() / job_id).resolve()
            if workspace.is_relative_to(workspace_root.resolve()) and workspace.is_dir():
                JobWorkspace(workspace).delete()
            expired_jobs += 1
            known_ids.discard(job_id)

    cutoff = current_time.timestamp() - orphan_grace_seconds
    root = workspace_root.resolve()
    if root.is_dir():
        for child in root.iterdir():
            if not child.is_dir() or child.name in known_ids:
                continue
            if child.stat().st_mtime >= cutoff:
                continue
            resolved = child.resolve()
            if resolved.is_relative_to(root) and len(resolved.parts) > len(root.parts):
                JobWorkspace(resolved).delete()
                orphaned_workspaces += 1
    return {
        "expired_jobs": expired_jobs,
        "orphaned_workspaces": orphaned_workspaces,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    redis = _redis(settings)
    repository = JobRepository(redis, settings.artifact_ttl_seconds)
    while True:
        cleanup_expired_jobs(repository, settings.workspace_root)
        if args.once:
            return
        time.sleep(60)


if __name__ == "__main__":
    main()
