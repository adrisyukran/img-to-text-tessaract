import pytest

from backend.app.domain.document import (
    BoundingBox,
    CanonicalDocument,
    CorrectionStatus,
    DocumentBlock,
    DocumentPage,
    OCRSpan,
)
from backend.app.pipeline.correction import (
    CorrectionProposal,
    apply_patch_status,
    select_candidates,
    validate_proposals,
)


def make_document() -> CanonicalDocument:
    spans = [
        OCRSpan(
            id="p1-s1",
            text="lnvoice",
            bbox=BoundingBox(x=0.1, y=0.1, width=0.1, height=0.03),
            confidence=0.52,
        ),
        OCRSpan(
            id="p1-s2",
            text="number",
            bbox=BoundingBox(x=0.22, y=0.1, width=0.1, height=0.03),
            confidence=0.96,
        ),
        OCRSpan(
            id="p1-s3",
            text="A1B2",
            bbox=BoundingBox(x=0.1, y=0.2, width=0.1, height=0.03),
            confidence=0.9,
        ),
    ]
    block = DocumentBlock(
        id="p1-b1",
        page_number=1,
        kind="paragraph",
        span_ids=[span.id for span in spans],
        raw_text="lnvoice number A1B2",
        bbox=BoundingBox(x=0.1, y=0.1, width=0.3, height=0.13),
        confidence=0.8,
    )
    return CanonicalDocument(
        schema_version="1.0",
        job_id="job-1",
        source_name="scan.pdf",
        pages=[DocumentPage(number=1, width=1000, height=1000, spans=spans, blocks=[block])],
    )


def test_candidate_selection_prefers_low_confidence_and_suspicious_tokens():
    candidates = select_candidates(make_document())
    assert [candidate.original_text for candidate in candidates] == ["lnvoice", "A1B2"]
    assert candidates[0].page_number == 1
    assert candidates[0].block_id == "p1-b1"


def test_valid_proposal_becomes_a_proposed_patch():
    document = make_document()
    candidate = select_candidates(document)[0]
    patches = validate_proposals(
        document,
        [candidate],
        [
            CorrectionProposal(
                candidate_id=candidate.id,
                original_text="lnvoice",
                replacement_text="Invoice",
                rationale="The low-confidence first character is a common OCR confusion.",
                confidence=0.98,
            )
        ],
    )
    assert len(patches) == 1
    assert patches[0].status is CorrectionStatus.proposed


def test_unknown_candidate_and_mismatched_original_are_rejected():
    document = make_document()
    candidate = select_candidates(document)[0]
    with pytest.raises(ValueError, match="unknown candidate"):
        validate_proposals(
            document,
            [candidate],
            [
                CorrectionProposal(
                    candidate_id="missing",
                    original_text="lnvoice",
                    replacement_text="Invoice",
                    rationale="reason",
                    confidence=0.9,
                )
            ],
        )
    with pytest.raises(ValueError, match="original text"):
        validate_proposals(
            document,
            [candidate],
            [
                CorrectionProposal(
                    candidate_id=candidate.id,
                    original_text="wrong",
                    replacement_text="Invoice",
                    rationale="reason",
                    confidence=0.9,
                )
            ],
        )


def test_patch_status_is_reversible_without_mutating_original():
    document = make_document()
    candidate = select_candidates(document)[0]
    patches = validate_proposals(
        document,
        [candidate],
        [
            CorrectionProposal(
                candidate_id=candidate.id,
                original_text="lnvoice",
                replacement_text="Invoice",
                rationale="reason",
                confidence=0.98,
            )
        ],
    )
    accepted = document.model_copy(update={"corrections": patches})
    rejected = apply_patch_status(accepted, patches[0].id, CorrectionStatus.rejected)
    assert accepted.accepted_text_for_block("p1-b1").startswith("lnvoice")
    assert rejected.accepted_text_for_block("p1-b1").startswith("lnvoice")
    assert rejected.corrections[0].status is CorrectionStatus.rejected
