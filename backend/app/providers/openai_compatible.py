from __future__ import annotations

from typing import Any

import httpx
from pydantic import SecretStr

from backend.app.pipeline.correction import CorrectionProposal, CorrectionRequest
from backend.app.providers.base import (
    PROPOSAL_SCHEMA,
    correction_prompt,
    parse_proposals,
    post_json,
)


class OpenAICompatibleProvider:
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
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a constrained OCR correction engine. Return only "
                        "schema-valid correction proposals."
                    ),
                },
                {"role": "user", "content": correction_prompt(request)},
            ],
            "temperature": 0,
            "max_tokens": 1200,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "ocr_correction_proposals",
                    "strict": True,
                    "schema": PROPOSAL_SCHEMA,
                },
            },
        }
        headers = {
            "Authorization": f"Bearer {api_key.get_secret_value()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            payload = await post_json(
                client,
                f"{self.base_url}/chat/completions",
                headers,
                body,
            )
        try:
            content: Any = payload["choices"][0]["message"]["content"]
            if isinstance(content, list):
                content = "".join(
                    str(part.get("text", ""))
                    for part in content
                    if isinstance(part, dict)
                )
            if not isinstance(content, str):
                raise TypeError
        except (IndexError, KeyError, TypeError) as exc:
            from backend.app.providers.base import ProviderProblem

            raise ProviderProblem(
                "invalid_provider_response",
                "provider response did not contain message content",
            ) from exc
        return parse_proposals(content)
