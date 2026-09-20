from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BlockKind(StrEnum):
    heading = "heading"
    paragraph = "paragraph"
    list_item = "list_item"
    table = "table"
    unknown = "unknown"


class CorrectionStatus(StrEnum):
    proposed = "proposed"
    accepted = "accepted"
    rejected = "rejected"


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(ge=0, le=1)
    height: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def fits_page(self) -> "BoundingBox":
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("bounding box must fit normalized page space")
        return self


class OCRSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    bbox: BoundingBox
    confidence: float = Field(ge=0, le=1)
    source: dict[str, int | str] = Field(default_factory=dict)


class DocumentBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    kind: BlockKind
    span_ids: list[str] = Field(min_length=1)
    raw_text: str
    bbox: BoundingBox
    confidence: float = Field(ge=0, le=1)


class DocumentPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    spans: list[OCRSpan]
    blocks: list[DocumentBlock]


class CorrectionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    block_id: str = Field(min_length=1)
    span_ids: list[str] = Field(min_length=1)
    original_text: str = Field(min_length=1)
    replacement_text: str = Field(min_length=1, max_length=120)
    rationale: str = Field(min_length=1, max_length=500)
    model_confidence: float = Field(ge=0, le=1)
    status: CorrectionStatus = CorrectionStatus.proposed


class ReportCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_number: int = Field(ge=1)
    block_ids: list[str] = Field(min_length=1)


class IntelligenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500)
    citations: list[ReportCitation] = Field(min_length=1)


class ExtractedEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["person", "organization", "date", "money", "location", "identifier"]
    value: str = Field(min_length=1, max_length=200)
    citations: list[ReportCitation] = Field(min_length=1)


class IntelligenceReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: IntelligenceItem
    key_points: list[IntelligenceItem] = Field(default_factory=list, max_length=8)
    entities: list[ExtractedEntity] = Field(default_factory=list, max_length=40)
    warnings: list[str] = Field(default_factory=list, max_length=20)


class CanonicalDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    job_id: str = Field(min_length=1)
    source_name: str = Field(min_length=1)
    pages: list[DocumentPage] = Field(min_length=1)
    corrections: list[CorrectionPatch] = Field(default_factory=list)
    report: IntelligenceReport | None = None

    @model_validator(mode="after")
    def validate_references(self) -> "CanonicalDocument":
        spans_by_id = {
            span.id: span
            for page in self.pages
            for span in page.spans
        }
        blocks_by_id = {
            block.id: block
            for page in self.pages
            for block in page.blocks
        }
        for patch in self.corrections:
            block = blocks_by_id.get(patch.block_id)
            if block is None:
                raise ValueError(f"correction references unknown block: {patch.block_id}")
            if any(span_id not in spans_by_id for span_id in patch.span_ids):
                raise ValueError(f"correction references unknown span: {patch.span_ids}")
            if any(span_id not in block.span_ids for span_id in patch.span_ids):
                raise ValueError("correction span is outside its block")
            selected = [
                block.span_ids.index(span_id)
                for span_id in patch.span_ids
            ]
            if selected != list(range(selected[0], selected[-1] + 1)):
                raise ValueError("correction spans must be contiguous")
            original = " ".join(spans_by_id[span_id].text for span_id in patch.span_ids)
            if original != patch.original_text:
                raise ValueError("correction original text does not match raw OCR")
        return self

    def accepted_text_for_block(self, block_id: str) -> str:
        block = next(
            (
                item
                for page in self.pages
                for item in page.blocks
                if item.id == block_id
            ),
            None,
        )
        if block is None:
            raise KeyError(block_id)
        spans_by_id = {
            span.id: span
            for page in self.pages
            for span in page.spans
        }
        values = [spans_by_id[span_id].text for span_id in block.span_ids]
        patches = [
            patch
            for patch in self.corrections
            if patch.block_id == block_id
            and patch.status is CorrectionStatus.accepted
        ]
        for patch in sorted(
            patches,
            key=lambda item: block.span_ids.index(item.span_ids[0]),
            reverse=True,
        ):
            start = block.span_ids.index(patch.span_ids[0])
            end = start + len(patch.span_ids)
            values[start:end] = [patch.replacement_text]
        return " ".join(values)
