from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps

from backend.app.ingestion.validation import ValidatedUpload
from backend.app.storage.workspaces import JobWorkspace


@dataclass(frozen=True)
class RenderedPage:
    page_number: int
    image_path: Path
    pixel_width: int
    pixel_height: int
    width_points: float
    height_points: float


def render_pages(
    upload: ValidatedUpload,
    workspace: JobWorkspace,
    dpi: int = 240,
) -> list[RenderedPage]:
    if dpi < 72 or dpi > 400:
        raise ValueError("dpi must be between 72 and 400")
    workspace.pages_dir.mkdir(parents=True, exist_ok=True)
    pages: list[RenderedPage] = []
    max_pixels = 40_000_000

    if upload.media_type == "application/pdf":
        document = pymupdf.open(stream=upload.content, filetype="pdf")  # type: ignore[no-untyped-call]
        try:
            matrix = pymupdf.Matrix(dpi / 72, dpi / 72)  # type: ignore[no-untyped-call]
            for index in range(document.page_count):
                page = document.load_page(index)  # type: ignore[no-untyped-call]
                rectangle = page.rect
                pixel_width = round(rectangle.width * dpi / 72)
                pixel_height = round(rectangle.height * dpi / 72)
                if pixel_width * pixel_height > max_pixels:
                    raise ValueError("page_pixel_limit_exceeded")
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                target = workspace.pages_dir / f"page-{index + 1:04d}-original.png"
                pixmap.save(str(target))
                pages.append(
                    RenderedPage(
                        index + 1,
                        target,
                        pixmap.width,
                        pixmap.height,
                        rectangle.width,
                        rectangle.height,
                    )
                )
        finally:
            document.close()  # type: ignore[no-untyped-call]
        return pages

    with Image.open(BytesIO(upload.content)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        pixel_width, pixel_height = image.size
        if pixel_width * pixel_height > max_pixels:
            raise ValueError("page_pixel_limit_exceeded")
        target = workspace.pages_dir / "page-0001-original.png"
        image.save(target, format="PNG")
    return [
        RenderedPage(
            1,
            target,
            pixel_width,
            pixel_height,
            pixel_width * 72 / dpi,
            pixel_height * 72 / dpi,
        )
    ]
