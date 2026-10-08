from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

from fastapi.responses import FileResponse, Response
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles


class SafeFrontendFiles(StaticFiles):
    async def get_response(
        self,
        path: str,
        scope: MutableMapping[str, Any],
    ) -> Response:
        parts = Path(path).parts
        if any(part.startswith(".") for part in parts):
            return Response(status_code=404)
        try:
            response = await super().get_response(path, scope)
        except HTTPException as error:
            if error.status_code != 404:
                raise
            response = Response(status_code=404)
        directory = self.directory
        if response.status_code == 404 and "." not in Path(path).name and directory is not None:
            index_path = Path(directory) / "index.html"
            if index_path.is_file():
                return FileResponse(
                    index_path,
                    media_type="text/html",
                    headers={"Cache-Control": "no-cache"},
                )
        if response.status_code == 200:
            if response.media_type == "text/html":
                response.headers["Cache-Control"] = "no-cache"
            elif path.startswith("assets/"):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            elif path == "favicon.svg":
                response.headers["Cache-Control"] = "public, max-age=86400"
        return response
