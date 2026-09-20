from backend.app.domain.document import (
    BoundingBox,
    CanonicalDocument,
    CorrectionPatch,
    CorrectionStatus,
    DocumentBlock,
    DocumentPage,
    OCRSpan,
)


def test_accepted_patch_changes_derived_text_without_mutating_raw_ocr():
    span = OCRSpan(
        id="p1-s1",
        text="lnvoice",
        bbox=BoundingBox(x=0.1, y=0.1, width=0.2, height=0.05),
        confidence=0.52,
    )
    block = DocumentBlock(
        id="p1-b1",
        page_number=1,
        kind="paragraph",
        span_ids=[span.id],
        raw_text=span.text,
        bbox=span.bbox,
        confidence=span.confidence,
    )
    patch = CorrectionPatch(
        id="c1",
        block_id=block.id,
        span_ids=[span.id],
        original_text="lnvoice",
        replacement_text="Invoice",
        rationale="Common OCR confusion between lowercase l and uppercase I.",
        model_confidence=0.98,
        status=CorrectionStatus.accepted,
    )
    document = CanonicalDocument(
        schema_version="1.0",
        job_id="job-1",
        source_name="sample.pdf",
        pages=[DocumentPage(number=1, width=1000, height=1400, spans=[span], blocks=[block])],
        corrections=[patch],
    )

    assert document.accepted_text_for_block("p1-b1") == "Invoice"
    assert document.pages[0].spans[0].text == "lnvoice"
