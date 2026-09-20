import pytest
from pydantic import ValidationError

from backend.app.domain.document import BoundingBox, OCRSpan


def test_bounding_box_must_fit_normalized_page_space():
    with pytest.raises(ValidationError):
        BoundingBox(x=0.8, y=0.1, width=0.3, height=0.2)


def test_ocr_confidence_is_normalized():
    span = OCRSpan(
        id="p1-s1",
        text="Invoice",
        bbox=BoundingBox(x=0.1, y=0.1, width=0.2, height=0.05),
        confidence=0.93,
    )
    assert span.confidence == 0.93


def test_document_rejects_unknown_correction_span():
    from backend.app.domain.document import (
        CanonicalDocument,
        CorrectionPatch,
        CorrectionStatus,
        DocumentBlock,
        DocumentPage,
    )

    span = OCRSpan(
        id="p1-s1",
        text="Invoice",
        bbox=BoundingBox(x=0.1, y=0.1, width=0.2, height=0.05),
        confidence=0.93,
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
        span_ids=["missing"],
        original_text="Invoice",
        replacement_text="Invoice",
        rationale="No change.",
        model_confidence=0.9,
        status=CorrectionStatus.proposed,
    )

    with pytest.raises(ValidationError, match="unknown span"):
        CanonicalDocument(
            schema_version="1.0",
            job_id="job-1",
            source_name="sample.pdf",
            pages=[DocumentPage(number=1, width=1000, height=1400, spans=[span], blocks=[block])],
            corrections=[patch],
        )
