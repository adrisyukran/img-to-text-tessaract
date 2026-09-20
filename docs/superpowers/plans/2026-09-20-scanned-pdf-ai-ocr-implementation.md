# Scanned-PDF AI OCR Portfolio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (\`- [ ]\`) syntax for tracking.

**Goal:** Build a polished public portfolio application that turns scanned PDFs into an inspectable digital document, a searchable PDF, and a cited intelligence report through a measurable and reversible AI pipeline.

**Architecture:** A React/TypeScript frontend talks to a versioned FastAPI API. Redis stores short-lived job state, hosted-demo quotas, and an RQ work queue; a Python worker renders and preprocesses pages, runs Tesseract, applies schema-validated AI correction patches, generates intelligence results, and creates exports from one canonical document model. Uploaded files and artifacts live in isolated, expiring job workspaces, while BYOK credentials remain request-scoped and never enter Redis or disk.

**Tech Stack:** Python 3.12, FastAPI, Pydantic 2, Redis, RQ, PyMuPDF, OpenCV, pytesseract/Tesseract, httpx, python-docx, pytest, Hypothesis, React 19, TypeScript, Vite, TanStack Query, PDF.js, Vitest, Testing Library, MSW, Playwright, Docker Compose, GitHub Actions.

## Global Constraints

- Optimize the first release for printed scanned PDFs; keep PNG and JPEG as secondary inputs and defer handwriting-specific models.
- Require no account for sample documents or limited anonymous hosted processing.
- Generate the digital document, searchable PDF, and intelligence report from one versioned canonical document model.
- Keep raw OCR immutable; represent every AI edit as a schema-validated, attributable, reversible correction patch.
- Require page-level and block-level source citations for every intelligence-report item.
- Keep hosted provider credentials on the server and keep BYOK credentials only in memory for the active AI request.
- Never persist or log BYOK credentials or document text; redact provider errors before recording them.
- Enforce hosted-demo request, page, size, concurrency, and token limits on the server through Redis.
- Delete uploads and generated artifacts after a short configurable TTL and support immediate user deletion.
- Use curated precomputed samples so the portfolio remains usable without provider availability or hosted quota.
- Treat PDF filenames, PDF contents, OCR text, and model output as untrusted input.
- Add no accounts, saved cloud history, collaboration, billing, document chat, or custom-model training in this release.
- Follow test-driven development: add a failing focused test, observe the expected failure, implement the minimum behavior, rerun the focused test, then run the affected suite.
- After every API route or response-model change, regenerate **frontend/openapi.json** and **frontend/src/api/generated.ts**, run the contract drift check, and commit both generated files.
- Keep the current static app intact until the new sample-document vertical slice is functional; remove it only after end-to-end replacement coverage passes.

---

## Delivery Milestones

1. **Observable vertical slice:** One bundled page reaches preprocessing, OCR, constrained correction, and metric display through the new API and frontend.
2. **Usable document workspace:** Anonymous visitors can upload a bounded multi-page PDF, follow progress, inspect pages and corrections, and export the digital document.
3. **Three complete outputs:** Searchable PDF and cited intelligence report use the same canonical model as the digital document.
4. **Public portfolio release:** Hosted quotas, ephemeral BYOK, evaluation dashboard, accessibility, security checks, containers, CI, documentation, and cleanup are complete.

## Planned File Structure

### Backend

- **pyproject.toml** — Python metadata, runtime dependencies, test/lint configuration.
- **backend/app/main.py** — FastAPI application factory, middleware, router registration, frontend mounting.
- **backend/app/core/config.py** — environment-backed settings and public capabilities.
- **backend/app/core/logging.py** — structured logging and secret/text redaction.
- **backend/app/core/rate_limit.py** — Redis-backed anonymous hosted quota enforcement.
- **backend/app/domain/document.py** — canonical page, block, span, correction, and report models.
- **backend/app/domain/jobs.py** — job stage, progress, artifact, and API response models.
- **backend/app/api/health.py** — liveness and readiness routes.
- **backend/app/api/capabilities.py** — limits, enabled providers, and quota-status route.
- **backend/app/api/samples.py** — curated sample catalog.
- **backend/app/api/jobs.py** — create, inspect, stream, mutate, export, and delete job routes.
- **backend/app/ingestion/validation.py** — signature, MIME, size, page-count, and encryption checks.
- **backend/app/ingestion/samples.py** — versioned sample manifest loader.
- **backend/app/storage/workspaces.py** — isolated paths, safe writes, artifact lookup, and deletion.
- **backend/app/storage/job_repository.py** — short-lived job/document state in Redis.
- **backend/app/pipeline/render.py** — bounded PDF and image rendering.
- **backend/app/pipeline/preprocess.py** — orientation, contrast, deskew, denoise, and threshold transforms.
- **backend/app/pipeline/ocr.py** — OCR engine protocol and Tesseract adapter.
- **backend/app/pipeline/layout.py** — deterministic reading order and block grouping.
- **backend/app/pipeline/correction.py** — candidate selection, patch validation, and patch application.
- **backend/app/pipeline/intelligence.py** — chunked summaries/entities with citation validation.
- **backend/app/pipeline/orchestrator.py** — stage sequencing and progress persistence.
- **backend/app/providers/base.py** — model-provider protocols and request/response contracts.
- **backend/app/providers/openai_compatible.py** — hosted/OpenAI-compatible structured-output adapter.
- **backend/app/providers/gemini.py** — Gemini BYOK structured-output adapter.
- **backend/app/exports/digital.py** — Markdown, HTML, JSON, and DOCX exports.
- **backend/app/exports/searchable_pdf.py** — invisible text-layer PDF export.
- **backend/app/worker.py** — RQ worker entrypoint and hosted processing function.
- **backend/tests/** — focused unit, integration, contract, security, and pipeline tests.

### Frontend

- **frontend/src/app/App.tsx** — routes and top-level query/error boundaries.
- **frontend/src/api/client.ts** — typed HTTP transport and problem-details errors.
- **frontend/src/api/generated.ts** — generated OpenAPI types.
- **frontend/src/features/home/** — portfolio introduction, sample picker, upload entry.
- **frontend/src/features/jobs/** — job creation, progress stream, retry, and deletion.
- **frontend/src/features/document/** — page viewer, reconstructed blocks, confidence overlays.
- **frontend/src/features/corrections/** — correction list, diff inspector, accept/reject controls.
- **frontend/src/features/report/** — cited summary and entity views.
- **frontend/src/features/evaluation/** — benchmark cards, tables, and representative diffs.
- **frontend/src/features/exports/** — download controls and artifact-state handling.
- **frontend/src/styles/** — design tokens, layout, components, responsive and reduced-motion rules.
- **frontend/tests/** — MSW handlers, fixtures, component tests, and browser tests.

### Evaluation and operations

- **evaluation/generate_corpus.py** — deterministic generation of legally safe scanned fixtures.
- **evaluation/corpus/manifest.json** — fixture metadata and ground-truth locations.
- **evaluation/ground_truth/** — exact text for CER/WER calculation.
- **evaluation/run.py** — reproducible benchmark runner.
- **evaluation/baseline.json** — reviewed regression baseline.
- **docker/Dockerfile** — shared API/worker image plus built frontend.
- **docker/entrypoint.sh** — explicit API or worker startup.
- **compose.yaml** — local API, worker, and Redis topology with a shared expiring workspace.
- **.github/workflows/ci.yml** — backend, frontend, end-to-end, evaluation, dependency, and secret checks.
- **docs/architecture.md** — data flow and component boundaries.
- **docs/model-card.md** — model behavior, evaluation, limitations, and safeguards.
- **docs/privacy.md** — uploads, provider data flow, retention, and BYOK behavior.

---

### Task 1: Establish the FastAPI foundation and health contract

**Files:**
- Create: **pyproject.toml**
- Create: **backend/app/__init__.py**
- Create: **backend/app/main.py**
- Create: **backend/app/core/__init__.py**
- Create: **backend/app/core/config.py**
- Create: **backend/app/api/__init__.py**
- Create: **backend/app/api/health.py**
- Create: **backend/tests/conftest.py**
- Create: **backend/tests/api/test_health.py**

**Interfaces:**
- Consumes: Environment variables prefixed with **OCR_**.
- Produces: **Settings**, **create_app(settings: Settings | None = None) -> FastAPI**, **GET /api/v1/health/live**, and **GET /api/v1/health/ready**.

- [ ] **Step 1: Initialize the locked Python project**

Run:

~~~powershell
uv init --bare --python 3.12
uv add "fastapi" "uvicorn[standard]" "pydantic-settings"
uv add --dev pytest pytest-asyncio httpx ruff mypy
~~~

Add this tool configuration to **pyproject.toml**:

~~~toml
[tool.pytest.ini_options]
testpaths = ["backend/tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
~~~

- [ ] **Step 2: Write the failing health-route tests**

Create **backend/tests/conftest.py**:

~~~python
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app


@pytest.fixture
def settings(tmp_path):
    return Settings(
        environment="test",
        redis_url="redis://localhost:6379/15",
        workspace_root=tmp_path,
        hosted_provider_enabled=False,
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client
~~~

Create **backend/tests/api/test_health.py**:

~~~python
def test_liveness_is_process_only(client):
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_environment(client):
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "environment": "test"}
~~~

- [ ] **Step 3: Run the focused test and observe the missing modules**

Run: **uv run pytest backend/tests/api/test_health.py -v**

Expected: collection fails because **backend.app.core.config** and **backend.app.main** do not exist.

- [ ] **Step 4: Implement settings and health routes**

Create **backend/app/core/config.py**:

~~~python
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OCR_",
        env_file=".env",
        extra="ignore",
    )

    environment: str = "development"
    redis_url: str = "redis://localhost:6379/0"
    workspace_root: Path = Path(".data/jobs")
    artifact_ttl_seconds: int = Field(default=3600, ge=300, le=86400)
    max_upload_bytes: int = Field(default=15_000_000, ge=1_000_000)
    max_pdf_pages: int = Field(default=12, ge=1, le=50)
    hosted_provider_enabled: bool = False
    hosted_provider_base_url: str | None = None
    hosted_provider_model: str | None = None
    hosted_provider_api_key: str | None = Field(default=None, repr=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
~~~

Create **backend/app/api/health.py**:

~~~python
from fastapi import APIRouter, Request

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(request: Request) -> dict[str, str]:
    return {
        "status": "ready",
        "environment": request.app.state.settings.environment,
    }
~~~

Create **backend/app/main.py**:

~~~python
from fastapi import FastAPI

from backend.app.api.health import router as health_router
from backend.app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    app = FastAPI(title="Scanned PDF Intelligence API", version="1.0.0")
    app.state.settings = resolved
    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()
~~~

Add empty **__init__.py** files in the declared package directories.

- [ ] **Step 5: Verify the backend foundation**

Run:

~~~powershell
uv run pytest backend/tests/api/test_health.py -v
uv run ruff check backend
uv run mypy backend/app
~~~

Expected: two passing tests and no lint or type errors.

- [ ] **Step 6: Commit the foundation**

~~~powershell
git add pyproject.toml uv.lock backend
git commit -m "build: establish FastAPI application foundation"
~~~

---

### Task 2: Establish the React shell and API status boundary

**Files:**
- Create: **frontend/package.json**
- Create: **frontend/vite.config.ts**
- Create: **frontend/tsconfig.json**
- Create: **frontend/index.html**
- Create: **frontend/src/main.tsx**
- Create: **frontend/src/app/App.tsx**
- Create: **frontend/src/api/client.ts**
- Create: **frontend/src/styles/tokens.css**
- Create: **frontend/src/styles/global.css**
- Create: **frontend/src/app/App.test.tsx**
- Create: **frontend/src/test/setup.ts**

**Interfaces:**
- Consumes: **GET /api/v1/health/ready** from Task 1.
- Produces: **api.get<T>(path: string): Promise<T>**, a responsive application shell, and a tested API availability indicator.

- [ ] **Step 1: Scaffold Vite and install focused dependencies**

Run:

~~~powershell
npm create vite@latest frontend -- --template react-ts
Set-Location frontend
npm install @tanstack/react-query react-router-dom
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event msw
Set-Location ..
~~~

Replace Vite's generated sample assets and component code rather than retaining demo branding.

- [ ] **Step 2: Configure browser tests**

Add these settings in **frontend/vite.config.ts**:

~~~typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:8000" },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
});
~~~

Create **frontend/src/test/setup.ts**:

~~~typescript
import "@testing-library/jest-dom/vitest";
~~~

- [ ] **Step 3: Write the failing shell test**

Create **frontend/src/app/App.test.tsx**:

~~~tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { App } from "./App";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn().mockResolvedValue({ status: "ready", environment: "test" }),
  },
}));

test("explains the document pipeline and reports API readiness", async () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  );

  expect(
    screen.getByRole("heading", { name: /turn scanned pages into trustworthy text/i }),
  ).toBeInTheDocument();
  expect(await screen.findByText(/processing service online/i)).toBeInTheDocument();
});
~~~

- [ ] **Step 4: Run the frontend test and observe the missing shell**

Run: **npm --prefix frontend test -- --run src/app/App.test.tsx**

Expected: FAIL because the application shell and API client contract do not exist.

- [ ] **Step 5: Implement the API client and shell**

Create **frontend/src/api/client.ts**:

~~~typescript
export class ApiProblem extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch("/api/v1" + path, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => ({
      detail: "The processing service could not complete the request.",
      code: "unexpected_error",
    }));
    throw new ApiProblem(problem.detail, response.status, problem.code);
  }
  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, init?: RequestInit) =>
    request<T>(path, { ...init, method: "POST" }),
  patch: <T>(path: string, init?: RequestInit) =>
    request<T>(path, { ...init, method: "PATCH" }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
~~~

Implement **frontend/src/app/App.tsx** with a TanStack Query for **/health/ready**, a single H1 using the tested wording, a short three-stage explanation, and an **aria-live="polite"** status reading “Processing service online” after success. Keep the component under 100 lines; place typography, spacing, focus, background, and light/dark design tokens in **tokens.css** and **global.css**.

