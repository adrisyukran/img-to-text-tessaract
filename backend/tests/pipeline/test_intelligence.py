import pytest

from backend.app.domain.document import (
    BoundingBox,
    CanonicalDocument,
    DocumentBlock,
    DocumentPage,
    OCRSpan,
)
from backend.app.pipeline.intelligence import (
    IntelligenceProblem,
    build_report_chunks,
    validate_report,
)


def make_document() -> CanonicalDocument:
    spans = [
        OCRSpan(
            id="p1-s1",
            text="Annual report",
            bbox=BoundingBox(x=0.1, y=0.1, width=0.3, height=0.04),
            confidence=0.9,
        ),
        OCRSpan(
            id="p1-s2",
            text="Revenue increased.",
            bbox=BoundingBox(x=0.1, y=0.2, width=0.3, height=0.04),
            confidence=0.9,
        ),
    ]
    blocks = [
        DocumentBlock(
            id="p1-b1",
            page_number=1,
            kind="heading",
            span_ids=["p1-s1"],
            raw_text="Annual report",
            bbox=spans[0].bbox,
            confidence=0.9,
        ),
        DocumentBlock(
            id="p1-b2",
            page_number=1,
            kind="paragraph",
            span_ids=["p1-s2"],
            raw_text="Revenue increased.",
            bbox=spans[1].bbox,
            confidence=0.9,
        ),
    ]
    return CanonicalDocument(
        schema_version="1.0",
        job_id="job-1",
        source_name="report.pdf",
        pages=[DocumentPage(number=1, width=100, height=100, spans=spans, blocks=blocks)],
    )


def test_chunks_keep_order_and_source_ids() -> None:
    chunks = build_report_chunks(make_document(), max_chars=20)

    assert [chunk.block_ids for chunk in chunks] == [["p1-b1"], ["p1-b2"]]
    assert "p1-b1" in chunks[0].text


def test_invalid_citations_are_dropped_and_uncited_summary_fails() -> None:
    document = make_document()
    report = {
        "summary": {
            "text": "Summary",
            "citations": [{"page_number": 1, "block_ids": ["missing"]}],
        },
        "key_points": [],
        "entities": [],
        "warnings": [],
    }
    with pytest.raises(IntelligenceProblem, match="uncited_report"):
        validate_report(document, report)
