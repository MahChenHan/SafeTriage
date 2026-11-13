"""AI MANAGER - ai_manager/groq_provider.py

Role: Backup AI provider. Calls Groq's free, OpenAI-compatible chat API when the primary (Gemini) fails.
Class in this file: GroqProvider
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable

from ai_manager.ai_provider import AIProvider
from constants import DEFAULT_GROQ_MODEL, GROQ_CHAT_URL

Transport = Callable[[urllib.request.Request, float], bytes]


def _http_post(request: urllib.request.Request, timeout: float) -> bytes:
    """The only function that touches the network. Tests replace it with a fake."""
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        # Groq's error body says why (for example: invalid key, or model not found). Keep it for the log.
        detail = error.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Groq HTTP {error.code}: {detail}") from error


class GroqProvider(AIProvider):
    """Groq implementation of AIProvider. Ignores the model name passed in: it uses its own (GROQ_MODEL)."""

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 transport: Transport = _http_post, timeout: float = 30.0) -> None:
        self._api_key = api_key
        self._model = model or os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        self._transport = transport
        self._timeout = timeout

    @property
    def model(self) -> str:
        return self._model

    def build_payload(self, prompt: str) -> dict:
        """The JSON body sent to Groq. JSON mode asks the model to return a JSON object."""
        return {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }

    @staticmethod
    def extract_text(raw: bytes) -> str:
        """Pull the reply text out of Groq's response. Raises ValueError if the shape is unexpected."""
        try:
            return json.loads(raw)["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise ValueError(f"unexpected Groq response: {error}") from error

    def generate(self, prompt: str, model: str) -> str:
        key = self._api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY is not set")
        request = urllib.request.Request(
            GROQ_CHAT_URL,
            data=json.dumps(self.build_payload(prompt)).encode("utf-8"),
            headers={
                # Groq's gateway rejects Python's default User-Agent (403), so identify the app explicitly.
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "SafeTriage/1.0",
            },
            method="POST",
        )
        return self.extract_text(self._transport(request, self._timeout))