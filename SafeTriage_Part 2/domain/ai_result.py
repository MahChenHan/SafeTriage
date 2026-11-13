"""DOMAIN MODELS (shared) - domain/ai_result.py

Role: Immutable records passed between the four managers. No I/O and no business rules.
Class in this file: AIResult
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.ai_analysis import AIAnalysis
from domain.check_result import CheckResult


@dataclass(frozen=True)
class AIResult:
    """Outcome of one trip through the AI: either an analysis or a failure description."""

    ok: bool
    analysis: AIAnalysis | None
    model: str = ""
    attempts: int = 0
    error_type: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "model": self.model,
            "attempts": self.attempts,
            "error_type": self.error_type,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: object) -> AIResult:
        if data is None:
            return cls(ok=False, analysis=None, error_type="unknown")
        if not isinstance(data, dict):
            raise ValueError("ai must be an object")
        raw_analysis = data.get("analysis")
        analysis = AIAnalysis.from_dict(raw_analysis) if raw_analysis is not None else None
        return cls(
            ok=analysis is not None and bool(data.get("ok", True)),
            analysis=analysis,
            model=str(data.get("model", "")),
            attempts=data["attempts"] if CheckResult.is_int(data.get("attempts")) else 0,
            error_type=str(data.get("error_type", "")),
            error=str(data.get("error", "")),
        )
