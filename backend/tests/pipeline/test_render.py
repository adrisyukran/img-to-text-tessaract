from pathlib import Path

import pymupdf
from PIL import Image

from backend.app.ingestion.validation import UploadLimits, validate_upload
from backend.app.pipeline.render import render_pages
from backend.app.storage.workspaces import JobWorkspace


def make_pdf() -> bytes:
    document = pymupdf.open()
    first = document.new_page(width=200, height=300)
    first.insert_text((40, 80), "First page")
    second = document.new_page(width=400, height=500)
    second.insert_text((40, 80), "Second page")
    output = document.tobytes()
    document.close()
    return output


def test_pdf_pages_render_in_order_and_preserve_page_dimensions(tmp_path: Path):
    upload = validate_upload(
        make_pdf(),
        "pages.pdf",
        "application/pdf",
        UploadLimits(max_bytes=100_000, max_pages=3),
    )
    workspace = JobWorkspace.create(tmp_path, "01ABC")

    pages = render_pages(upload, workspace, dpi=72)

    assert [page.page_number for page in pages] == [1, 2]
    assert [page.width_points for page in pages] == [200, 400]
    assert [page.height_points for page in pages] == [300, 500]
    assert all(page.image_path.exists() for page in pages)


def test_png_input_becomes_one_rendered_page(tmp_path: Path):
    image_path = tmp_path / "source.png"
    Image.new("RGB", (100, 80), "white").save(image_path)
    upload = validate_upload(
        image_path.read_bytes(),
        "source.png",
        "image/png",
        UploadLimits(max_bytes=100_000, max_pages=3),
    )
    workspace = JobWorkspace.create(tmp_path / "jobs", "01PNG")

    pages = render_pages(upload, workspace, dpi=72)

    assert len(pages) == 1
    assert pages[0].pixel_width == 100
    assert pages[0].pixel_height == 80
    assert pages[0].image_path.suffix == ".png"
