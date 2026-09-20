# Scanned PDF Intelligence

Scanned PDF Intelligence is a portfolio-grade OCR and document-intelligence system for scanned
PDFs and images. It makes the pipeline observable: visitors can inspect preprocessing, raw OCR,
confidence bands, constrained AI corrections, source-cited report items, and downloadable
canonical exports.

## Why this project is interesting

The AI layer never receives permission to rewrite a document. It receives bounded, suspicious OCR
spans and must return schema-validated patches. Every patch keeps its source span IDs, original
text, rationale, confidence, and reversible status. Raw OCR remains immutable.

The demo supports:

- PDF, PNG, and JPEG ingestion with byte/page limits.
- Multi-stage rendering, preprocessing, Tesseract OCR, layout grouping, and progress events.
- Curated measurable samples with ground truth.
- OpenAI-compatible and Gemini adapters with structured-output contracts.
- Public hosted quota plus request-scoped BYOK.
- Accept/reject/reverse correction decisions.
- Markdown, HTML, canonical JSON, DOCX, and position-aware searchable PDF exports.
- Source-cited document intelligence with citation validation.
- CER/WER evaluation fixtures and deterministic provider-contract tests.
- A public evaluation panel with checked-in, container-measured raw OCR metrics.

## Run locally

Requirements: Python 3.11+, Node 22+, Tesseract OCR, and Redis. The reproducible topology is
easiest with Docker:

~~~powershell
Copy-Item .env.example .env
docker compose up --build
~~~

Open http://localhost:8000. Redis, API, worker, and cleanup run as separate services. Hosted AI
is disabled by default; uploads and sample OCR remain available.

For a split development workflow:

~~~powershell
uv sync --all-groups
npm --prefix frontend install
uv run uvicorn backend.app.main:app --reload
npm --prefix frontend run dev
~~~

The Vite dev server proxies /api to port 8000. Start Redis and an RQ worker before submitting a
job:

~~~powershell
uv run rq worker --url redis://localhost:6379/0 ocr
~~~

## Optional hosted AI and BYOK

To enable the server-side provider, set OCR_HOSTED_PROVIDER_ENABLED=true,
OCR_HOSTED_PROVIDER_BASE_URL, OCR_HOSTED_PROVIDER_MODEL, and OCR_HOSTED_PROVIDER_API_KEY in a
secret manager or local ignored .env. The API enforces the configured hosted quota per client and
time window.

Visitors may instead submit a Gemini or OpenAI-compatible key for one correction request. BYOK
keys are held only in request memory, sent in a provider header, never placed in Redis or a
workspace, and cleared from the browser after submission. Do not use the public demo for sensitive
documents.

## Evaluation

Run the deterministic evaluation tests and the baseline runner with synthetic fixtures:

~~~powershell
uv run pytest backend/tests/evaluation -v
uv run python -m evaluation.run --help
~~~

The corpus is intentionally small and legally safe. CER and WER are useful measurements, not
proof that every layout, language, handwriting style, or domain will perform well.
The same result is available from GET /api/v1/evaluation and is rendered in the home page
evaluation panel.

## Quality gates

~~~powershell
uv run ruff check backend evaluation
uv run mypy backend/app evaluation
uv run pytest -q
npm --prefix frontend run check:api
npm --prefix frontend run lint
npm --prefix frontend test -- --run
npm --prefix frontend run build
~~~

## Security and privacy

Uploads live under expiring per-job workspaces. Public API errors are stable and redacted; raw
provider response bodies and credentials are not recorded. Static serving is allow-listed to the
built frontend and adds a restrictive Content Security Policy. See
docs/privacy.md and docs/architecture.md.

If you find a security issue, please avoid filing a public issue containing credentials or document
content. Contact the project owner privately with reproduction steps.