- [ ] **Step 6: Verify type checks and the focused UI test**

Run:

~~~powershell
npm --prefix frontend test -- --run src/app/App.test.tsx
npm --prefix frontend run build
~~~

Expected: one passing test and a successful production build.

- [ ] **Step 7: Commit the frontend shell**

~~~powershell
git add frontend
git commit -m "feat: add typed portfolio application shell"
~~~

---

### Task 3: Define the canonical document and correction model

**Files:**
- Create: **backend/app/domain/__init__.py**
- Create: **backend/app/domain/document.py**
- Create: **backend/tests/domain/test_document.py**
- Create: **backend/tests/domain/test_corrections.py**

**Interfaces:**
- Consumes: Pydantic 2.
- Produces: **BoundingBox**, **OCRSpan**, **DocumentBlock**, **DocumentPage**, **CorrectionPatch**, **ReportCitation**, **IntelligenceItem**, **IntelligenceReport**, **CanonicalDocument**, and **CanonicalDocument.accepted_text_for_block(block_id: str) -> str**.

- [ ] **Step 1: Write model-invariant tests**

Create **backend/tests/domain/test_document.py**:

~~~python
import pytest
from pydantic import ValidationError

from backend.app.domain.document import BoundingBox, OCRSpan


def test_bounding_box_must_fit_normalized_page_space():
    with pytest.raises(ValidationError):
        BoundingBox(x=0.8, y=0.1, width=0.3, height=0.2)


def test_ocr_confidence_is_normalized():
    span = OCRSpan(
        id="p1-s1",
        text="Invoice",
        bbox=BoundingBox(x=0.1, y=0.1, width=0.2, height=0.05),
        confidence=0.93,
    )
    assert span.confidence == 0.93
~~~

Create **backend/tests/domain/test_corrections.py**:

~~~python
from backend.app.domain.document import (
    BoundingBox,
    CanonicalDocument,
    CorrectionPatch,
    CorrectionStatus,
    DocumentBlock,
    DocumentPage,
    OCRSpan,
)


def test_accepted_patch_changes_derived_text_without_mutating_raw_ocr():
    span = OCRSpan(
        id="p1-s1",
        text="lnvoice",
        bbox=BoundingBox(x=0.1, y=0.1, width=0.2, height=0.05),
        confidence=0.52,
    )
    block = DocumentBlock(
        id="p1-b1",
        page_number=1,
        kind="paragraph",
        span_ids=[span.id],
        raw_text=span.text,
        bbox=span.bbox,
        confidence=span.confidence,
    )
    patch = CorrectionPatch(
        id="c1",
        block_id=block.id,
        span_ids=[span.id],
        original_text="lnvoice",
        replacement_text="Invoice",
        rationale="Common OCR confusion between lowercase l and uppercase I.",
        model_confidence=0.98,
        status=CorrectionStatus.accepted,
    )
    document = CanonicalDocument(
        schema_version="1.0",
        job_id="job-1",
        source_name="sample.pdf",
        pages=[DocumentPage(number=1, width=1000, height=1400, spans=[span], blocks=[block])],
        corrections=[patch],
    )

    assert document.accepted_text_for_block("p1-b1") == "Invoice"
    assert document.pages[0].spans[0].text == "lnvoice"
~~~

- [ ] **Step 2: Run tests and observe missing domain types**

Run: **uv run pytest backend/tests/domain -v**

Expected: collection fails because **backend.app.domain.document** does not exist.

- [ ] **Step 3: Implement immutable OCR types and correction-derived text**

Create enums **BlockKind** with values **heading**, **paragraph**, **list_item**, **table**, and **unknown**, plus **CorrectionStatus** with **proposed**, **accepted**, and **rejected**. Use Pydantic models with **extra="forbid"** and validated confidence values from 0 through 1.

Implement **BoundingBox** with normalized **x**, **y**, **width**, and **height** and a model validator requiring **x + width <= 1** and **y + height <= 1**.

Implement **CanonicalDocument.accepted_text_for_block** by:

1. Finding the block or raising **KeyError(block_id)**.
2. Starting from the block's ordered spans and their immutable **text** values.
3. Replacing only exact contiguous **span_ids** for patches whose status is **accepted**.
4. Joining spans with one space and never assigning back to a span or block.

Define **ReportCitation**, **IntelligenceItem**, **ExtractedEntity**, and **IntelligenceReport** with the exact strict shapes repeated in Task 14. Task 3 establishes the canonical serialization contract; Task 14 adds generation and source validation behavior without changing those field names.

Use this signature:

