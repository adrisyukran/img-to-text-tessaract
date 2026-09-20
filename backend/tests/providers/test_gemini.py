import json
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from backend.app.pipeline.correction import CorrectionRequest
from backend.app.providers.gemini import GeminiProvider
from backend.tests.fixtures.provider_responses import gemini_correction_response


@pytest.mark.asyncio
async def test_gemini_provider_uses_header_key_and_parses_json_content() -> None:
    captured: dict[str, Any] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=gemini_correction_response())

    provider = GeminiProvider(
        "https://generativelanguage.test/v1beta",
        "gemini-test",
        transport=httpx.MockTransport(handler),
    )
    result = await provider.propose(
        CorrectionRequest(job_id="job-1", candidates=[]),
        SecretStr("secret-value"),
    )

    assert result[0].replacement_text == "Invoice"
    assert captured["url"] == (
        "https://generativelanguage.test/v1beta/models/gemini-test:generateContent"
    )
    assert captured["headers"]["x-goog-api-key"] == "secret-value"
    assert "responseSchema" in captured["body"]["generationConfig"]
