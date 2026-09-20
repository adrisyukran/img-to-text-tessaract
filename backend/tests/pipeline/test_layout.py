from backend.app.domain.document import BoundingBox, OCRSpan
from backend.app.pipeline.layout import group_spans


def span(
    identifier: str,
    text: str,
    top: float,
    left: float,
    height: float = 0.03,
    line: int = 1,
) -> OCRSpan:
    return OCRSpan(
        id=identifier,
        text=text,
        bbox=BoundingBox(x=left, y=top, width=0.1, height=height),
        confidence=0.9,
        source={"block_num": 1, "par_num": 1, "line_num": line, "word_num": 1},
    )


def test_words_on_same_line_form_ordered_paragraph_block():
    blocks = group_spans(
        1,
        [
            span("p1-s1", "Invoice", 0.1, 0.1),
            span("p1-s2", "number", 0.1, 0.22, line=1),
            span("p1-s3", "2025", 0.16, 0.1, line=2),
        ],
    )

    assert len(blocks) == 1
    assert blocks[0].raw_text == "Invoice number 2025"
    assert blocks[0].kind == "paragraph"
    assert blocks[0].span_ids == ["p1-s1", "p1-s2", "p1-s3"]


def test_large_short_line_becomes_heading():
    blocks = group_spans(
        1,
        [
            span("p1-s1", "TITLE", 0.1, 0.1, height=0.08),
            span("p1-s2", "Body", 0.3, 0.1, height=0.03, line=2),
        ],
    )
    assert blocks[0].kind == "heading"
