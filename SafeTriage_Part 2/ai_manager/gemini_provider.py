"""AI MANAGER - ai_manager/gemini_provider.py

Role: Builds prompts, calls the Gemini API, parses the JSON reply and validates its schema. Every record passes through here.
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import os

from ai_manager.ai_provider import AIProvider


class GeminiProvider(AIProvider):
    """Google Gemini implementation. The only class that touches the network."""

    def __init__(self, api_key: str | None = None) -> None:
        # Read lazily from the environment so the key is never stored in the repo.
        self._api_key = api_key

    def generate(self, prompt: str, model: str) -> str:
        from google import genai  # imported here so tests run without the SDK or a key

        client = genai.Client(api_key=self._api_key or os.environ.get("GEMINI_API_KEY"))
        interaction = client.interactions.create(model=model, input=prompt)
        return interaction.output_text
