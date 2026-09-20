import hashlib
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.app.domain.document import (
    CanonicalDocument,
    CorrectionPatch,
    CorrectionStatus,
)


class CorrectionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    block_id: str = Field(min_length=1)
    span_ids: list[str] = Field(min_length=1)
    original_text: str = Field(min_length=1)
    left_context: str
    right_context: str
    ocr_confidence: float = Field(ge=0, le=1)


class CorrectionProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1)
    original_text: str = Field(min_length=1)
    replacement_text: str = Field(min_length=1, max_length=120)
    rationale: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)


class CorrectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    candidates: list[dict[str, Any]]


def _candidate_id(document: CanonicalDocument, block_id: str, span_id: str, text: str) -> str:
    raw = f"{document.job_id}:{block_id}:{span_id}:{text}".encode()
    return "c-" + hashlib.sha256(raw).hexdigest()[:16]


def _suspicious_token(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text) and re.search(r"\d", text))


def select_candidates(document: CanonicalDocument) -> list[CorrectionCandidate]:
    spans_by_id = {
        span.id: span
        for page in document.pages
        for span in page.spans
    }
    candidates: list[CorrectionCandidate] = []
    for page in document.pages:
        for block in page.blocks:
            for position, span_id in enumerate(block.span_ids):
                span = spans_by_id[span_id]
                if span.confidence >= 0.8 and not _suspicious_token(span.text):
                    continue
                context_before = " ".join(
                    spans_by_id[item].text for item in block.span_ids[:position]
                )[-120:]
                context_after = " ".join(
                    spans_by_id[item].text for item in block.span_ids[position + 1 :]
                )[:120]
                candidates.append(
                    CorrectionCandidate(
                        id=_candidate_id(document, block.id, span.id, span.text),
                        page_number=page.number,
                        block_id=block.id,
                        span_ids=[span.id],
                        original_text=span.text,
                        left_context=context_before,
                        right_context=context_after,
                        ocr_confidence=span.confidence,
                    )
                )
    return candidates


def validate_proposals(
    document: CanonicalDocument,
    candidates: list[CorrectionCandidate],
    proposals: list[CorrectionProposal],
) -> list[CorrectionPatch]:
    candidates_by_id = {candidate.id: candidate for candidate in candidates}
    patches: list[CorrectionPatch] = []
    for proposal in proposals:
        candidate = candidates_by_id.get(proposal.candidate_id)
        if candidate is None:
            raise ValueError(f"unknown candidate: {proposal.candidate_id}")
        if proposal.original_text != candidate.original_text:
            raise ValueError("correction original text does not match candidate")
        if proposal.replacement_text.strip() == "":
            raise ValueError("correction replacement text cannot be empty")
        if len(proposal.replacement_text) > max(120, len(proposal.original_text) * 3):
            raise ValueError("correction replacement is too long")
        patch_id = "p-" + hashlib.sha256(
            f"{document.job_id}:{proposal.candidate_id}:{proposal.replacement_text}".encode()
        ).hexdigest()[:16]
        patches.append(
            CorrectionPatch(
                id=patch_id,
                block_id=candidate.block_id,
                span_ids=candidate.span_ids,
                original_text=proposal.original_text,
                replacement_text=proposal.replacement_text,
                rationale=proposal.rationale,
                model_confidence=proposal.confidence,
                status=CorrectionStatus.proposed,
            )
        )
    return patches


def apply_patch_status(
    document: CanonicalDocument,
    patch_id: str,
    status: CorrectionStatus,
) -> CanonicalDocument:
    if not any(patch.id == patch_id for patch in document.corrections):
        raise ValueError(f"unknown patch: {patch_id}")
    corrections = [
        patch.model_copy(update={"status": status}) if patch.id == patch_id else patch
        for patch in document.corrections
    ]
    updated = document.model_copy(update={"corrections": corrections})
    return CanonicalDocument.model_validate(updated)
