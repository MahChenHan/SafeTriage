"""AI MANAGER - ai_manager/ai_provider.py

Role: Builds prompts, calls the Gemini API, parses the JSON reply and validates its schema. Every record passes through here.
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Contract for anything that can turn a prompt into reply text."""

    @abstractmethod
    def generate(self, prompt: str, model: str) -> str:
        """Return the model's raw text reply. Raise any exception on failure."""
