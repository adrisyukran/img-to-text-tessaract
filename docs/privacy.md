# Privacy and retention

## What stays local to the deployment

Uploaded files, rendered pages, OCR spans, canonical documents, reports, and exports stay inside
the deployment's Redis/workspace boundary. Jobs expire after OCR_ARTIFACT_TTL_SECONDS; users can
delete them sooner through the API. The cleanup service removes expired records and exact
workspaces.

## What reaches an external provider

Local OCR does not require a language-model provider. If hosted AI is enabled, the selected
low-confidence OCR spans and nearby context are sent to the configured provider. If a visitor
uses BYOK, the same bounded correction request is sent to the selected provider using the
request-scoped key. Page images are not sent by the correction adapter.

Provider names, models, elapsed times, and public error codes may be recorded for operations.
Credentials, request headers, prompts, raw OCR text, raw provider responses, and exception traces
must not be recorded.

## Public-demo warning

The hosted instance is for portfolio experimentation. Do not upload confidential, regulated,
personal, or otherwise sensitive documents. Disable hosted AI or run the stack locally when the
document must remain within your own network.
