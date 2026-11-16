"""AI MANAGER - ai_manager/fallback_ai_provider.py

Role: Builds prompts, calls the AI provider (Gemini, with Groq as backup), parses the JSON reply
and validates its schema. Every record passes through here.
Class in this file: FallbackAIProvider
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Sequence

from ai_manager.ai_provider import AIProvider
from errors.ai_timeout_error import AITimeoutError

logger = logging.getLogger("safetriage.ai")


class FallbackAIProvider(AIProvider):
    """Composite: it is an AIProvider made of other AIProviders (composition plus polymorphism).

    Each provider gets its own time limit. Without it, a primary that hangs (instead of failing
    quickly) would use up the caller's whole time budget and the backup would never be tried.
    """

    def __init__(self, providers: Sequence[AIProvider], *, timeout_seconds: float | None = None) -> None:
        if not providers:
            raise ValueError("FallbackAIProvider needs at least one provider")
        self._providers = list(providers)  # composition: the list is built and owned here
        self._timeout = timeout_seconds    # per provider; None means "wait for the provider itself"

    @property
    def provider_names(self) -> list[str]:
        return [type(provider).__name__ for provider in self._providers]

    @property
    def total_timeout(self) -> float | None:
        """Longest time one generate() call can take: every provider using its full limit."""
        return None if self._timeout is None else self._timeout * len(self._providers)

    def _call(self, provider: AIProvider, prompt: str, model: str) -> str:
        """Call one provider, giving up after the per-provider time limit."""
        if self._timeout is None:
            return provider.generate(prompt, model)
        outcome: dict[str, object] = {}

        def worker() -> None:
            try:
                outcome["text"] = provider.generate(prompt, model)
            except BaseException as error:  # handed back to the caller thread below
                outcome["error"] = error

        thread = threading.Thread(target=worker, daemon=True, name="safetriage-ai-provider")
        thread.start()
        thread.join(self._timeout)
        if thread.is_alive():
            raise AITimeoutError(f"no reply within {self._timeout:g} seconds")
        if "error" in outcome:
            raise outcome["error"]  # type: ignore[misc]
        return outcome["text"]  # type: ignore[return-value]

    def generate(self, prompt: str, model: str) -> str:
        last_error: Exception | None = None
        for provider in self._providers:
            try:
                text = self._call(provider, prompt, model)
            except Exception as error:  # any failure or timeout means "try the next provider"
                last_error = error
                logger.warning("%s failed, trying the next provider: %s", type(provider).__name__, error)
            else:
                logger.info("reply supplied by %s", type(provider).__name__)
                return text
        assert last_error is not None
        raise last_error
