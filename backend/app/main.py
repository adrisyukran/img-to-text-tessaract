from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from redis import Redis
from starlette.responses import Response

from backend.app.api.capabilities import router as capabilities_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.health import router as health_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.samples import router as samples_router
from backend.app.core.config import Settings, get_settings
from backend.app.core.rate_limit import RedisQuotaLimiter
from backend.app.ingestion.samples import SampleRegistry
from backend.app.providers.base import CorrectionProvider
from backend.app.providers.factory import provider_for
from backend.app.static import SafeFrontendFiles
from backend.app.storage.job_repository import JobRepository
from backend.app.worker import enqueue_job as enqueue_default_job


def create_app(
    settings: Settings | None = None,
    *,
    repository: JobRepository | None = None,
    redis_client: Redis | None = None,
    enqueue_job: Callable[[str], None] | None = None,
    sample_registry: SampleRegistry | None = None,
    quota_limiter: RedisQuotaLimiter | None = None,
    provider_factory: Callable[[str, Settings], CorrectionProvider] | None = None,
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
    app.state.quota_limiter = quota_limiter or RedisQuotaLimiter(
        app.state.repository.redis,
        resolved.hosted_quota_limit,
        resolved.hosted_quota_window_seconds,
    )
    app.state.enqueue_job = enqueue_job or enqueue_default_job
    app.state.samples = sample_registry or SampleRegistry.default()
    app.state.provider_factory = provider_factory or (
        lambda provider_name, settings: provider_for(provider_name, settings)
    )

    @app.middleware("http")
    async def security_headers(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' blob: data:; connect-src 'self'; "
            "style-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; "
            "frame-ancestors 'none'",
        )
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        return response
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(capabilities_router, prefix="/api/v1")
    app.include_router(evaluation_router, prefix="/api/v1")
    app.include_router(jobs_router, prefix="/api/v1")
    app.include_router(samples_router, prefix="/api/v1")
    if resolved.frontend_dist is not None and resolved.frontend_dist.is_dir():
        app.mount(
            "/",
            SafeFrontendFiles(directory=str(resolved.frontend_dist)),
            name="frontend",
        )
    return app


app = create_app()
