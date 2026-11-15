"""AI MANAGER - ai_manager/ai_manager.py

Role: Builds prompts, calls the Gemini API, parses the JSON reply and validates its schema. Every record passes through here.
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from collections.abc import Callable

from ai_manager.ai_provider import AIProvider
from ai_manager.prompt_builder import PromptBuilder
from ai_manager.response_validator import ResponseValidator
from constants import DEFAULT_MODEL, ERROR_API_FAILURE, ERROR_MALFORMED, MAX_ATTEMPTS, REQUEST_TIMEOUT_SECONDS, RETRY_DELAY_SECONDS
from domain.ai_result import AIResult
from domain.hazard_report import HazardReport
from errors.ai_timeout_error import AITimeoutError
from errors.invalid_ai_response_error import InvalidAIResponseError


logger = logging.getLogger("safetriage.ai")


class AIManager:
    """Runs one report through the AI provider, with timeout, retries and validation."""

    def __init__(
        self,
        provider: AIProvider,
        *,
        model: str | None = None,
        max_attempts: int = MAX_ATTEMPTS,
        retry_delay: float = RETRY_DELAY_SECONDS,
        timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._provider = provider                      # aggregation (injected)
        self._prompt_builder = PromptBuilder()         # composition (owned)
        self._validator = ResponseValidator()          # composition (owned)
        self._model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
        self._max_attempts = max(1, max_attempts)
        self._retry_delay = retry_delay
        self._timeout = timeout_seconds
        self._sleep = sleep

    @property
    def model(self) -> str:
        return self._model

    def analyse_report(self, report: HazardReport) -> AIResult:
        """Send one report through the AI and return an AIResult. Never raises."""
        prompt = self._prompt_builder.build(report)
        error_type, error_text = ERROR_API_FAILURE, "no attempt made"

        for attempt in range(1, self._max_attempts + 1):
            try:
                raw = self._call_with_timeout(prompt)
            except Exception as error:  # broad on purpose: an API problem must never crash the app
                error_type = ERROR_API_FAILURE
                error_text = f"{type(error).__name__}: {error}"
                logger.warning("API call failed (attempt %d/%d): %s", attempt, self._max_attempts, error_text)
            else:
                try:
                    analysis = self._validator.validate(self._validator.parse_json_text(raw))
                except InvalidAIResponseError as problem:
                    error_type, error_text = ERROR_MALFORMED, str(problem)
                    logger.warning("Malformed AI output (attempt %d/%d): %s", attempt, self._max_attempts, problem)
                else:
                    return AIResult(ok=True, analysis=analysis, model=self._model, attempts=attempt)
            if attempt < self._max_attempts:
                self._sleep(self._retry_delay)

        logger.error("AI analysis failed after %d attempts: %s", self._max_attempts, error_text)
        return AIResult(
            ok=False, analysis=None, model=self._model, attempts=self._max_attempts,
            error_type=error_type, error=error_text,
        )

    def _call_with_timeout(self, prompt: str) -> str:
        """Call the provider but give up after the timeout (a hung connection must not hang the app)."""
        outcome: dict[str, object] = {}

        def worker() -> None:
            try:
                outcome["text"] = self._provider.generate(prompt, self._model)
            except BaseException as error:  # handed back to the caller thread below
                outcome["error"] = error

        thread = threading.Thread(target=worker, daemon=True, name="safetriage-ai-call")
        thread.start()
        thread.join(self._timeout)
        if thread.is_alive():
            raise AITimeoutError(f"no reply within {self._timeout:g} seconds")
        if "error" in outcome:
            raise outcome["error"]  # type: ignore[misc]
        return outcome["text"]  # type: ignore[return-value]
