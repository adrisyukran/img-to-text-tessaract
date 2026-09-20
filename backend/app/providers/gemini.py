from __future__ import annotations

from typing import Any

import httpx
from pydantic import SecretStr

from backend.app.pipeline.correction import CorrectionProposal, CorrectionRequest
from backend.app.providers.base import (
    PROPOSAL_SCHEMA,
    ProviderProblem,
    correction_prompt,
    parse_proposals,
    post_json,
)


class GeminiProvider:
    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.transport = transport

    async def propose(
        self,
        request: CorrectionRequest,
        api_key: SecretStr,
    ) -> list[CorrectionProposal]:
        body: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": correction_prompt(request)}],
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 1200,
                "responseMimeType": "application/json",
                "responseSchema": PROPOSAL_SCHEMA,
            },
        }
        headers = {
            "x-goog-api-key": api_key.get_secret_value(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            payload = await post_json(
                client,
                f"{self.base_url}/models/{self.model}:generateContent",
                headers,
                body,
            )
        try:
            candidates = payload["candidates"]
            content = candidates[0]["content"]
            parts = content["parts"]
            text_parts = [
                str(part["text"])
                for part in parts
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ]
            response_text = "".join(text_parts)
            if not response_text:
                raise TypeError
        except (IndexError, KeyError, TypeError) as exc:
            raise ProviderProblem(
                "invalid_provider_response",
                "provider response did not contain text content",
            ) from exc
        return parse_proposals(response_text)
