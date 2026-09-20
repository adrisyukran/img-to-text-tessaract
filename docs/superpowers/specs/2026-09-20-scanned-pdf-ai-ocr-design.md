# Scanned-PDF AI OCR Portfolio — Product and Technical Design

**Date:** 2026-09-20
**Status:** Approved direction
**Primary goal:** Turn the existing image-to-text demo into a polished, publicly usable AI-engineering portfolio project.

## 1. Product Positioning

The product is an observable document-intelligence pipeline for scanned PDFs. A visitor can upload a document or choose a bundled sample, watch the document move through preprocessing, OCR, confidence analysis, constrained AI correction, and document understanding, and then inspect every result.

The project should demonstrate more than calling an OCR library or language-model API. Its core engineering story is that AI corrections are measurable, attributable, and reversible. The interface must expose raw OCR, confidence data, proposed corrections, and before/after evaluation rather than presenting model output as unquestionable truth.

The first release targets printed, scanned PDFs. Clean screenshots and image files remain supported as a secondary input. Handwriting, camera capture, document chat, accounts, collaboration, billing, and indefinite cloud storage are outside the first release.

## 2. Users and Success Criteria

### Primary audiences

- Recruiters and engineering reviewers evaluating AI-engineering ability.
- Developers interested in OCR, document processing, and reliable LLM integration.
- General visitors who need to digitize a small scanned document.

### Product success

A first-time visitor can use a curated sample without an account or API key, understand the pipeline within one minute, and inspect a useful result. A visitor can also upload a supported PDF, subject to public-demo limits, or supply a provider API key for additional AI usage.

### Engineering success

- The system reports character error rate (CER), word error rate (WER), processing latency, and correction counts for a bundled evaluation corpus.
- AI corrections use structured outputs and are restricted to identified spans; raw OCR is never destroyed.
- Every summary claim and extracted entity links back to a page and source block.
- Hosted credentials never reach browser JavaScript or logs.
- Uploaded files and generated artifacts are automatically deleted after a short retention window.
- Unit, integration, evaluation, and browser tests cover the critical pipeline.

## 3. User Experience

### Entry experience

The home screen explains the pipeline in one concise sentence and presents two primary actions:

1. Try a sample document.
2. Upload a scanned PDF.

No account is required. The screen shows supported formats, page and file limits, privacy behavior, and remaining hosted-demo usage before upload.

### Processing workspace

After ingestion, the user enters a three-pane workspace:

- A page navigator and original-page preview.
- A reconstructed digital document with selectable blocks.
- An inspector for OCR confidence, AI corrections, source coordinates, and processing metadata.

A pipeline timeline reports the active stage and per-page progress. Processing may continue while already completed pages become inspectable.

### Result views

The workspace provides three views backed by the same canonical document model:

1. **Digital document:** Layout-aware headings, paragraphs, lists, and tables where confidence is sufficient. Users can compare raw OCR and corrected text, accept or reject individual correction patches, and export Markdown, HTML, JSON, or DOCX.
2. **Searchable PDF:** The original page images are retained and an invisible, position-aware text layer is added. The user can download the generated PDF and see whether its layer uses raw or accepted corrected text.
3. **Intelligence report:** A concise summary, key points, dates, people, organizations, and other useful entities. Every item carries page-level and block-level citations that navigate to the source.

### Evaluation showcase

A dedicated evaluation view runs against bundled, non-sensitive sample documents with ground truth. It compares raw OCR and AI-corrected results using CER and WER, shows latency and correction counts, and includes representative diffs. This view is central to the portfolio narrative, not hidden administrative tooling.

## 4. Architecture

### Repository shape

The repository becomes a small monorepo:

```text
frontend/                 React + TypeScript + Vite application
backend/                  FastAPI application and document pipeline
  app/api/                HTTP and server-sent-event endpoints
  app/core/               settings, security, logging, rate limits
  app/domain/             canonical document and correction models
  app/pipeline/           ingestion, preprocessing, OCR, correction, analysis
  app/providers/          hosted and BYOK model adapters
  app/exports/            Markdown, HTML, JSON, DOCX, searchable PDF
  tests/                  unit and integration tests
evaluation/               versioned sample corpus, ground truth, metrics
docs/                     architecture, setup, model card, privacy notes
```

