from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from backend.app.domain.document import (
    CanonicalDocument,
    ExtractedEntity,
    IntelligenceItem,
    IntelligenceReport,
    ReportCitation,
)


class IntelligenceProblem(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class ReportChunk:
    page_number: int
    block_ids: list[str]
    text: str


def build_report_chunks(
    document: CanonicalDocument,
    max_chars: int = 6_000,
) -> list[ReportChunk]:
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    chunks: list[ReportChunk] = []
    current_page: int | None = None
    current_ids: list[str] = []
    current_parts: list[str] = []
    current_length = 0

    def flush() -> None:
        nonlocal current_page, current_ids, current_parts, current_length
        if current_parts and current_page is not None:
            chunks.append(ReportChunk(current_page, current_ids, "\n".join(current_parts)))
        current_page = None
        current_ids = []
        current_parts = []
        current_length = 0

    for page in document.pages:
        for block in page.blocks:
            text = document.accepted_text_for_block(block.id)
            labeled = f"[page={page.number} block={block.id}]\n{text}"
            if len(labeled) > max_chars:
                flush()
                words = text.split()
                part: list[str] = []
                part_length = 0
                for word in words:
                    if part and part_length + len(word) + 1 > max_chars:
                        chunks.append(
                            ReportChunk(
                                page.number,
                                [block.id],
                                f"[page={page.number} block={block.id}]\n{' '.join(part)}",
                            )
                        )
                        part = []
                        part_length = 0
                    part.append(word)
                    part_length += len(word) + (1 if part_length else 0)
                if part:
                    chunks.append(
                        ReportChunk(
                            page.number,
                            [block.id],
                            f"[page={page.number} block={block.id}]\n{' '.join(part)}",
                        )
                    )
                continue
            if current_parts and (
                current_length + len(labeled) + 1 > max_chars
                or current_page != page.number
            ):
                flush()
            current_page = page.number
            current_ids.append(block.id)
            current_parts.append(labeled)
            current_length += len(labeled) + 1
    flush()
    return chunks


def _citation_is_valid(
    citation: ReportCitation,
    blocks_by_page: dict[int, set[str]],
) -> bool:
    valid_blocks = blocks_by_page.get(citation.page_number)
    return valid_blocks is not None and all(
        block_id in valid_blocks for block_id in citation.block_ids
    )


def _valid_item(
    item: IntelligenceItem,
    blocks_by_page: dict[int, set[str]],
) -> IntelligenceItem | None:
    citations = [
        citation
        for citation in item.citations
        if _citation_is_valid(citation, blocks_by_page)
    ]
    return item.model_copy(update={"citations": citations}) if citations else None


def _valid_entity(
    entity: ExtractedEntity,
    blocks_by_page: dict[int, set[str]],
) -> ExtractedEntity | None:
    citations = [
        citation
        for citation in entity.citations
        if _citation_is_valid(citation, blocks_by_page)
    ]
    return entity.model_copy(update={"citations": citations}) if citations else None


def validate_report(
    document: CanonicalDocument,
    report: IntelligenceReport | dict[str, Any],
) -> IntelligenceReport:
    try:
        parsed = (
            report
            if isinstance(report, IntelligenceReport)
            else IntelligenceReport.model_validate(report)
        )
    except ValidationError as exc:
        raise IntelligenceProblem(
            "invalid_report",
            "The provider report failed schema validation.",
        ) from exc

    blocks_by_page = {
        page.number: {block.id for block in page.blocks}
        for page in document.pages
    }
    summary = _valid_item(parsed.summary, blocks_by_page)
    if summary is None:
        raise IntelligenceProblem("uncited_report", "The report summary has no valid citations.")

    key_points: list[IntelligenceItem] = []
    warnings = list(parsed.warnings)
    for item in parsed.key_points:
        valid = _valid_item(item, blocks_by_page)
        if valid is None:
            warnings.append("A key point was omitted because its citations were invalid.")
        else:
            key_points.append(valid)

    merged: dict[tuple[str, str], ExtractedEntity] = {}
    for entity in parsed.entities:
        valid_entity = _valid_entity(entity, blocks_by_page)
        if valid_entity is None:
            warnings.append("An entity was omitted because its citations were invalid.")
            continue
        key = (valid_entity.kind, valid_entity.value.casefold())
        if key in merged:
            citations = merged[key].citations + valid_entity.citations
            merged[key] = merged[key].model_copy(update={"citations": citations})
        else:
            merged[key] = valid_entity

    return IntelligenceReport(
        summary=summary,
        key_points=key_points,
        entities=list(merged.values()),
        warnings=warnings,
    )


def build_basic_report(document: CanonicalDocument) -> IntelligenceReport:
    blocks = [
        (page.number, block)
        for page in document.pages
        for block in page.blocks
        if document.accepted_text_for_block(block.id).strip()
    ]
    if not blocks:
        raise IntelligenceProblem("uncited_report", "No source text is available for a report.")
    first_page, first_block = blocks[0]
    summary = IntelligenceItem(
        text=document.accepted_text_for_block(first_block.id)[:500],
        citations=[ReportCitation(page_number=first_page, block_ids=[first_block.id])],
    )
    key_points = [
        IntelligenceItem(
            text=document.accepted_text_for_block(block.id)[:500],
            citations=[ReportCitation(page_number=page_number, block_ids=[block.id])],
        )
        for page_number, block in blocks[1:4]
    ]
    return validate_report(
        document,
        IntelligenceReport(summary=summary, key_points=key_points),
    )
