from dataclasses import dataclass
from statistics import median

from backend.app.domain.document import BlockKind, BoundingBox, DocumentBlock, OCRSpan


@dataclass
class _Line:
    spans: list[OCRSpan]

    @property
    def top(self) -> float:
        return min(span.bbox.y for span in self.spans)

    @property
    def bottom(self) -> float:
        return max(span.bbox.y + span.bbox.height for span in self.spans)

    @property
    def left(self) -> float:
        return min(span.bbox.x for span in self.spans)

    @property
    def height(self) -> float:
        return max(span.bbox.height for span in self.spans)

    @property
    def text(self) -> str:
        return " ".join(span.text for span in self.spans)


def _line_for_span(spans: list[OCRSpan]) -> list[_Line]:
    grouped: dict[tuple[int, int, int], list[OCRSpan]] = {}
    for span in spans:
        key = (
            int(span.source.get("block_num", 0)),
            int(span.source.get("par_num", 0)),
            int(span.source.get("line_num", 0)),
        )
        grouped.setdefault(key, []).append(span)
    return [
        _Line(
            sorted(
                words,
                key=lambda item: (
                    int(item.source.get("word_num", 0)),
                    item.bbox.x,
                ),
            )
        )
        for words in grouped.values()
    ]


def _union(spans: list[OCRSpan]) -> BoundingBox:
    left = min(span.bbox.x for span in spans)
    top = min(span.bbox.y for span in spans)
    right = max(span.bbox.x + span.bbox.width for span in spans)
    bottom = max(span.bbox.y + span.bbox.height for span in spans)
    return BoundingBox(x=left, y=top, width=right - left, height=bottom - top)


def _weighted_confidence(spans: list[OCRSpan]) -> float:
    total = sum(len(span.text) for span in spans)
    return sum(len(span.text) * span.confidence for span in spans) / total


def _merge_lines(lines: list[_Line]) -> list[list[OCRSpan]]:
    ordered = sorted(lines, key=lambda line: (line.top, line.left))
    if not ordered:
        return []
    median_height = median(line.height for line in ordered)
    groups: list[list[_Line]] = [[ordered[0]]]
    for current in ordered[1:]:
        previous = groups[-1][-1]
        vertical_gap = current.top - previous.bottom
        aligned = abs(current.left - groups[-1][0].left) <= median_height * 2
        if vertical_gap <= median_height * 1.5 and aligned:
            groups[-1].append(current)
        else:
            groups.append([current])
    return [
        [
            span
            for line in group
            for span in sorted(line.spans, key=lambda item: (item.bbox.y, item.bbox.x))
        ]
        for group in groups
    ]


def group_spans(page_number: int, spans: list[OCRSpan]) -> list[DocumentBlock]:
    lines = _line_for_span(spans)
    merged = _merge_lines(lines)
    line_heights = [line.height for line in lines] or [0]
    typical_height = median(line_heights)
    blocks: list[DocumentBlock] = []
    for index, block_spans in enumerate(merged, start=1):
        block_lines = [
            line
            for line in lines
            if any(item.id in {span.id for span in block_spans} for item in line.spans)
        ]
        kind = BlockKind.paragraph
        if len(block_lines) == 1 and block_lines[0].height >= typical_height * 1.25:
            kind = BlockKind.heading
        if block_spans[0].text.startswith(("-", "•", "*")):
            kind = BlockKind.list_item
        blocks.append(
            DocumentBlock(
                id=f"p{page_number}-b{index:04d}",
                page_number=page_number,
                kind=kind,
                span_ids=[span.id for span in block_spans],
                raw_text=" ".join(span.text for span in block_spans),
                bbox=_union(block_spans),
                confidence=_weighted_confidence(block_spans),
            )
        )
    return blocks