The current static implementation remains available during migration until the new vertical slice replaces it. Production serves only explicit frontend assets and API routes; it never exposes the repository root.

### Runtime components

- **Frontend:** React, TypeScript, Vite, compiled styling, PDF.js for page preview, and server-sent events for job progress.
- **API:** FastAPI validates requests, creates jobs, exposes results, streams progress, mediates provider calls, and generates downloads.
- **Worker:** A separate Python worker processes CPU-intensive PDF rasterization and OCR. Redis backs the queue, job state, and hosted-demo rate limits.
- **Temporary artifacts:** Each job uses an isolated temporary workspace. Deployments may map this workspace to short-lived object storage, but the domain interface must not depend on a specific vendor.
- **AI providers:** A provider-neutral interface supports the hosted model and user-supplied keys. Keys supplied by users are request-scoped, held only in memory for the active job, redacted from telemetry, and never persisted.

### Canonical document model

The pipeline produces a versioned JSON document containing:

- Document and page metadata.
- Page dimensions and render parameters.
- Ordered blocks with type, text, polygon or bounding box, OCR confidence, and source page.
- Word or span-level raw OCR data.
- Proposed correction patches with original text, replacement text, rationale, model confidence, status, and affected span IDs.
- Accepted text computed from raw spans plus accepted patches.
- Intelligence-report items with citations to source blocks.

All result views and export formats consume this model. They must not independently reinterpret raw model responses.

## 5. Processing Pipeline

### Ingestion

The API accepts PDF, PNG, and JPEG uploads after validating content signatures, MIME type, size, page count, and encryption status. Filenames are treated as untrusted metadata. Public limits are configuration-driven and returned by a capabilities endpoint so the UI never hard-codes them.

### PDF rendering and image preprocessing

PyMuPDF renders pages at a controlled resolution. OpenCV preprocessing performs orientation detection, grayscale conversion, contrast normalization, deskewing, denoising, and optional adaptive thresholding. The pipeline records which transformations were applied and keeps preview images for before/after inspection.

### OCR and layout reconstruction

Tesseract runs server-side and returns TSV or hOCR data with text, coordinates, hierarchy, and confidence. A layout stage groups words into lines and blocks, classifies common block types using deterministic rules, and preserves reading order. Table reconstruction is best-effort in the first release and must visibly indicate low confidence rather than fabricate structure.

The OCR engine sits behind an interface so a second engine can be evaluated later without changing downstream components. Multi-engine comparison is not required for the first release.

### Constrained AI correction

The correction stage selects low-confidence or suspicious spans and sends them to the configured language model with neighboring context and stable span IDs. The model must return schema-validated patches, not a rewritten document. The service rejects patches that reference unknown spans, omit originals, exceed configured edit-distance or size boundaries, or fail schema validation.

Raw OCR remains immutable. Accepted text is derived by applying correction patches. The default public-demo result may auto-accept high-confidence patches while still allowing every patch to be inspected and reversed.

### Document intelligence

The report generator consumes accepted blocks in bounded chunks. It produces structured summaries and entities with required source block IDs. A validation stage removes unsupported citations and refuses uncited items. Long documents use a map-and-reduce strategy; the initial public limits keep inputs small enough for predictable cost and latency.

### Searchable PDF generation

The export service uses original page images and canonical block coordinates to place an invisible text layer. Text is drawn with appropriate scaling and page transforms. The export records whether it used raw OCR or accepted corrected text. Automated tests verify that text can be extracted from the generated PDF and that page counts and dimensions remain stable.

## 6. API Surface

The initial API is versioned under `/api/v1`:

- `GET /capabilities` — accepted formats, limits, enabled providers, and hosted quota status.
- `GET /samples` — bundled sample metadata.
- `POST /jobs` — create a document-processing job from an upload or sample ID.
- `GET /jobs/{job_id}` — state, stage, progress, errors, and artifact availability.
- `GET /jobs/{job_id}/events` — server-sent progress and page-completion events.
- `GET /jobs/{job_id}/document` — canonical document JSON.
- `PATCH /jobs/{job_id}/corrections/{patch_id}` — accept or reject a correction.
- `GET /jobs/{job_id}/exports/{format}` — generated Markdown, HTML, JSON, DOCX, or PDF.
- `DELETE /jobs/{job_id}` — immediately remove a job and its temporary artifacts.
- `GET /evaluation` — committed benchmark summary and per-sample results.
- `GET /health/live` and `GET /health/ready` — runtime health checks.

