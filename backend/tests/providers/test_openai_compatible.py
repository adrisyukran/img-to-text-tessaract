import json
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from backend.app.pipeline.correction import CorrectionRequest
from backend.app.providers.base import ProviderProblem
from backend.app.providers.openai_compatible import OpenAICompatibleProvider
from backend.tests.fixtures.provider_responses import correction_response


@pytest.mark.asyncio
async def test_openai_compatible_provider_sends_schema_and_parses_response() -> None:
    captured: dict[str, Any] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=correction_response())

    provider = OpenAICompatibleProvider(
        "https://provider.test/v1",
        "demo-model",
        transport=httpx.MockTransport(handler),
    )
    result = await provider.propose(
        CorrectionRequest(
            job_id="job-1",
            candidates=[
                {
                    "id": "candidate-1",
                    "original_text": "lnvoice",
                    "page_number": 1,
                    "block_id": "p1-b1",
                }
            ],
        ),
        SecretStr("secret-value"),
    )

    assert result[0].replacement_text == "Invoice"
    assert captured["url"] == "https://provider.test/v1/chat/completions"
    assert captured["headers"]["authorization"] == "Bearer secret-value"
    assert captured["body"]["response_format"]["type"] == "json_schema"


@pytest.mark.asyncio
async def test_openai_provider_maps_auth_error_without_response_body() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="secret provider response")

    provider = OpenAICompatibleProvider(
        "https://provider.test/v1",
        "demo-model",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(ProviderProblem, match="invalid_provider_key") as error:
        await provider.propose(CorrectionRequest(job_id="job-1", candidates=[]), SecretStr("key"))
    assert "secret provider response" not in str(error.value)


@pytest.mark.asyncio
async def test_openai_provider_maps_rate_limit_without_response_body() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="private rate limit detail")

    provider = OpenAICompatibleProvider(
        "https://provider.test/v1",
        "demo-model",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(ProviderProblem, match="provider_rate_limited") as error:
        await provider.propose(CorrectionRequest(job_id="job-1", candidates=[]), SecretStr("key"))
    assert error.value.retryable is True
    assert "private rate limit detail" not in str(error.value)


@pytest.mark.asyncio
async def test_openai_provider_retries_server_errors() -> None:
    attempts = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(503, text="private server detail")
        return httpx.Response(200, json=correction_response())

    provider = OpenAICompatibleProvider(
        "https://provider.test/v1",
        "demo-model",
        transport=httpx.MockTransport(handler),
    )
    result = await provider.propose(
        CorrectionRequest(job_id="job-1", candidates=[]),
        SecretStr("key"),
    )
    assert attempts == 3
    assert result[0].replacement_text == "Invoice"


@pytest.mark.asyncio
async def test_openai_provider_rejects_malformed_model_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "not json"}}]},
        )

    provider = OpenAICompatibleProvider(
        "https://provider.test/v1",
        "demo-model",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(ProviderProblem, match="invalid_provider_response"):
        await provider.propose(CorrectionRequest(job_id="job-1", candidates=[]), SecretStr("key"))