~~~python
class CanonicalDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    job_id: str
    source_name: str
    pages: list[DocumentPage]
    corrections: list[CorrectionPatch] = Field(default_factory=list)
    report: IntelligenceReport | None = None

    def accepted_text_for_block(self, block_id: str) -> str:
        block = next(
            (
                block
                for page in self.pages
                for block in page.blocks
                if block.id == block_id
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
~~~

The method body must implement the four rules above exactly.

- [ ] **Step 4: Add property coverage for corrupt patch references**

Add Hypothesis:

~~~powershell
uv add --dev hypothesis
~~~

Add a test generating unknown span IDs and assert that document validation rejects a correction whose **span_ids** are not all present in its **block_id**. Implement this as a **model_validator(mode="after")** on **CanonicalDocument** so corrupt documents cannot cross API or storage boundaries.

- [ ] **Step 5: Verify the domain suite and static checks**

Run:

~~~powershell
uv run pytest backend/tests/domain -v
uv run ruff check backend/app/domain backend/tests/domain
uv run mypy backend/app/domain
~~~

Expected: all document and correction tests pass with no lint or type errors.

- [ ] **Step 6: Commit the canonical model**

~~~powershell
git add pyproject.toml uv.lock backend/app/domain backend/tests/domain
git commit -m "feat: define immutable canonical document model"
~~~

---

### Task 4: Add isolated job workspaces and strict document ingestion

**Files:**
- Create: **backend/app/ingestion/__init__.py**
- Create: **backend/app/ingestion/validation.py**
- Create: **backend/app/storage/__init__.py**
- Create: **backend/app/storage/workspaces.py**
- Create: **backend/tests/ingestion/test_validation.py**
- Create: **backend/tests/storage/test_workspaces.py**

**Interfaces:**
- Consumes: **Settings.max_upload_bytes**, **Settings.max_pdf_pages**, and **Settings.workspace_root**.
- Produces: **UploadLimits**, **ValidatedUpload**, **UploadProblem**, **validate_upload(content: bytes, filename: str, declared_type: str, limits: UploadLimits) -> ValidatedUpload**, and **JobWorkspace.create(root: Path, job_id: str) -> JobWorkspace**.

- [ ] **Step 1: Install parsing dependencies**

Run:

~~~powershell
uv add pymupdf pillow
~~~

- [ ] **Step 2: Write failing validation tests**

Create tests proving:

- A PDF beginning with **%PDF-** and containing one readable page is accepted even when the browser reports **application/octet-stream**.
- A file named **report.pdf** containing PNG bytes is classified by content as PNG.
- A payload over **max_upload_bytes** raises **UploadProblem(code="file_too_large")** before parsing.
- An encrypted PDF raises **UploadProblem(code="encrypted_pdf")**.
- A PDF over **max_pdf_pages** raises **UploadProblem(code="page_limit_exceeded")**.
- Random bytes raise **UploadProblem(code="unsupported_file")**.
- The returned **safe_name** contains no directory separators or control characters.

Use in-memory PDFs generated with **fitz.open()**, **new_page()**, and **tobytes()**; do not add opaque test binaries for these unit cases.

- [ ] **Step 3: Run validation tests and observe missing implementation**

Run: **uv run pytest backend/tests/ingestion/test_validation.py -v**

Expected: collection fails because the ingestion module does not exist.

- [ ] **Step 4: Implement signature-first validation**

Implement these exact contracts:

~~~python
@dataclass(frozen=True)
class UploadLimits:
    max_bytes: int
    max_pages: int


@dataclass(frozen=True)
class ValidatedUpload:
    media_type: Literal["application/pdf", "image/png", "image/jpeg"]
    safe_name: str
    page_count: int
    content: bytes


class UploadProblem(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(detail)
~~~

Classify by magic bytes: **%PDF-**, PNG's eight-byte signature, and JPEG's leading **FF D8 FF**. Use PyMuPDF to open PDFs from bytes, reject **needs_pass**, and read **page_count** without rendering. Use Pillow **Image.verify()** for images and normalize extensions to **.pdf**, **.png**, or **.jpg**. Replace filename characters outside **[A-Za-z0-9._-]** with underscores and use **document** if the stem becomes empty.

- [ ] **Step 5: Write failing workspace-containment tests**

Test that:

- **JobWorkspace.create(tmp_path, "01ABC")** creates **tmp_path/01ABC/input**, **pages**, **artifacts**, and **state**.
- **workspace.write_input("../escape.pdf", content)** writes a sanitized basename inside **input**.
- **workspace.artifact_path("../../secret", "result.pdf")** raises **ValueError** for an unsupported artifact key.
- **workspace.delete()** removes only the resolved job directory and leaves a sibling directory untouched.

- [ ] **Step 6: Implement contained workspaces**

Use a fixed artifact-key mapping:

~~~python
ARTIFACT_NAMES = {
    "document_json": "document.json",
    "document_markdown": "document.md",
    "document_html": "document.html",
    "document_docx": "document.docx",
    "searchable_pdf": "searchable.pdf",
    "report_json": "report.json",
}
~~~

Resolve the root and candidate paths before writes or deletion and require **candidate.is_relative_to(root.resolve())**. Never accept a path fragment from a request. Open uploads with exclusive creation mode **xb** to prevent replacement.

- [ ] **Step 7: Verify ingestion and storage**

Run:

~~~powershell
uv run pytest backend/tests/ingestion backend/tests/storage -v
uv run ruff check backend/app/ingestion backend/app/storage
uv run mypy backend/app/ingestion backend/app/storage
~~~

Expected: all validation and containment tests pass.

- [ ] **Step 8: Commit secure ingestion**

~~~powershell
git add pyproject.toml uv.lock backend/app/ingestion backend/app/storage backend/tests/ingestion backend/tests/storage
git commit -m "feat: validate uploads in isolated job workspaces"
~~~

---

### Task 5: Render and preprocess pages with recorded transformations

**Files:**
- Create: **backend/app/pipeline/__init__.py**
- Create: **backend/app/pipeline/render.py**
- Create: **backend/app/pipeline/preprocess.py**
- Create: **backend/tests/pipeline/test_render.py**
- Create: **backend/tests/pipeline/test_preprocess.py**
- Create: **backend/tests/fixtures/images.py**

**Interfaces:**
- Consumes: **ValidatedUpload** and a **JobWorkspace**.
- Produces: **RenderedPage**, **PreprocessMetadata**, **PreprocessedPage**, **render_pages(upload: ValidatedUpload, workspace: JobWorkspace, dpi: int = 240) -> list[RenderedPage]**, and **preprocess_page(page: RenderedPage, output_dir: Path) -> PreprocessedPage**.

- [ ] **Step 1: Install image-processing dependencies**

Run:

~~~powershell
uv add numpy opencv-python-headless
~~~

- [ ] **Step 2: Write failing bounded-render tests**

Create a two-page in-memory PDF with different page sizes and assert:

- **render_pages** returns page numbers 1 and 2 in order.
- Each rendered PNG exists under **workspace/pages**.
- Pixel dimensions reflect 240 DPI within one pixel of the PyMuPDF matrix calculation.
- **RenderedPage.width_points** and **height_points** preserve PDF page dimensions.
- A PNG input becomes exactly one **RenderedPage** without lossy JPEG conversion.

Use this public type:

~~~python
@dataclass(frozen=True)
class RenderedPage:
    page_number: int
    image_path: Path
    pixel_width: int
    pixel_height: int
    width_points: float
    height_points: float
~~~

- [ ] **Step 3: Run render tests and observe the missing renderer**

Run: **uv run pytest backend/tests/pipeline/test_render.py -v**

Expected: collection fails because **backend.app.pipeline.render** does not exist.

- [ ] **Step 4: Implement controlled rendering**

For PDFs, open **ValidatedUpload.content** with PyMuPDF, build **fitz.Matrix(dpi / 72, dpi / 72)**, disable alpha, and save each page as **page-0001-original.png**. For images, decode with Pillow, apply EXIF orientation, convert to RGB, and save losslessly as PNG. Refuse any computed page over 40 million pixels by raising **RenderProblem(code="page_pixel_limit_exceeded")**.

- [ ] **Step 5: Write failing preprocessing tests**

Create deterministic synthetic images in **backend/tests/fixtures/images.py**:

- A white page with three black text-like bars rotated by 4 degrees.
- A low-contrast gray page with dark-gray bars.
- A clean high-contrast page that should not be thresholded aggressively.

Assert that **preprocess_page**:

- Returns an output file named **page-0001-processed.png**.
- Reports an absolute deskew angle between 3 and 5 degrees for the rotated fixture.
- Raises grayscale contrast for the low-contrast fixture.
- Records every applied operation in stable order.
- Leaves **RenderedPage** and its original file unchanged.

- [ ] **Step 6: Implement deterministic preprocessing**

Use these contracts:

~~~python
class PreprocessMetadata(BaseModel):
    rotation_degrees: int
    deskew_degrees: float
    contrast_applied: bool
    denoise_applied: bool
    threshold_method: Literal["none", "otsu", "adaptive"]
    operations: list[str]


@dataclass(frozen=True)
class PreprocessedPage:
    rendered: RenderedPage
    image_path: Path
    metadata: PreprocessMetadata
~~~

Implement the stages in this order:

1. Decode as grayscale and reject unreadable images.
2. Detect 90-degree orientation only when Tesseract orientation data is available; otherwise record 0.
3. Normalize low contrast with CLAHE when grayscale standard deviation is below 45.
4. Estimate small skew from dark-pixel coordinates using **cv2.minAreaRect**, clamp corrections to ±12 degrees, and rotate around the image center with a white border.
5. Apply a 3-by-3 median blur only when Laplacian variance indicates visible noise.
6. Select Otsu thresholding for bimodal histograms, adaptive thresholding for uneven illumination, or no threshold for already crisp pages.
7. Save once at the end and record the exact operations.

Keep the decision functions (**needs_contrast**, **estimate_skew**, **choose_threshold**) pure so their thresholds can be unit tested independently.

- [ ] **Step 7: Verify render and preprocessing behavior**

Run:

~~~powershell
uv run pytest backend/tests/pipeline/test_render.py backend/tests/pipeline/test_preprocess.py -v
uv run ruff check backend/app/pipeline backend/tests/pipeline
uv run mypy backend/app/pipeline
~~~

Expected: rendering and transformation tests pass, including original-file immutability.

- [ ] **Step 8: Commit page preparation**

~~~powershell
git add pyproject.toml uv.lock backend/app/pipeline backend/tests/pipeline backend/tests/fixtures
git commit -m "feat: render and preprocess scanned pages"
~~~

---

### Task 6: Add confidence-aware Tesseract OCR and layout grouping

**Files:**
- Create: **backend/app/pipeline/ocr.py**
- Create: **backend/app/pipeline/layout.py**
- Create: **backend/tests/pipeline/test_ocr.py**
- Create: **backend/tests/pipeline/test_layout.py**

**Interfaces:**
- Consumes: **PreprocessedPage**, **OCRSpan**, **DocumentBlock**, and normalized **BoundingBox**.
- Produces: **OCREngine** protocol, **TesseractEngine.recognize(page: PreprocessedPage) -> list[OCRSpan]**, and **group_spans(page_number: int, spans: list[OCRSpan]) -> list[DocumentBlock]**.

- [ ] **Step 1: Add the OCR adapter dependency**

Run:

~~~powershell
uv add pytesseract
~~~

Document the local binary requirement in a short **backend/README.md** section: Tesseract 5 with English trained data must be on **PATH**; the production image installs it explicitly.

- [ ] **Step 2: Write a failing adapter contract test**

Use a fake **pytesseract.image_to_data** result containing two lines, one blank token, and confidences **92**, **48**, and **-1**. Assert that the adapter:

- Omits blank and **-1** entries.
- Creates stable IDs **p1-s0001** and **p1-s0002**.
- Converts confidence percentages to **0.92** and **0.48**.
- Normalizes pixel coordinates to page width and height.
- Preserves Tesseract block, paragraph, line, and word numbers as source metadata.

Define the protocol:

~~~python
class OCREngine(Protocol):
    def recognize(self, page: PreprocessedPage) -> list[OCRSpan]:
        raise NotImplementedError
~~~

- [ ] **Step 3: Run the OCR test and observe failure**

Run: **uv run pytest backend/tests/pipeline/test_ocr.py -v**

Expected: FAIL because the OCR adapter is missing.

- [ ] **Step 4: Implement the Tesseract adapter**

Call **pytesseract.image_to_data** with **lang="eng"**, **config="--oem 1 --psm 3"**, and **output_type=Output.DICT**. Convert each accepted word to **OCRSpan**, include a metadata mapping with integer source hierarchy, and sort by Tesseract's block/paragraph/line/word tuple. Wrap missing-binary and timeout failures in **OCRProblem** with stable codes **tesseract_unavailable** and **ocr_timeout**.

- [ ] **Step 5: Write layout grouping tests**

Cover:

- Words sharing Tesseract block, paragraph, and line numbers become one ordered line.
- Vertically adjacent lines with similar left edges become one paragraph.
- A short line followed by a larger vertical gap is classified as a heading when its bounding-box height exceeds the page median by at least 25 percent.
- Repeated aligned columns with at least three rows produce a **table** block only when alignment confidence is at least 0.8.
- Ambiguous aligned text remains an **unknown** block and is never fabricated into a table.
- Block confidence is the character-count-weighted mean of its spans.

- [ ] **Step 6: Implement deterministic grouping**

Implement **group_spans** without model calls. Order first by source hierarchy and then by top/left coordinates. Use helper functions **group_lines**, **merge_paragraph_lines**, **classify_block**, and **weighted_confidence**, each returning new values without mutating spans. Populate **DocumentBlock.span_ids**, **raw_text**, unioned **bbox**, **confidence**, and **kind**.

- [ ] **Step 7: Verify OCR and layout tests**

Run:

~~~powershell
uv run pytest backend/tests/pipeline/test_ocr.py backend/tests/pipeline/test_layout.py -v
uv run ruff check backend/app/pipeline/ocr.py backend/app/pipeline/layout.py
uv run mypy backend/app/pipeline/ocr.py backend/app/pipeline/layout.py
~~~

Expected: all adapter and grouping cases pass.

- [ ] **Step 8: Commit OCR and layout**

~~~powershell
git add pyproject.toml uv.lock backend/README.md backend/app/pipeline/ocr.py backend/app/pipeline/layout.py backend/tests/pipeline
git commit -m "feat: add confidence-aware OCR and layout grouping"
~~~

---

### Task 7: Build a reproducible OCR evaluation corpus and baseline

**Files:**
- Create: **evaluation/__init__.py**
- Create: **evaluation/generate_corpus.py**
- Create: **evaluation/metrics.py**
- Create: **evaluation/run.py**
- Create: **evaluation/corpus/manifest.json**
- Create: **evaluation/ground_truth/clean-letter.txt**
- Create: **evaluation/ground_truth/skewed-report.txt**
- Create: **evaluation/ground_truth/noisy-invoice.txt**
- Create: **evaluation/baseline.json**
- Create: **backend/tests/evaluation/test_metrics.py**
- Create: **backend/tests/evaluation/test_runner.py**

**Interfaces:**
- Consumes: rendering, preprocessing, OCR, and layout components from Tasks 5–6.
- Produces: **TextMetrics**, **normalize_for_evaluation(text: str) -> str**, **score_text(reference: str, hypothesis: str) -> TextMetrics**, and a deterministic **evaluation/results.json**.

- [ ] **Step 1: Add metric and fixture-generation dependencies**

Run:

~~~powershell
uv add jiwer reportlab
~~~

- [ ] **Step 2: Write failing metric tests**

Create tests asserting:

~~~python
from evaluation.metrics import normalize_for_evaluation, score_text


def test_metrics_are_zero_for_equivalent_whitespace():
    result = score_text("A clean\ninvoice", "A   clean invoice")
    assert result.cer == 0
    assert result.wer == 0


def test_metrics_count_a_single_character_substitution():
    result = score_text("invoice", "lnvoice")
    assert result.character_substitutions == 1
    assert result.cer == 1 / 7
~~~

Also assert that punctuation and case remain significant; normalization may standardize line endings and repeated whitespace but must not hide OCR mistakes.

- [ ] **Step 3: Run metric tests and observe the missing module**

Run: **uv run pytest backend/tests/evaluation/test_metrics.py -v**

Expected: collection fails because **evaluation.metrics** does not exist.

- [ ] **Step 4: Implement typed CER/WER metrics**

Create a frozen **TextMetrics** dataclass with **cer**, **wer**, character insertions/deletions/substitutions, and word insertions/deletions/substitutions. Use **jiwer.process_characters** and **jiwer.process_words** after normalization. Round only while serializing the public JSON; preserve full floats internally.

- [ ] **Step 5: Generate a legally safe deterministic corpus**

Implement **generate_corpus.py** with a fixed random seed of **20260920**. It must:

- Draw original text written for this project into PDFs with ReportLab.
- Produce a clean letter, a report rotated by 3.5 degrees, and an invoice with deterministic Gaussian noise and uneven illumination.
- Store exact UTF-8 ground truth in the three declared text files.
- Write a manifest with sample ID, title, description, PDF path, ground-truth path, expected page count, and transformation labels.
- Refuse to overwrite corpus files unless called with **--replace**.

Run:

~~~powershell
uv run python -m evaluation.generate_corpus --replace
~~~

- [ ] **Step 6: Write the failing evaluation-runner test**

Inject a fake OCR engine returning known hypotheses for the three samples. Assert that **evaluation.run.evaluate_corpus** writes:

- **schema_version: "1.0"**
- **generated_from_manifest_sha256**
- Aggregate and per-sample raw OCR metrics.
- Per-stage elapsed milliseconds.
- Engine name and preprocessing configuration.

Freeze elapsed timers in the test so output is deterministic.

- [ ] **Step 7: Implement the runner and establish the reviewed baseline**

The runner calls the real rendering, preprocessing, OCR, grouping, and metric modules; it accepts **--engine tesseract**, **--output evaluation/results.json**, and **--compare evaluation/baseline.json**. Comparison exits nonzero when aggregate CER or WER regresses by more than 0.02 absolute or when a sample cannot be processed.

Run the real corpus locally, inspect each hypothesis beside its ground truth, then copy the reviewed metrics and configuration into **evaluation/baseline.json**. Do not place generated timestamps in the baseline.

- [ ] **Step 8: Verify metrics and corpus reproducibility**

Run:

~~~powershell
uv run pytest backend/tests/evaluation -v
uv run python -m evaluation.generate_corpus
uv run python -m evaluation.run --engine tesseract --output evaluation/results.json --compare evaluation/baseline.json
~~~

Expected: the generator refuses overwrite without changing files, unit/integration tests pass, and the benchmark stays within explicit thresholds.

- [ ] **Step 9: Commit the evaluation foundation**

~~~powershell
git add pyproject.toml uv.lock evaluation backend/tests/evaluation
git commit -m "feat: add reproducible OCR evaluation baseline"
~~~

---

### Task 8: Implement constrained, reversible AI correction

**Files:**
- Create: **backend/app/providers/__init__.py**
- Create: **backend/app/providers/base.py**
- Create: **backend/app/providers/openai_compatible.py**
- Create: **backend/app/providers/gemini.py**
- Create: **backend/app/pipeline/correction.py**
- Create: **backend/tests/providers/test_openai_compatible.py**
- Create: **backend/tests/providers/test_gemini.py**
- Create: **backend/tests/pipeline/test_correction.py**
- Create: **backend/tests/fixtures/provider_responses.py**

**Interfaces:**
- Consumes: canonical spans/blocks and provider configuration.
- Produces: **CorrectionCandidate**, **CorrectionRequest**, **CorrectionProposal**, **CorrectionProvider.propose(request: CorrectionRequest, api_key: SecretStr) -> list[CorrectionProposal]**, **select_candidates(document: CanonicalDocument) -> list[CorrectionCandidate]**, **validate_proposals(document, candidates, proposals) -> list[CorrectionPatch]**, and **apply_patch_status(document, patch_id, status) -> CanonicalDocument**.

- [ ] **Step 1: Add provider transport dependencies**

Run:

~~~powershell
uv add httpx tenacity
~~~

- [ ] **Step 2: Write candidate-selection tests**

Create a document containing:

- One span at confidence 0.45.
- One span at confidence 0.76 containing mixed letters and digits.
- One ordinary span at confidence 0.96.
- One heading at confidence 0.88.

Assert that **select_candidates** includes the first two spans, excludes the ordinary span, keeps block/page context, and returns stable IDs. Candidate rules are: confidence below 0.80, suspicious mixed alphanumeric tokens matching a word-like pattern, or disagreement with the local spell-check heuristic. Do not send an entire high-confidence block merely because one span is suspicious.

- [ ] **Step 3: Write patch-validation and immutability tests**

Test rejection of:

- Unknown candidate or span IDs.
- An **original_text** that does not exactly match the selected raw spans.
- Noncontiguous spans.
- Empty replacement text.
- A replacement over three times the original length or over 120 characters.
- A proposal containing an unrecognized field.

Test that valid proposals become **proposed** patches, patches over model confidence 0.97 become **accepted** only when every source span has OCR confidence below 0.65, and all other patches require manual acceptance.

- [ ] **Step 4: Run correction tests and observe missing contracts**

Run: **uv run pytest backend/tests/pipeline/test_correction.py -v**

Expected: collection fails because correction/provider types do not exist.

- [ ] **Step 5: Implement correction contracts and validation**

Use strict Pydantic models:

~~~python
class CorrectionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    page_number: int
    block_id: str
    span_ids: list[str]
    original_text: str
    left_context: str
    right_context: str
    ocr_confidence: float


class CorrectionProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str
    original_text: str
    replacement_text: str
    rationale: str
    confidence: float = Field(ge=0, le=1)
~~~

Build stable candidate and patch IDs from SHA-256 hashes of job ID, block ID, span IDs, and raw text. Treat OCR text as quoted data in prompts. The system instruction must require JSON only, prohibit summaries and unsupported additions, and require returning no proposal when uncertain.

- [ ] **Step 6: Write provider contract tests before adapters**

With **httpx.MockTransport**, assert that:

- The OpenAI-compatible adapter sends a JSON-schema response format, configured model, bounded output tokens, candidate IDs, and no API key in the URL or exception text.
- The Gemini adapter sends an equivalent response schema through its generation configuration.
- HTTP 401 becomes **ProviderProblem(code="invalid_provider_key", retryable=False)**.
- HTTP 429 becomes **ProviderProblem(code="provider_rate_limited", retryable=True)** without leaking response bodies.
- A malformed JSON response becomes **ProviderProblem(code="invalid_provider_response", retryable=False)**.
- The original **SecretStr** value never appears in captured logs.

- [ ] **Step 7: Implement both structured-output adapters**

Define:

~~~python
class CorrectionProvider(Protocol):
    async def propose(
        self,
        request: CorrectionRequest,
        api_key: SecretStr,
    ) -> list[CorrectionProposal]:
        raise NotImplementedError
~~~

Both adapters must use a 30-second total timeout, retry connection failures and 5xx responses at most twice with bounded exponential backoff, and never retry authentication or schema failures. Parse the provider response into a list of **CorrectionProposal** before returning. Log provider name, model, elapsed time, input candidate count, output proposal count, and token counts; do not log prompts, document text, headers, or response bodies.

- [ ] **Step 8: Verify correction and provider suites**

Run:

~~~powershell
uv run pytest backend/tests/pipeline/test_correction.py backend/tests/providers -v
uv run ruff check backend/app/providers backend/app/pipeline/correction.py
uv run mypy backend/app/providers backend/app/pipeline/correction.py
~~~

Expected: selection, validation, adapter, redaction, and retry tests pass without live API calls.

- [ ] **Step 9: Extend evaluation output with correction metrics**

Update **evaluation/run.py** and its test so an injected correction provider can add:

- Corrected CER and WER.
- Accepted and rejected correction counts.
- Correction precision against ground truth for modified spans.
- Input/output token counts and provider latency.

The default CI path uses a deterministic fake provider fixture; a separately documented **--live-provider** flag may run locally but is never used in CI.

- [ ] **Step 10: Commit constrained correction**

~~~powershell
git add pyproject.toml uv.lock backend/app/providers backend/app/pipeline/correction.py backend/tests/providers backend/tests/pipeline/test_correction.py backend/tests/fixtures evaluation
git commit -m "feat: add constrained reversible AI correction"
~~~

---

### Task 9: Add short-lived job state, queue processing, and progress events

**Files:**
- Create: **backend/app/domain/jobs.py**
- Create: **backend/app/storage/job_repository.py**
- Create: **backend/app/pipeline/orchestrator.py**
- Create: **backend/app/worker.py**
- Create: **backend/app/api/jobs.py**
- Modify: **backend/app/main.py**
- Modify: **backend/app/core/config.py**
- Create: **backend/tests/storage/test_job_repository.py**
- Create: **backend/tests/pipeline/test_orchestrator.py**
- Create: **backend/tests/api/test_jobs.py**

**Interfaces:**
- Consumes: ingestion, workspace, rendering, preprocessing, OCR, layout, correction, settings, and canonical document components.
- Produces: **JobStage**, **JobRecord**, **JobRepository**, **ArtifactBuilder**, **PipelineServices**, **process_document(job_id: str, services: PipelineServices) -> CanonicalDocument**, **process_hosted_job(job_id: str) -> None**, and initial job API routes.

- [ ] **Step 1: Add queue and Redis test dependencies**

Run:

~~~powershell
uv add redis rq sse-starlette python-multipart
uv add --dev fakeredis
~~~

- [ ] **Step 2: Write failing repository tests**

Define tests for:

- **create(record)** uses Redis **SET NX** and rejects a duplicate job ID.
- **get(job_id)** round-trips all fields through strict Pydantic JSON.
- **update(job_id, expected_revision, changes)** increments revision and rejects stale writers.
- Every create/update/document write refreshes the configured TTL.
- **delete(job_id)** removes job state and document JSON.
- Missing and expired jobs return **None** rather than creating state.

Use this model:

~~~python
class JobStage(StrEnum):
    queued = "queued"
    rendering = "rendering"
    preprocessing = "preprocessing"
    ocr = "ocr"
    correction = "correction"
    awaiting_byok = "awaiting_byok"
    intelligence = "intelligence"
    exports = "exports"
    complete = "complete"
    failed = "failed"


class JobRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    source_name: str
    stage: JobStage
    progress: float = Field(ge=0, le=1)
    current_page: int | None = None
    total_pages: int
    revision: int = 0
    error_code: str | None = None
    error_detail: str | None = None
    artifact_keys: list[str] = Field(default_factory=list)
    created_at: datetime
    expires_at: datetime
~~~

- [ ] **Step 3: Run repository tests and observe the missing implementation**

Run: **uv run pytest backend/tests/storage/test_job_repository.py -v**

Expected: collection fails because job models and repository do not exist.

- [ ] **Step 4: Implement optimistic, expiring job storage**

Store records at **job:{id}**, canonical documents at **job:{id}:document**, and event revisions at **job:{id}:events**. Use a Redis transaction watching the record key for revision-checked updates. Publish the serialized public **JobRecord** after each successful update. Never store provider keys, raw request headers, or exception trace text.

- [ ] **Step 5: Write the failing orchestration test**

Build fake renderer, preprocessor, OCR engine, correction provider, repository, and workspace factory. Assert the exact stage sequence:

~~~text
queued -> rendering -> preprocessing -> ocr -> correction -> exports -> complete
~~~

Assert that:

- Progress never decreases and finishes at 1.
- Completed page count is visible after each page.
- A two-page document retains page order even if fake page work finishes out of order.
- Raw OCR remains present after correction.
- A stage exception becomes **failed** with a stable public error code and no document text in **error_detail**.
- The canonical document is persisted before the job becomes **complete**.

- [ ] **Step 6: Implement dependency-injected orchestration**

Define **ArtifactBuilder.build(document: CanonicalDocument, workspace: JobWorkspace) -> list[str]** as a protocol. Its initial implementation writes validated canonical JSON and returns **["document_json"]**; Tasks 12–14 extend it with the other export implementations.

Create a **PipelineServices** dataclass holding repository, workspace factory, renderer, preprocessor, OCR engine, correction service, hosted provider factory, artifact builder, and clock. Keep **process_document** independent of FastAPI and RQ. Update state at every stage and page boundary. Catch known pipeline problems and map them to stable public codes; map unrecognized exceptions to **processing_failed** while logging a redacted stack trace.

The hosted worker function receives only **job_id**. It loads settings and the server-side hosted key inside the worker process, builds **PipelineServices**, and calls **process_document**. Never serialize a key in RQ arguments or metadata.

- [ ] **Step 7: Write initial job API tests**

Test:

- **POST /api/v1/jobs** accepts a small PDF multipart upload and returns 202 with a job ID, stage **queued**, expiry, and status/events URLs.
- Invalid content returns a problem-details response with the ingestion code.
- **GET /api/v1/jobs/{id}** returns current state and 404 **job_not_found** after expiry.
- **GET /api/v1/jobs/{id}/document** returns 409 **result_not_ready** before a document exists.
- **GET /api/v1/jobs/{id}/pages/{page_number}/image** serves only a rendered page belonging to that job and rejects traversal or unknown page numbers.
- **DELETE /api/v1/jobs/{id}** deletes Redis state and the isolated workspace, then returns 204.
- **GET /api/v1/jobs/{id}/events** emits a named **job.progress** event and closes after complete, failed, or expiry.

Override Redis, queue, repository, and workspace dependencies in tests; do not require a running Redis server.

- [ ] **Step 8: Implement job routes and problem details**

Create a ULID job ID using a small dependency:

~~~powershell
uv add ulid-py
~~~

Add a **ProblemDetail** Pydantic model with **type**, **title**, **status**, **detail**, **code**, **retryable**, **stage**, and **page_number**. Register exception handlers in **main.py**. In **POST /jobs**, validate before writing, create the workspace and record, enqueue **backend.app.worker.process_hosted_job** with only the ID, and return 202.

Implement the page-image route through a fixed page-number-to-workspace mapping and return **image/png**, **nosniff**, and **Cache-Control: private, no-store**. Never accept a filename or path from the request.

Implement SSE with **sse-starlette.EventSourceResponse**. Subscribe to the Redis channel, send an initial snapshot, send a heartbeat comment every 15 seconds, and disconnect cleanly when **request.is_disconnected()** becomes true.

- [ ] **Step 9: Verify repository, orchestration, and API suites**

Run:

~~~powershell
uv run pytest backend/tests/storage/test_job_repository.py backend/tests/pipeline/test_orchestrator.py backend/tests/api/test_jobs.py -v
uv run ruff check backend/app backend/tests
uv run mypy backend/app
~~~

Expected: queue boundaries, progress monotonicity, expiry, SSE, deletion, and error-shaping tests pass.

- [ ] **Step 10: Commit asynchronous job processing**

~~~powershell
git add pyproject.toml uv.lock backend/app backend/tests
git commit -m "feat: process documents as observable expiring jobs"
~~~

---

### Task 10: Deliver the first sample-document vertical slice

**Files:**
- Create: **backend/app/ingestion/samples.py**
- Create: **backend/app/api/samples.py**
- Create: **backend/scripts/__init__.py**
- Create: **backend/scripts/export_openapi.py**
- Modify: **backend/app/main.py**
- Create: **backend/tests/ingestion/test_samples.py**
- Create: **backend/tests/api/test_samples.py**
- Modify: **frontend/package.json**
- Create: **frontend/src/api/generated.ts**
- Create: **frontend/src/features/home/SampleGallery.tsx**
- Create: **frontend/src/features/home/SampleGallery.test.tsx**
- Create: **frontend/src/features/jobs/useJob.ts**
- Create: **frontend/src/features/jobs/JobProgress.tsx**
- Create: **frontend/src/features/jobs/JobProgress.test.tsx**
- Create: **frontend/src/features/document/RawResult.tsx**
- Modify: **frontend/src/app/App.tsx**

**Interfaces:**
- Consumes: evaluation manifest/corpus, job API, job SSE, and canonical document JSON.
- Produces: **SampleManifest**, **GET /api/v1/samples**, sample-backed **POST /api/v1/jobs**, generated frontend API types, **useJob(jobId)**, and the first browser-visible raw/corrected OCR result.

- [ ] **Step 1: Write sample-manifest validation tests**

Assert that the loader:

- Rejects duplicate IDs, missing corpus files, paths escaping **evaluation/corpus**, absent ground truth, and unsupported media types.
- Returns samples in manifest order.
- Exposes ID, title, description, page count, preview URL, and transformation labels but never filesystem paths or ground-truth text.

- [ ] **Step 2: Implement the immutable sample registry**

Define:

~~~python
class PublicSample(BaseModel):
    id: str
    title: str
    description: str
    page_count: int
    preview_url: str
    labels: list[str]
~~~

Load and validate the manifest once at application startup. Add an allow-listed route for sample preview images. Extend **POST /jobs** with a mutually exclusive **sample_id** form field; copy the known sample into the job workspace rather than accepting a client path.

- [ ] **Step 3: Add sample API tests**

Assert:

- **GET /samples** returns all public samples with no paths or ground truth.
- A valid **sample_id** creates a queued job.
- An unknown sample ID returns 404 **sample_not_found**.
- A request containing both upload and sample ID returns 422 **ambiguous_job_source**.

Run: **uv run pytest backend/tests/ingestion/test_samples.py backend/tests/api/test_samples.py -v**

Expected: all sample registry and route tests pass.

- [ ] **Step 4: Generate TypeScript contracts from FastAPI**

Add:

~~~powershell
npm --prefix frontend install -D openapi-typescript
~~~

Implement **backend/scripts/export_openapi.py** to import **create_app**, serialize **app.openapi()** with stable sorted keys, and write **frontend/openapi.json**. Add frontend scripts:

~~~json
{
  "generate:api": "openapi-typescript openapi.json -o src/api/generated.ts",
  "check:api": "npm run generate:api && git diff --exit-code -- src/api/generated.ts openapi.json"
}
~~~

Run the exporter and generator, then commit both the schema and generated types.

- [ ] **Step 5: Write the failing sample gallery test**

Mock **GET /samples** and **POST /jobs** with MSW. Assert that:

- Cards display title, description, page count, and labels.
- Clicking **Run this sample** posts only its sample ID.
- The returned job switches the screen to progress.
- The action remains keyboard accessible and has one clear accessible name.

Run: **npm --prefix frontend test -- --run src/features/home/SampleGallery.test.tsx**

Expected: FAIL because sample components do not exist.

- [ ] **Step 6: Implement sample selection and job progress**

Create **useJob** with:

- Initial status fetch through TanStack Query.
- An **EventSource** for **/jobs/{id}/events**.
- Cache replacement only when the event revision exceeds the cached revision.
- Automatic close on complete, failed, or component unmount.
- Polling fallback every two seconds after an SSE error.

Build **JobProgress** as a semantic ordered list of stages with one live status sentence and page progress. Honor **prefers-reduced-motion**; progress must remain understandable without animation.

- [ ] **Step 7: Display the first inspectable result**

Create **RawResult** to show, for the selected page:

- Original page image.
- Raw OCR block text and confidence.
- Accepted derived text.
- Proposed patch count.
- Raw versus corrected CER/WER when the sample has evaluation data.

This first view can be visually simple but must expose the complete vertical slice. Do not add upload controls in this task.

- [ ] **Step 8: Verify the vertical slice**

Run:

~~~powershell
uv run pytest backend/tests/ingestion/test_samples.py backend/tests/api/test_samples.py -v
python -m backend.scripts.export_openapi
npm --prefix frontend run generate:api
npm --prefix frontend test -- --run
npm --prefix frontend run build
~~~

Then run API, worker, and Redis locally and process **clean-letter** once. Expected: the browser moves from sample card through stage progress to original page, raw text, corrected text, confidence, and metrics without a manual refresh.

- [ ] **Step 9: Commit the vertical slice**

~~~powershell
git add backend evaluation frontend
git commit -m "feat: deliver sample OCR vertical slice"
~~~

---

### Task 11: Add anonymous multi-page uploads and resilient progress recovery

**Files:**
- Create: **backend/app/api/capabilities.py**
- Modify: **backend/app/main.py**
- Modify: **backend/app/api/jobs.py**
- Create: **backend/tests/api/test_capabilities.py**
- Modify: **backend/tests/api/test_jobs.py**
- Create: **frontend/src/features/home/UploadDropzone.tsx**
- Create: **frontend/src/features/home/UploadDropzone.test.tsx**
- Create: **frontend/src/features/jobs/JobRecovery.tsx**
- Modify: **frontend/src/features/jobs/useJob.ts**
- Modify: **frontend/src/app/App.tsx**

**Interfaces:**
- Consumes: upload limits, job API, and worker stages.
- Produces: **GET /api/v1/capabilities**, a bounded drag/drop/file-picker flow, upload progress, resumable job routing, and actionable multi-page errors.

- [ ] **Step 1: Write the capabilities contract test**

Assert the endpoint returns:

~~~json
{
  "accepted_media_types": ["application/pdf", "image/png", "image/jpeg"],
  "max_upload_bytes": 15000000,
  "max_pdf_pages": 12,
  "artifact_ttl_seconds": 3600,
  "hosted_provider": {
    "enabled": false,
    "remaining_documents": 0,
    "reset_at": null
  },
  "byok_providers": ["gemini", "openai_compatible"]
}
~~~

Values must come from settings and a quota-status service rather than literals in the route.

- [ ] **Step 2: Implement and register capabilities**

Create strict response models and inject **QuotaStatusProvider**. The initial implementation returns disabled/zero when hosted processing is disabled and delegates to the Redis limiter added in Task 15 when enabled.

- [ ] **Step 3: Write upload interaction tests**

Mock capabilities and job creation. Assert that:

- The file picker accepts PDF, PNG, and JPEG.
- Browser-side size rejection uses the server-provided byte limit.
- PDF page count is never guessed in the browser; the server response controls that error.
- Drop and picker paths call the same **submitUpload(file)** function.
- Upload state reports bytes sent when XMLHttpRequest progress is available.
- A 422 problem response displays its public detail and retains the selected filename.
- Refreshing **/jobs/{id}** restores status from the API instead of restarting work.

- [ ] **Step 4: Implement upload and route recovery**

Use **FormData** and XMLHttpRequest in a focused **uploadJob** function because Fetch does not provide standardized upload progress. Send no provider credential during ingestion. Navigate to **/jobs/{jobId}** immediately after 202. On app startup, read the URL, fetch the job, and show one of progress, result, expired, failed, or not-found states.

Keep the file input visibly labeled, support drag enter/leave without requiring drag use, and announce validation errors through **role="alert"**.

- [ ] **Step 5: Add multi-page integration coverage**

Create a three-page PDF fixture in memory and run the orchestration with fake OCR. Assert that:

- Three pages appear in canonical order.
- SSE reports current pages 1, 2, and 3.
- A completed first page can be fetched from the document endpoint while later pages remain in progress if partial persistence is enabled.
- Retrying a transient provider failure does not repeat OCR.

Implement stage checkpoints in the repository so a retried worker loads the last valid canonical document and resumes at correction or export rather than mutating earlier OCR.

- [ ] **Step 6: Verify upload and recovery**

Run:

~~~powershell
uv run pytest backend/tests/api/test_capabilities.py backend/tests/api/test_jobs.py backend/tests/pipeline/test_orchestrator.py -v
npm --prefix frontend test -- --run src/features/home/UploadDropzone.test.tsx src/features/jobs
npm --prefix frontend run build
~~~

Expected: bounded upload, three-page ordering, retry checkpoint, and browser recovery tests pass.

- [ ] **Step 7: Commit anonymous uploads**

~~~powershell
git add backend frontend
git commit -m "feat: add bounded multi-page upload workflow"
~~~

---

### Task 12: Build the digital-document workspace and reversible correction controls

**Files:**
- Modify: **backend/app/api/jobs.py**
- Create: **backend/app/exports/__init__.py**
- Create: **backend/app/exports/digital.py**
- Create: **backend/tests/api/test_corrections.py**
- Create: **backend/tests/exports/test_digital.py**
- Create: **frontend/src/features/document/DocumentWorkspace.tsx**
- Create: **frontend/src/features/document/PageNavigator.tsx**
- Create: **frontend/src/features/document/PagePreview.tsx**
- Create: **frontend/src/features/document/ReconstructedDocument.tsx**
- Create: **frontend/src/features/document/ConfidenceLegend.tsx**
- Create: **frontend/src/features/corrections/CorrectionInspector.tsx**
- Create: **frontend/src/features/corrections/CorrectionDiff.tsx**
- Create: **frontend/src/features/corrections/CorrectionInspector.test.tsx**
- Create: **frontend/src/features/exports/ExportMenu.tsx**
- Modify: **frontend/src/app/App.tsx**
- Create: **frontend/src/styles/workspace.css**

**Interfaces:**
- Consumes: canonical document, correction patches, job repository, workspace artifacts, and generated API types.
- Produces: **PATCH /jobs/{job_id}/corrections/{patch_id}**, **export_markdown**, **export_html**, **export_json**, **export_docx**, the three-pane document workspace, and digital export downloads.

- [ ] **Step 1: Write correction mutation API tests**

Assert:

- A body **{"status": "accepted"}** or **{"status": "rejected"}** updates only the named patch.
- Unknown job and patch IDs return separate 404 codes.
- A completed job update increments document and job revisions.
- Repeating the same status is idempotent.
- Updating an expired job fails without recreating it.
- The response returns the updated patch and affected block's derived accepted text.

- [ ] **Step 2: Implement atomic correction decisions**

Use repository optimistic revision checks so concurrent decisions cannot overwrite each other. Revalidate the entire **CanonicalDocument** before saving. Mark digital and searchable-PDF artifacts stale after a decision; JSON reflects the change immediately, while derived downloads regenerate lazily.

- [ ] **Step 3: Write digital exporter tests**

Build a two-page canonical document containing a heading, paragraph, list item, accepted patch, and rejected patch. Assert:

- Markdown uses heading/list syntax and accepted text.
- HTML uses only allow-listed semantic tags and escapes OCR/model HTML.
- JSON round-trips through **CanonicalDocument.model_validate_json**.
- DOCX contains page headings and accepted paragraph text.
- All exporters produce deterministic bytes or normalized text for the same input.

- [ ] **Step 4: Implement digital exporters**

Add:

~~~powershell
uv add python-docx nh3
~~~

Use this registry contract:

~~~python
class DigitalExporter(Protocol):
    media_type: str
    extension: str

    def export(self, document: CanonicalDocument) -> bytes:
        raise NotImplementedError


DIGITAL_EXPORTERS: dict[str, DigitalExporter]
~~~

Use accepted derived text, preserve page and block order, escape all untrusted text, sanitize final HTML with **nh3**, and include canonical schema/version metadata in JSON. Add **GET /jobs/{id}/exports/{format}** for **json**, **markdown**, **html**, and **docx** with safe fixed filenames and **Content-Disposition: attachment**.

- [ ] **Step 5: Write correction inspector tests**

With a canonical fixture, assert that the inspector:

- Shows original and replacement text without interpreting either as HTML.
- Displays page, block, OCR confidence, model confidence, and rationale.
- Accepts and rejects through the PATCH endpoint.
- Updates the reconstructed block immediately and can reverse the decision.
- Moves focus to the next undecided patch after a decision.
- Provides a “show source” action that selects the correct page/block.

- [ ] **Step 6: Implement the three-pane workspace**

Use CSS Grid with desktop columns for page navigation, document content, and inspector. Below 960 pixels, switch to one content pane with accessible tabs. Use canonical normalized boxes to draw non-interactive confidence overlays over the page image. Apply four confidence bands with color plus text/icon labels so color is not the only signal.

Keep selected page, block, and patch in the URL query string. Render reconstructed text as text nodes. A block click selects its source and inspector data; it never injects canonical HTML.

- [ ] **Step 7: Implement export states**

The export menu lists JSON, Markdown, HTML, and DOCX only when the canonical document exists. On a stale artifact, request generation and show a bounded pending state. Download through a same-origin URL; never create data URLs containing a full document.

- [ ] **Step 8: Verify the digital workspace**

Run:

~~~powershell
uv run pytest backend/tests/api/test_corrections.py backend/tests/exports/test_digital.py -v
npm --prefix frontend test -- --run src/features/corrections src/features/document src/features/exports
npm --prefix frontend run build
~~~

Manually verify keyboard navigation across page list, blocks, inspector decisions, and exports at 1440, 1024, and 390 CSS pixels.

- [ ] **Step 9: Commit the faithful digital document**

~~~powershell
git add pyproject.toml uv.lock backend frontend
git commit -m "feat: add inspectable digital document workspace"
~~~

---

### Task 13: Generate searchable PDFs from accepted canonical text

**Files:**
- Create: **backend/app/exports/searchable_pdf.py**
- Modify: **backend/app/api/jobs.py**
- Modify: **backend/app/pipeline/orchestrator.py**
- Create: **backend/tests/exports/test_searchable_pdf.py**
- Modify: **frontend/src/features/exports/ExportMenu.tsx**
- Create: **frontend/src/features/exports/SearchablePdfStatus.test.tsx**

**Interfaces:**
- Consumes: original validated upload, rendered-page dimensions, canonical blocks/spans, accepted corrections, and workspace artifacts.
- Produces: **SearchablePdfExporter.export(document: CanonicalDocument, source: ValidatedUpload, rendered_pages: list[RenderedPage]) -> bytes** and the **pdf** export route.

- [ ] **Step 1: Write failing PDF invariants**

Create an image-only two-page PDF fixture and canonical blocks with normalized coordinates. Assert that the output:

- Has the same page count and page dimensions as the source.
- Visually preserves page raster hashes when rendered with text visibility disabled.
- Returns accepted corrected text through **page.get_text("text")**.
- Does not return rejected replacement text.
- Places extracted words within an allowed coordinate tolerance of their canonical boxes.
- Contains no visible duplicate text when rendered normally.
- Opens without repair warnings in PyMuPDF.

Add an image-input case and assert it becomes a one-page PDF matching the source image aspect ratio.

- [ ] **Step 2: Run the PDF tests and observe the missing exporter**

Run: **uv run pytest backend/tests/exports/test_searchable_pdf.py -v**

Expected: collection fails because the searchable-PDF exporter does not exist.

- [ ] **Step 3: Implement invisible text placement**

For PDF sources, open the original bytes and retain each original page. For image sources, create a page sized from image dimensions at 72 DPI and insert the image once. For every canonical line:

1. Convert its normalized bounding box to PDF points.
2. Compute a font size from box height, clamped from 4 through 36 points.
3. Call PyMuPDF **insert_textbox** with a built-in font, **render_mode=3**, **overlay=True**, and the mapped box.
4. Reduce the font size in 0.5-point steps until insertion succeeds or reaches 4 points.
5. Record a nonfatal **text_layer_warning** if text still cannot fit; never alter page graphics.

Use accepted derived text and write metadata fields **OCRPipelineVersion**, **TextLayerSource=accepted**, and the canonical schema version. Save with garbage collection and compression enabled.

- [ ] **Step 4: Integrate artifact invalidation and lazy regeneration**

Add **pdf** to the export registry and artifact mapping. Generate it during the exports stage for completed hosted jobs. After any correction decision, remove only the stale searchable PDF artifact and its key from the job record. A subsequent download regenerates from the canonical document under a per-job Redis lock to prevent duplicate work.

- [ ] **Step 5: Add frontend searchable-PDF states**

Test and implement:

- A short explanation that the original appearance is preserved while selectable text is added.
- The source label **accepted corrections** or **raw OCR** from artifact metadata.
- Pending, ready, stale/regenerating, failed, and downloaded states.
- A retry action for generation failures that does not rerun OCR.

- [ ] **Step 6: Verify searchable PDF generation**

Run:

~~~powershell
uv run pytest backend/tests/exports/test_searchable_pdf.py backend/tests/api/test_corrections.py -v
npm --prefix frontend test -- --run src/features/exports
~~~

Open one generated PDF in two independent viewers, select text across at least two lines, search for one accepted corrected word, and verify the page image remains unchanged.

- [ ] **Step 7: Commit searchable PDF support**

~~~powershell
git add backend frontend
git commit -m "feat: generate position-aware searchable PDFs"
~~~

---

### Task 14: Add cited document intelligence with strict source validation

**Files:**
- Modify: **backend/app/domain/document.py**
- Modify: **backend/app/providers/base.py**
- Modify: **backend/app/providers/openai_compatible.py**
- Modify: **backend/app/providers/gemini.py**
- Create: **backend/app/pipeline/intelligence.py**
- Modify: **backend/app/pipeline/orchestrator.py**
- Create: **backend/tests/pipeline/test_intelligence.py**
- Create: **backend/tests/providers/test_intelligence_contracts.py**
- Create: **frontend/src/features/report/IntelligenceReport.tsx**
- Create: **frontend/src/features/report/CitedItem.tsx**
- Create: **frontend/src/features/report/IntelligenceReport.test.tsx**
- Modify: **frontend/src/features/document/DocumentWorkspace.tsx**

**Interfaces:**
- Consumes: accepted canonical block text and provider structured-output transport.
- Produces: **ReportCitation**, **IntelligenceItem**, **ExtractedEntity**, **IntelligenceReport**, **build_report_chunks**, **validate_report**, and report UI that navigates citations to page/block sources.

- [ ] **Step 1: Define and test strict report models**

Add these shapes:

~~~python
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
    key_points: list[IntelligenceItem] = Field(max_length=8)
    entities: list[ExtractedEntity] = Field(max_length=40)
~~~

Test invalid empty citations, excess items, unknown entity kinds, and oversized text.

- [ ] **Step 2: Write chunking and citation-validation tests**

Assert that:

- Chunks preserve page/block order and contain stable block IDs beside accepted text.
- No chunk exceeds a configured 6,000-character budget unless one source block itself exceeds it; oversized blocks split into numbered subparts tied to the original block.
- Map-stage outputs may cite only IDs present in their chunk.
- Reduce-stage outputs may cite only IDs present anywhere in the document.
- An item containing one unknown ID is dropped and recorded in validation warnings.
- Duplicate entities of the same kind/value merge citations deterministically.
- A report with no valid summary raises **IntelligenceProblem(code="uncited_report")**.

- [ ] **Step 3: Implement chunking, map/reduce, and validation**

Use accepted block text. The provider returns strict JSON report fragments with source IDs; it never receives page images or raw credentials in the prompt. For one chunk, perform one analysis call. For multiple chunks, analyze each chunk and reduce only the structured fragments, retaining citations. Validate every final citation against canonical page/block membership.

Extend provider adapters with a shared private structured-request primitive rather than duplicating HTTP/error logic. Add **IntelligenceProvider.analyze(chunks, api_key)** at the protocol boundary.

- [ ] **Step 4: Add provider contract tests**

With mock transports, assert bounded token settings, schema use, exact block-ID inclusion, malformed response handling, redaction, and map/reduce call counts. CI must not contact a live model.

- [ ] **Step 5: Integrate report generation into job stages**

For hosted jobs, run intelligence after correction and before exports. Persist a canonical document containing the report and warnings. A report failure must not discard the digital document or searchable PDF; complete the job with an artifact warning and expose **report_unavailable**.

- [ ] **Step 6: Write report UI tests**

Assert that:

- Summary, key points, and grouped entities render as text.
- Each item exposes one or more buttons named with page and source reference.
- Activating a citation changes selected page/block and focuses the source.
- Invalid or absent report data produces an honest unavailable state.
- The UI never displays a citation that is absent from the canonical block map.

- [ ] **Step 7: Implement the cited report panel**

Add a workspace tab for **Intelligence report**. Keep the summary concise, key points scannable, and entities grouped by kind. Citation controls call the existing source-selection boundary; they do not duplicate page-viewer state. Show model/provider name, generation timestamp, token count, and a limitations note outside the report content.

- [ ] **Step 8: Verify report behavior**

Run:

~~~powershell
uv run pytest backend/tests/pipeline/test_intelligence.py backend/tests/providers/test_intelligence_contracts.py -v
npm --prefix frontend test -- --run src/features/report
uv run ruff check backend/app/pipeline/intelligence.py backend/app/providers
uv run mypy backend/app/pipeline/intelligence.py backend/app/providers
~~~

Expected: citation validation, bounded map/reduce, provider contracts, and source navigation pass.

- [ ] **Step 9: Commit cited intelligence**

~~~powershell
git add backend frontend
git commit -m "feat: add source-cited document intelligence"
~~~

---

### Task 15: Enforce hosted quotas and implement ephemeral BYOK

**Files:**
- Create: **backend/app/core/rate_limit.py**
- Create: **backend/app/core/logging.py**
- Modify: **backend/app/core/config.py**
- Modify: **backend/app/api/capabilities.py**
- Modify: **backend/app/api/jobs.py**
- Modify: **backend/app/pipeline/orchestrator.py**
- Modify: **backend/app/worker.py**
- Modify: **backend/app/main.py**
- Create: **backend/tests/core/test_rate_limit.py**
- Create: **backend/tests/core/test_redaction.py**
- Create: **backend/tests/api/test_hosted_quota.py**
- Create: **backend/tests/api/test_byok.py**
- Create: **frontend/src/features/jobs/ProviderChoice.tsx**
- Create: **frontend/src/features/jobs/ByokForm.tsx**
- Create: **frontend/src/features/jobs/ByokForm.test.tsx**
- Modify: **frontend/src/features/home/UploadDropzone.tsx**
- Modify: **frontend/src/features/jobs/JobProgress.tsx**

**Interfaces:**
- Consumes: Redis, request metadata, provider adapters, correction/intelligence services, and server settings.
- Produces: **UsageLimiter**, **VisitorIdentity**, **RedactingProcessor**, hosted quota status/consumption, **POST /jobs/{id}/ai**, and browser-memory-only BYOK submission.

- [ ] **Step 1: Add exact hosted-limit settings**

Add validated settings with these public-demo defaults:

~~~python
hosted_window_seconds: int = 86_400
hosted_documents_per_window: int = 3
hosted_pages_per_window: int = 20
hosted_tokens_per_window: int = 30_000
hosted_concurrent_jobs: int = 1
visitor_cookie_name: str = "ocr_visitor"
visitor_signing_secret: SecretStr
identity_hash_secret: SecretStr
~~~

Production startup must fail when hosted processing is enabled and either hosted provider credentials or signing secrets are absent. Test environment settings may inject fixed secrets.

- [ ] **Step 2: Write atomic limiter tests**

With fakeredis, assert:

- A visitor can consume up to three documents and 20 pages in one window.
- Document, page, and token counters reject before exceeding their limit.
- Rejected consumption does not increment any counter.
- At most one active hosted job exists per visitor.
- Releasing or expiring a job frees concurrency.
- Reset time is stable within the window.
- Two simultaneous consumers cannot both claim the final slot.
- Raw IP addresses and visitor cookie values never appear in Redis keys or values.

- [ ] **Step 3: Implement privacy-preserving visitor identity and Lua consumption**

Issue a random 128-bit visitor token as **HttpOnly**, **Secure** in production, **SameSite=Lax**, and bounded to the hosted window. Verify its HMAC signature on each request. Compute a rate-limit subject as SHA-256 HMAC over the verified visitor ID plus normalized client IP using **identity_hash_secret**. Never trust **X-Forwarded-For** unless the immediate peer is in a configured trusted-proxy list.

Use one Redis Lua script to check and increment document/page/token counters plus concurrency atomically and set expiries. Return remaining counts and reset epoch. Provide a separate idempotent release operation keyed by job ID.

- [ ] **Step 4: Integrate hosted quota with capabilities and job creation**

Capabilities returns the current visitor's remaining documents/pages and reset time. Hosted job creation reserves quota after upload validation but before queueing. If queueing fails, release the reservation. Known sample playback using precomputed results consumes no provider quota; rerunning a sample through live AI does.

Return HTTP 429 **hosted_quota_exhausted** or **hosted_job_in_progress** with reset/retry metadata.

- [ ] **Step 5: Write BYOK security tests**

Assert that **POST /jobs/{id}/ai**:

- Accepts provider **gemini** or **openai_compatible** plus an API key in **X-Provider-API-Key**.
- Rejects missing, blank, line-break-containing, or oversized keys.
- Requires a job at **awaiting_byok** and never reruns OCR.
- Calls correction and intelligence using **SecretStr** local to the request.
- Stores no key in Redis, RQ, workspace files, canonical JSON, logs, exceptions, or responses.
- Clears references after success/failure and leaves the job retryable after an invalid key.
- Uses a 120-second request timeout and marks a disconnected request as **byok_cancelled** without persisting credentials.

- [ ] **Step 6: Implement request-scoped BYOK processing**

Add **ai_mode=hosted|byok** to job creation. Hosted mode follows the complete queued pipeline. BYOK mode queues **process_ocr_only_job(job_id)** with no credential, stops after canonical OCR/layout persistence, and enters **awaiting_byok**. The browser can then call **POST /jobs/{id}/ai**.

Do not enqueue BYOK credentials. Run correction and intelligence in the FastAPI request task after OCR has completed. Pass **SecretStr** directly to the selected provider adapter, update ordinary job progress through the repository, and return the completed public job record. Limit BYOK documents to the same page/file bounds but do not consume hosted model quota.

Set **Cache-Control: no-store** on the request and response, exclude **X-Provider-API-Key** from access logs, and reject cross-origin requests. Configure the reverse proxy not to log this header in Task 18.

- [ ] **Step 7: Implement structured redaction**

Use standard logging plus a processor/filter that recursively replaces values whose keys contain **authorization**, **api_key**, **token**, **secret**, **document_text**, **prompt**, or **response_body**. Redact provider URLs containing query keys. Tests must capture logs from successful and failed hosted/BYOK calls and assert sentinel keys and OCR phrases are absent.

- [ ] **Step 8: Write and implement BYOK frontend behavior**

Test that:

- Provider choice clearly separates limited hosted processing from BYOK.
- The key field uses **type="password"**, **autocomplete="off"**, and a warning that text goes to the selected provider.
- The key exists only in component state and is cleared immediately after the request settles or the form unmounts.
- No localStorage/sessionStorage calls occur.
- Network errors ask the user to re-enter the key rather than retaining it.
- Provider keys never appear in URLs, analytics events, error messages, or rendered DOM after submission.

- [ ] **Step 9: Verify quota, redaction, and BYOK**

Run:

~~~powershell
uv run pytest backend/tests/core/test_rate_limit.py backend/tests/core/test_redaction.py backend/tests/api/test_hosted_quota.py backend/tests/api/test_byok.py -v
npm --prefix frontend test -- --run src/features/jobs/ByokForm.test.tsx
uv run ruff check backend/app/core backend/app/api
uv run mypy backend/app/core backend/app/api
~~~

Expected: atomic quota and secret non-persistence tests pass.

- [ ] **Step 10: Commit public usage controls**

~~~powershell
git add backend frontend
git commit -m "feat: enforce hosted quotas and ephemeral BYOK"
~~~

---

### Task 16: Publish the evaluation dashboard and precomputed demo results

**Files:**
- Modify: **evaluation/run.py**
- Create: **evaluation/public-results.json**
- Create: **evaluation/precompute_samples.py**
- Create: **evaluation/precomputed/** generated canonical/artifact files
- Create: **backend/app/api/evaluation.py**
- Modify: **backend/app/api/samples.py**
- Modify: **backend/app/main.py**
- Create: **backend/tests/api/test_evaluation.py**
- Create: **backend/tests/ingestion/test_precomputed_samples.py**
- Create: **frontend/src/features/evaluation/EvaluationDashboard.tsx**
- Create: **frontend/src/features/evaluation/MetricCard.tsx**
- Create: **frontend/src/features/evaluation/SampleComparison.tsx**
- Create: **frontend/src/features/evaluation/EvaluationDashboard.test.tsx**
- Modify: **frontend/src/app/App.tsx**

**Interfaces:**
- Consumes: reviewed evaluation output, sample manifest, canonical models, and digital/searchable-PDF exporters.
- Produces: **GET /api/v1/evaluation**, no-provider precomputed sample jobs, and a public raw-versus-corrected benchmark experience.

- [ ] **Step 1: Define and test the public evaluation schema**

The public endpoint must return:

- Evaluation schema version and corpus revision hash.
- OCR engine, preprocessing profile, correction provider label, and run environment.
- Aggregate raw/corrected CER and WER.
- Per-sample raw/corrected CER and WER, stage latency, correction counts, token counts, and representative diff spans.
- A clear flag distinguishing measured data from descriptive metadata.

Test rejection of NaN/Infinity, negative timing/token values, missing sample IDs, and metrics outside 0 through 1 where bounded.

- [ ] **Step 2: Generate a deterministic public result**

Extend the evaluation runner with **--public-output evaluation/public-results.json**. Strip local absolute paths, credentials, raw provider responses, timestamps that change on every run, and full document text. Keep corpus revision, dependency/model identifiers, configuration, metrics, and reviewed representative diffs.

- [ ] **Step 3: Precompute sample jobs**

Implement **precompute_samples.py** to run each sample through the complete pipeline with a selected reviewed provider recording, then write:

- Strict canonical JSON.
- Page previews.
- Markdown, HTML, JSON, DOCX, and searchable PDF artifacts.
- Public job metadata with **precomputed: true**.
- SHA-256 hashes for every artifact in a manifest.

The script validates all output against current Pydantic models and refuses unreviewed provider fixtures. Commit these bounded artifacts so sample playback needs neither Redis queue work nor a provider.

- [ ] **Step 4: Serve immutable precomputed samples**

When a visitor chooses ordinary sample playback, clone the precomputed job metadata into an expiring visitor job and expose allow-listed artifacts. Verify hashes before serving. Add a separate explicitly labeled **Run live pipeline** action when hosted quota is available.

- [ ] **Step 5: Write dashboard interaction tests**

Assert:

- Metric cards label CER/WER in plain language and include exact values.
- Raw and corrected results are not presented as universally improved; regressions show honestly.
- Sample selection updates the comparison and URL.
- Representative diffs use additions/deletions labels in addition to color.
- Methodology, corpus size, model label, and limitations are visible.
- The dashboard works with JavaScript-generated charts disabled because exact values remain in a semantic table.

- [ ] **Step 6: Implement the portfolio evaluation view**

Create a dedicated **/evaluation** route. Use small SVG or CSS bars for raw/corrected comparisons, an accessible table for exact values, and a source-linked representative diff. Explain CER, WER, constrained correction, corpus limitations, and why evaluation fixtures are synthetic.

- [ ] **Step 7: Verify public evaluation and offline samples**

Run:

~~~powershell
uv run pytest backend/tests/api/test_evaluation.py backend/tests/ingestion/test_precomputed_samples.py backend/tests/evaluation -v
uv run python -m evaluation.precompute_samples
npm --prefix frontend test -- --run src/features/evaluation
npm --prefix frontend run build
~~~

Temporarily unset hosted provider credentials and stop external network access. Expected: every ordinary sample still opens with all three outputs and the evaluation dashboard remains complete.

- [ ] **Step 8: Commit the evaluation showcase**

~~~powershell
git add evaluation backend frontend
git commit -m "feat: publish OCR evaluation and offline demos"
~~~

---

### Task 17: Add end-to-end, accessibility, cleanup, and security regression coverage

**Files:**
- Create: **backend/app/cleanup.py**
- Create: **backend/tests/test_cleanup.py**
- Create: **frontend/playwright.config.ts**
- Create: **frontend/tests/e2e/sample-flow.spec.ts**
- Create: **frontend/tests/e2e/upload-flow.spec.ts**
- Create: **frontend/tests/e2e/byok-flow.spec.ts**
- Create: **frontend/tests/e2e/accessibility.spec.ts**
- Create: **frontend/tests/e2e/security.spec.ts**
- Modify: **frontend/package.json**
- Create: **backend/tests/security/test_static_serving.py**
- Create: **backend/tests/security/test_untrusted_content.py**

**Interfaces:**
- Consumes: the complete product surface from Tasks 1–16.
- Produces: deterministic expiry cleanup, browser-level acceptance tests, accessibility checks, and security regressions that guard prior key/text exposure.

- [ ] **Step 1: Write cleanup tests**

Using a fixed clock, create active, expired, malformed, and orphaned workspace cases. Assert that **cleanup_expired_jobs**:

- Deletes only expired job records and their exact workspaces.
- Leaves active jobs and unrelated sibling directories untouched.
- Removes orphaned workspaces only after **artifact_ttl_seconds + 300**.
- Is idempotent.
- Logs job ID and artifact counts but no filenames or document text.

- [ ] **Step 2: Implement scheduled cleanup**

Create **python -m backend.app.cleanup** with **--once** and loop modes. Resolve and contain every deletion path before removal. Acquire a Redis lock so only one cleaner runs. Add cleanup as a separate Compose service in Task 18 rather than hiding it inside the API process.

- [ ] **Step 3: Install browser and accessibility tooling**

Run:

~~~powershell
npm --prefix frontend install -D @playwright/test @axe-core/playwright
npx --prefix frontend playwright install chromium
~~~

Configure Playwright to start the test Compose profile, use one worker for rate-limit determinism, capture traces on first retry, and retain screenshots only on failure.

Add these frontend scripts:

~~~json
{
  "test": "vitest",
  "e2e": "playwright test"
}
~~~

- [ ] **Step 4: Write the sample happy-path browser test**

The test must:

1. Open the home page.
2. Select **clean-letter** without an account/key.
3. Observe progress/result recovery.
4. Compare one raw/corrected span.
5. Reject then accept a patch.
6. Follow one intelligence citation.
7. Download Markdown and searchable PDF.
8. Visit evaluation and verify raw/corrected metrics.
9. Delete the job and confirm the expired/deleted state.

Use role/name selectors, not CSS implementation selectors.

- [ ] **Step 5: Write upload and BYOK browser tests**

Cover valid multi-page upload, size rejection, unsupported bytes, page-limit problem, refresh during progress, hosted quota exhaustion, BYOK invalid key, BYOK success through a mock provider, and key clearing. Intercept the mock provider at the backend transport boundary so the browser exercises the real API.

- [ ] **Step 6: Add automated accessibility checks**

Run Axe on home, processing, document workspace, correction inspector, intelligence report, evaluation, quota error, and BYOK modal states. Add keyboard-only assertions for upload, page navigation, correction decisions, citations, export menu, and focus return after modal close. Assert no serious or critical violations.

- [ ] **Step 7: Add explicit security regressions**

Backend tests must prove:

- **/.env**, **/server.js**, repository metadata, workspace paths, and arbitrary files return 404.
- Hosted secrets are absent from HTML, JavaScript, OpenAPI, capabilities, logs, and error bodies.
- Script tags, event-handler attributes, CSS URLs, bidirectional control characters, and formula-like text from OCR/model output render or export safely.
- Oversized multipart bodies terminate before writing a full file.
- Cross-origin BYOK and correction mutations are rejected.
- Public downloads use **nosniff**, safe media types, fixed filenames, and attachment disposition where appropriate.

- [ ] **Step 8: Run complete local verification**

Run:

~~~powershell
uv run pytest -v
uv run ruff check .
uv run mypy backend/app evaluation
npm --prefix frontend test -- --run
npm --prefix frontend run build
npm --prefix frontend run e2e
~~~

Expected: backend, frontend, browser, accessibility, cleanup, and security suites pass.

- [ ] **Step 9: Commit release-level regression coverage**

~~~powershell
git add backend frontend
git commit -m "test: cover public OCR workflow end to end"
~~~

---

### Task 18: Containerize, automate CI, document the system, and retire the insecure legacy server

**Files:**
- Create: **docker/Dockerfile**
- Create: **docker/entrypoint.sh**
- Create: **compose.yaml**
- Create: **.dockerignore**
- Create: **.env.example**
- Create: **.github/workflows/ci.yml**
- Create: **docs/architecture.md**
- Create: **docs/model-card.md**
- Create: **docs/privacy.md**
- Rewrite: **README.md**
- Delete after replacement verification: **server.js**
- Delete after replacement verification: **config.js**
- Delete after replacement verification: **env-loader.js**
- Delete after replacement verification: **ai-service.js**
- Delete after replacement verification: **script.js**
- Delete after replacement verification: **style.css**
- Delete after replacement verification: **index.html**
- Delete after replacement verification: **landing.html**
- Delete after replacement verification: root **package.json**
- Delete after replacement verification: root **package-lock.json**

**Interfaces:**
- Consumes: completed API, worker, cleaner, frontend, tests, generated sample artifacts, and environment settings.
- Produces: reproducible local/production containers, CI quality gates, a safe static frontend mount, operator/user documentation, and no remaining path that logs or injects provider secrets.

- [ ] **Step 1: Create the production image**

Use a multi-stage image:

1. Node stage installs frontend dependencies with **npm ci**, verifies generated API types, runs the production build, and outputs static assets.
2. Python base stage installs locked runtime dependencies.
3. Test target adds development dependencies, source tests, and Chromium prerequisites.
4. Runtime target installs only Tesseract English data and minimal native libraries needed by OpenCV/PyMuPDF.
5. Copy backend, evaluation precomputed assets, and built frontend into runtime.
6. Run runtime as a non-root user with **/data/jobs** as the only writable application path.

The entrypoint accepts exactly **api**, **worker**, or **cleanup** and maps them to Uvicorn, RQ worker, or cleanup loop. It must not echo environment values.

- [ ] **Step 2: Define the local production topology**

Create Compose services:

- **api** — exposed on port 8000, health checked, same-origin static frontend.
- **worker** — same image, no public port, shared **job-data** volume.
- **cleanup** — same image, one cleanup loop, shared volume.
- **redis** — internal only, append-only persistence disabled because all data is disposable.
- **test-backend** and **test-e2e** — test-image services under the **test** profile, never started in production.

Set CPU/memory limits for worker and Redis, a read-only root filesystem where supported, **no-new-privileges**, and temporary **/tmp** mounts. Do not place any secret value in Compose; reference environment variable names.

- [ ] **Step 3: Serve only the built frontend allow-list**

After API routes, mount the compiled frontend directory. Add an SPA fallback that serves only **index.html** for paths without a file suffix; return 404 for dotfiles, backend paths, repository files, and unknown asset filenames. Add headers:

~~~text
Content-Security-Policy: default-src 'self'; img-src 'self' blob: data:; connect-src 'self'; style-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'
Referrer-Policy: no-referrer
X-Content-Type-Options: nosniff
Permissions-Policy: camera=(), microphone=(), geolocation=()
~~~

Do not allow inline scripts or CDN-loaded runtime code.

- [ ] **Step 4: Add CI quality and security gates**

Define jobs for:

- Backend lint/type/unit/integration tests on Python 3.12.
- Frontend generated-contract check, unit tests, and build on the locked Node version.
- Docker Compose browser tests with Chromium.
- Evaluation regression against **evaluation/baseline.json** using deterministic provider fixtures.
- **pip-audit**, **npm audit --omit=dev**, and **gitleaks/gitleaks-action@v2**.
- Container build with no push on pull requests.

Cache only package downloads, never **.env**, Redis, workspaces, Playwright traces containing user uploads, or generated job artifacts. Upload failing test traces with a seven-day retention.

- [ ] **Step 5: Write operational examples without secrets**

Create **.env.example** containing names and safe defaults only. Include hosted provider base URL/model, Redis URL, limits, TTL, trusted proxies, signing secrets represented by explanatory dummy values, and environment. The README must instruct users to generate secrets and must state that committing real values is unsafe.

- [ ] **Step 6: Document architecture, evaluation, and privacy**

Write:

- **architecture.md** — one diagram and prose for browser → API → Redis/RQ → worker → workspace/provider, canonical model ownership, stage recovery, and BYOK's request-scoped exception.
- **model-card.md** — OCR engine/model names, synthetic corpus, CER/WER method, reviewed results, known language/layout limits, correction auto-accept rule, hallucination safeguards, and non-goals.
- **privacy.md** — exactly what stays local, what reaches the server, what reaches the selected provider, retention duration, immediate deletion, hosted/BYOK differences, logging exclusions, and public-demo warning against sensitive documents.
- **README.md** — 60-second product explanation, screenshots, a deployment step that adds the real live-demo URL only after it exists, feature list, architecture summary, local quick start, evaluation command, tests, deployment, and security disclosure path.

- [ ] **Step 7: Verify replacement before removing legacy files**

Run the complete Task 17 command set inside fresh containers. Compare every legacy capability that remains in scope:

- Image upload.
- PDF upload.
- OCR progress.
- AI cleanup.
- Summary.
- Copy/export.
- Hosted limited usage.
- BYOK.

Only after all replacement checks pass, remove the listed legacy root files with **git rm**. Preserve their history in Git; do not copy them into the production image or a public legacy directory.

- [ ] **Step 8: Run secret and artifact inspection**

Run:

~~~powershell
git grep -n -I -E "OPENAI_COMPATIBLE_API_KEY|GEMINI_API_KEY|AIza|sk-[A-Za-z0-9]"
docker compose build --no-cache
docker compose up -d
curl.exe -f http://localhost:8000/api/v1/health/ready
curl.exe -i http://localhost:8000/.env
curl.exe -i http://localhost:8000/server.js
docker compose --profile test run --rm test-backend uv run pytest -v
docker compose --profile test run --rm test-backend uv run python -m evaluation.run --engine tesseract --output /tmp/results.json --compare evaluation/baseline.json
docker compose --profile test run --rm test-e2e npm run e2e
docker compose down
~~~

Expected: grep reports only documented variable names or test sentinels, health returns 200, forbidden files return 404, tests and evaluation pass, and container logs contain no secrets or document text.

- [ ] **Step 9: Commit the production-ready replacement**

~~~powershell
git add docker compose.yaml .dockerignore .env.example .github docs README.md backend frontend evaluation pyproject.toml uv.lock
git add -u
git commit -m "release: ship scanned PDF intelligence portfolio"
~~~

---

## Final Acceptance Checklist

- [ ] A new visitor can run a precomputed sample without an account, key, quota, provider, or network dependency beyond the application itself.
- [ ] A bounded scanned PDF upload reaches an observable multi-page OCR pipeline and recovers after refresh.
- [ ] Raw OCR, confidence, preprocessing metadata, proposed patches, and accepted text remain inspectable.
- [ ] Correction decisions are reversible and never mutate stored raw OCR.
- [ ] Digital JSON, Markdown, HTML, DOCX, and searchable PDF exports derive from the same canonical model.
- [ ] Every intelligence item has a valid source navigation target.
- [ ] Evaluation reports raw/corrected CER, WER, latency, correction, and token metrics against reviewed ground truth.
- [ ] Hosted quota is atomic and server-enforced; BYOK keys appear nowhere outside request memory and provider transport.
- [ ] Expired/deleted jobs leave neither Redis records nor workspace artifacts.
- [ ] Browser accessibility, security, backend, frontend, provider-contract, and evaluation tests all pass.
- [ ] Production static serving cannot expose repository files, environment files, or provider credentials.
- [ ] Documentation accurately describes privacy boundaries, model limitations, evaluation method, and local/deployment workflows.

## Spec Coverage Review

| Design requirement | Implemented by |
|---|---|
| Public sample and upload entry experience | Tasks 10–11 |
| Three-pane inspectable digital document | Task 12 |
| Searchable PDF retaining original appearance | Task 13 |
| Cited summary and entity report | Task 14 |
| Observable preprocessing, OCR confidence, and correction patches | Tasks 5–6, 8–12 |
| One canonical model for all views and exports | Tasks 3, 12–14 |
| Hosted limit plus request-scoped BYOK | Task 15 |
| CER/WER, latency, correction, and token evaluation | Tasks 7, 8, and 16 |
| Precomputed provider-independent demos | Task 16 |
| Validation, redaction, retention, and safe static serving | Tasks 4, 15, 17, and 18 |
| Unit, integration, provider-contract, browser, and accessibility tests | Tasks 1–18, consolidated in Task 17 |
| Containerized public deployment and portfolio documentation | Task 18 |

No design requirement lacks an implementation task. Deferred handwriting, accounts, billing, collaboration, document chat, and custom-model training remain absent from implementation tasks by design.
