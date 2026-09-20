from collections.abc import Callable

from fastapi import FastAPI
from redis import Redis

from backend.app.api.health import router as health_router
from backend.app.api.jobs import router as jobs_router
from backend.app.core.config import Settings, get_settings
from backend.app.storage.job_repository import JobRepository
from backend.app.worker import enqueue_job as enqueue_default_job


def create_app(
    settings: Settings | None = None,
    *,
    repository: JobRepository | None = None,
    redis_client: Redis | None = None,
    enqueue_job: Callable[[str], None] | None = None,
) -> FastAPI:
    resolved = settings or get_settings()
    app = FastAPI(title="Scanned PDF Intelligence API", version="1.0.0")
    app.state.settings = resolved
    app.state.redis = redis_client or (repository.redis if repository is not None else None)
    app.state.repository = repository or JobRepository(
        app.state.redis
        or Redis.from_url(resolved.redis_url, decode_responses=True),
        resolved.artifact_ttl_seconds,
    )
    app.state.enqueue_job = enqueue_job or enqueue_default_job
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(jobs_router, prefix="/api/v1")
    return app


app = create_app()
