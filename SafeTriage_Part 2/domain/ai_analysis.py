"""DOMAIN MODELS (shared) - domain/ai_analysis.py

Role: Immutable records passed between the four managers. No I/O and no business rules.
Class in this file: AIAnalysis
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.check_result import CheckResult


@dataclass(frozen=True)
class AIAnalysis:
    """Structured facts the AI extracted from a report (never a priority)."""

    is_hazard_report: bool
    hazard_types: tuple[str, ...]
    severity: int
    injury_present: bool
    people_exposed: int
    confidence: float
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_hazard_report": self.is_hazard_report,
            "hazard_types": list(self.hazard_types),
            "severity": self.severity,
            "injury_present": self.injury_present,
            "people_exposed": self.people_exposed,
            "confidence": self.confidence,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: object) -> AIAnalysis:
        """Rebuild a stored analysis. Raises ValueError if any field is unusable."""
        if not isinstance(data, dict):
            raise ValueError("analysis must be an object")
        for key in ("hazard_types", "severity", "injury_present", "people_exposed", "confidence", "summary"):
            if key not in data:
                raise ValueError(f"analysis is missing '{key}'")
        if not CheckResult.is_int(data["severity"]) or not CheckResult.is_int(data["people_exposed"]):
            raise ValueError("severity and people_exposed must be whole numbers")
        if not CheckResult.is_number(data["confidence"]):
            raise ValueError("confidence must be a number")
        if not isinstance(data["injury_present"], bool) or not isinstance(data["summary"], str):
            raise ValueError("injury_present must be true/false and summary must be text")
        return cls(
            is_hazard_report=bool(data.get("is_hazard_report", True)),
            hazard_types=CheckResult.require_str_list(data["hazard_types"], "hazard_types"),
            severity=data["severity"],
            injury_present=data["injury_present"],
            people_exposed=data["people_exposed"],
            confidence=float(data["confidence"]),
            summary=data["summary"],
        )
