# Model and evaluation card

## Components

- Tesseract OCR with the configured English language data.
- OpenCV preprocessing for grayscale, contrast, denoising, threshold selection, and bounded
  deskewing.
- Layout grouping based on OCR hierarchy, coordinates, line spacing, and confidence.
- Optional OpenAI-compatible or Gemini structured-output correction.

## Safeguards

The model receives only selected low-confidence or suspicious spans with local context. It returns
patches, not a replacement document. Unknown IDs, mismatched originals, excessive replacements,
invalid citations, and malformed provider responses are rejected. Raw OCR is never overwritten.

The default public result keeps corrections proposed until a user accepts them. A correction is
reversible and every export derives from the current canonical state.

## Evaluation limits

The checked-in corpus contains three synthetic, deterministic printed-page fixtures: clean,
skewed, and noisy. CER and WER are calculated after whitespace normalization. The corpus does not
represent handwriting, multilingual documents, tables with complex cell geometry, privacy-sensitive
records, or domain-specific terminology. Results should be read as an engineering regression
signal, not a general accuracy guarantee.

The checked-in container run measured raw OCR at 58.6% CER and 58.0% WER across the three fixtures.
The noisy invoice scored 100% on both metrics, which is intentionally visible in the dashboard:
the benchmark is a regression signal, not a marketing claim. No provider correction score is
published until a reviewed correction fixture is available.

## Non-goals

This project does not provide identity, legal, medical, financial, or archival guarantees. It does
not train a custom OCR model, build user accounts, or infer facts that cannot be cited to source
blocks.
