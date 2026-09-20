from pathlib import Path

import pymupdf

from backend.app.domain.document import (
    BoundingBox,
    CanonicalDocument,
    DocumentBlock,
    DocumentPage,
    OCRSpan,
)
from backend.app.exports.searchable_pdf import SearchablePdfExporter
from backend.app.ingestion.validation import UploadLimits, validate_upload
from backend.app.pipeline.render import RenderedPage


def make_source() -> bytes:
    source = pymupdf.open()
    page = source.new_page(width=200, height=200)
    page.insert_text((20, 40), "Raster source")
    output = source.tobytes()
    source.close()
    return output


def make_document() -> CanonicalDocument:
    span = OCRSpan(
        id="p1-s1",
        text="lnvoice",
        bbox=BoundingBox(x=0.1, y=0.1, width=0.4, height=0.08),
        confidence=0.5,
    )
    block = DocumentBlock(
        id="p1-b1",
        page_number=1,
        kind="paragraph",
        span_ids=[span.id],
        raw_text=span.text,
        bbox=span.bbox,
        confidence=0.5,
    )
    return CanonicalDocument(
        schema_version="1.0",
        job_id="job-1",
        source_name="scan.pdf",
        pages=[DocumentPage(number=1, width=200, height=200, spans=[span], blocks=[block])],
    )


def test_searchable_pdf_preserves_page_and_adds_accepted_text(tmp_path: Path) -> None:
    source_bytes = make_source()
    source = validate_upload(
        source_bytes,
        "scan.pdf",
        "application/pdf",
        UploadLimits(1_000_000, 2),
    )
    rendered = [
        RenderedPage(1, tmp_path / "page.png", 200, 200, 200, 200),
    ]
    output = SearchablePdfExporter().export(make_document(), source, rendered)

    result = pymupdf.open(stream=output, filetype="pdf")
    assert result.page_count == 1
    assert "lnvoice" in result[0].get_text()
    assert "OCRPipelineVersion=1.0" in result.metadata["keywords"]
    result.close()
