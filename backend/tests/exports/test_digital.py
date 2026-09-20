from backend.app.domain.document import (
    BoundingBox,
    CanonicalDocument,
    CorrectionPatch,
    DocumentBlock,
    DocumentPage,
    OCRSpan,
)
from backend.app.exports.digital import DIGITAL_EXPORTERS


def make_document() -> CanonicalDocument:
    page_one_spans = [
        OCRSpan(
            id="p1-s1",
            text="The",
            bbox=BoundingBox(x=0.1, y=0.1, width=0.1, height=0.04),
            confidence=0.95,
        ),
        OCRSpan(
            id="p1-s2",
            text="lnvoice",
            bbox=BoundingBox(x=0.22, y=0.1, width=0.2, height=0.04),
            confidence=0.5,
        ),
        OCRSpan(
            id="p1-s3",
            text="<script>alert(1)</script>",
            bbox=BoundingBox(x=0.1, y=0.2, width=0.3, height=0.04),
            confidence=0.8,
        ),
    ]
    page_one_blocks = [
        DocumentBlock(
            id="p1-b1",
            page_number=1,
            kind="heading",
            span_ids=["p1-s1", "p1-s2"],
            raw_text="The lnvoice",
            bbox=BoundingBox(x=0.1, y=0.1, width=0.32, height=0.04),
            confidence=0.7,
        ),
        DocumentBlock(
            id="p1-b2",
            page_number=1,
            kind="paragraph",
            span_ids=["p1-s3"],
            raw_text="<script>alert(1)</script>",
            bbox=BoundingBox(x=0.1, y=0.2, width=0.3, height=0.04),
            confidence=0.8,
        ),
    ]
    page_two_span = OCRSpan(
        id="p2-s1",
        text="Second page",
        bbox=BoundingBox(x=0.1, y=0.1, width=0.2, height=0.04),
        confidence=0.9,
    )
    page_two_block = DocumentBlock(
        id="p2-b1",
        page_number=2,
        kind="list_item",
        span_ids=["p2-s1"],
        raw_text="Second page",
        bbox=page_two_span.bbox,
        confidence=0.9,
    )
    return CanonicalDocument(
        schema_version="1.0",
        job_id="job-1",
        source_name="scan.pdf",
        pages=[
            DocumentPage(
                number=1,
                width=1000,
                height=1000,
                spans=page_one_spans,
                blocks=page_one_blocks,
            ),
            DocumentPage(
                number=2,
                width=1000,
                height=1000,
                spans=[page_two_span],
                blocks=[page_two_block],
            ),
        ],
        corrections=[
            CorrectionPatch(
                id="p-correct",
                block_id="p1-b1",
                span_ids=["p1-s2"],
                original_text="lnvoice",
                replacement_text="Invoice",
                rationale="OCR confusion",
                model_confidence=0.9,
                status="accepted",
            ),
            CorrectionPatch(
                id="p-reject",
                block_id="p1-b2",
                span_ids=["p1-s3"],
                original_text="<script>alert(1)</script>",
                replacement_text="safe",
                rationale="not accepted",
                model_confidence=0.8,
                status="rejected",
            ),
        ],
    )


def test_markdown_uses_accepted_text_and_layout() -> None:
    output = DIGITAL_EXPORTERS["markdown"].export(make_document()).decode()

    assert "## Page 1" in output
    assert "### The Invoice" in output
    assert "<script>alert(1)</script>" in output
    assert "safe" not in output
    assert "- Second page" in output


def test_html_escapes_untrusted_ocr_text() -> None:
    output = DIGITAL_EXPORTERS["html"].export(make_document()).decode()

    assert "<script>" not in output
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in output
    assert "<h3>The Invoice</h3>" in output
    assert "<li>Second page</li>" in output


def test_json_round_trips_and_docx_contains_text() -> None:
    document = make_document()
    json_bytes = DIGITAL_EXPORTERS["json"].export(document)
    assert CanonicalDocument.model_validate_json(json_bytes) == document

    docx_bytes = DIGITAL_EXPORTERS["docx"].export(document)
    assert len(docx_bytes) > 100
