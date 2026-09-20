from __future__ import annotations

from backend.app.core.config import Settings
from backend.app.providers.base import CorrectionProvider
from backend.app.providers.gemini import GeminiProvider
from backend.app.providers.openai_compatible import OpenAICompatibleProvider


def provider_for(name: str, settings: Settings) -> CorrectionProvider:
    if name == "gemini":
        return GeminiProvider(
            settings.gemini_base_url,
            settings.gemini_model,
        )
    if name == "openai_compatible":
        base_url = settings.hosted_provider_base_url or settings.openai_base_url
        model = settings.hosted_provider_model or settings.openai_model
        return OpenAICompatibleProvider(base_url, model)
    raise ValueError("unsupported_provider")
