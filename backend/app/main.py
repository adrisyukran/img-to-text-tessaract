from fastapi import FastAPI

from backend.app.api.health import router as health_router
from backend.app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    app = FastAPI(title="Scanned PDF Intelligence API", version="1.0.0")
    app.state.settings = resolved
    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()