Errors use a stable problem-details format with a public code, readable message, retryability flag, and optional stage/page context.

## 7. Hosted Usage and BYOK

Anonymous hosted usage is deliberately small and enforced server-side using Redis. Limits cover requests, pages, document size, concurrent jobs, and model tokens. Rate-limit responses include the reset time. Browser storage may remember a non-secret visitor token for usability, but it is not the enforcement boundary.

BYOK users select a supported provider and submit a key over TLS for an individual processing job. The key is passed through an excluded, redacted request path and is never written to Redis, files, analytics, exception traces, or application logs. The UI clearly distinguishes locally computed OCR from text sent to an external model.

Curated sample results can be precomputed so the portfolio remains demonstrable when provider services are unavailable or the hosted quota is exhausted.

## 8. Reliability, Privacy, and Security

- Replace the current server behavior that logs and injects API credentials into HTML.
- Serve only allow-listed assets; never use the repository root as a static directory.
- Sanitize reconstructed HTML and model-generated text before rendering.
- Validate PDFs and process them in resource-limited worker jobs with timeouts.
- Reject encrypted, malformed, oversized, or excessive-page documents with actionable errors.
- Delete job data automatically after a configurable short TTL and allow immediate deletion.
- Use structured logs with job IDs, stages, timings, and redacted errors; never log document text by default.
- Add dependency scanning, secret scanning, static analysis, and locked dependency versions in continuous integration.
- Publish a concise privacy statement and an AI limitations/model card.

## 9. Testing and Evaluation

### Backend tests

- Unit tests for validation, preprocessing decisions, layout grouping, patch application, citations, rate limits, and exporters.
- Contract tests for AI providers using recorded or synthetic responses; CI never spends live model credits.
- Integration tests for the complete pipeline using small fixture PDFs.
- Property tests for correction patches so invalid ranges and IDs cannot corrupt canonical text.

### Frontend tests

- Component tests for uploads, progress, diff inspection, correction decisions, and errors.
- Browser tests for the sample-document happy path, upload limits, hosted quota exhaustion, BYOK entry, and export downloads.
- Accessibility checks for keyboard navigation, focus states, labels, contrast, and reduced motion.

### Evaluation

The repository contains a small, legally safe corpus with ground-truth text. The evaluation runner produces machine-readable and human-readable reports containing CER, WER, per-stage latency, model/token usage, correction precision on annotated spans where available, and regressions against a checked-in baseline. CI fails only on explicit regression thresholds to avoid noisy benchmark failures.

## 10. Delivery Scope

### First public release

- PDF/JPEG/PNG ingestion with strict public limits.
- Observable preprocessing and Tesseract OCR pipeline.
- Canonical page/block/span model with confidence.
- Structured, reversible AI correction.
- Faithful digital-document workspace.
- Searchable PDF generation.
- Cited summary and key-entity report.
- Hosted quota plus ephemeral BYOK.
- Curated samples and public evaluation dashboard.
- Containerized deployment, CI, documentation, and automated cleanup.

### Deferred work

- Handwriting-specific models.
- Full table reconstruction and spreadsheet export.
- Multi-user accounts, saved history, collaboration, or billing.
- General document chat or retrieval-augmented question answering.
- Native mobile or desktop applications.
- Training or fine-tuning a custom OCR model.

## 11. Rollout Strategy

Implementation proceeds as vertical slices. The first slice processes one bundled one-page sample through the new FastAPI pipeline and displays raw OCR, a constrained correction diff, and metrics in the new frontend. Later slices add uploads and multi-page jobs, exports, intelligence, quotas/BYOK, and production hardening. This order ensures the portfolio story is visible early and prevents infrastructure or design work from hiding an incomplete AI pipeline.
