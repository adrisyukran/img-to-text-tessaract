# Architecture

~~~text
Browser
  | same-origin JSON / SSE / downloads
  v
FastAPI API --- Redis job state, revisions, progress, quota
  |                         |
  | enqueue job ID          v
  +---------------------- RQ worker
                              |
                              +- isolated expiring workspace
                              +- render -> preprocess -> Tesseract -> layout
                              +- constrained provider correction
                              +- citation-validated report
                              +- canonical exports
~~~

The browser never owns the canonical document. The worker creates one CanonicalDocument, and the
API, correction inspector, report view, and exporters all read from that model. Raw OCR spans and
page coordinates are retained; accepted text is derived by applying accepted patches.

Redis stores short-lived public job state, revisioned progress events, canonical JSON, and hosted
quota counters. Uploaded bytes and generated files live in a per-job workspace below the configured
workspace root. Cleanup deletes expired records and their exact workspace.

Provider adapters share a transport/error boundary and return strict Pydantic models. OpenAI-
compatible and Gemini keys are sent in headers, never URLs. BYOK is the deliberate exception to
the normal server-side provider configuration: the key exists only during the active correction
request.
