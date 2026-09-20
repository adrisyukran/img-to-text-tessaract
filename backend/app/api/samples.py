from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from starlette.responses import Response

from backend.app.api.jobs import problem
from backend.app.ingestion.samples import PublicSample, SampleRegistry

router = APIRouter(prefix="/samples", tags=["samples"])


@router.get("", response_model=list[PublicSample])
def list_samples(request: Request) -> list[PublicSample]:
    registry = cast(SampleRegistry, request.app.state.samples)
    return registry.public_samples()


@router.get("/{sample_id}/preview", response_model=None)
def sample_preview(request: Request, sample_id: str) -> Response:
    registry = cast(SampleRegistry, request.app.state.samples)
    sample = registry.get(sample_id)
    if sample is None:
        return problem(404, "sample_not_found", "The requested sample was not found.")
    return FileResponse(
        sample.pdf_path,
        media_type="application/pdf",
        headers={"Cache-Control": "public, max-age=3600"},
    )
