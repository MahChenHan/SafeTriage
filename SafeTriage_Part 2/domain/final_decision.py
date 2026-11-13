"""DOMAIN MODELS (shared) - domain/final_decision.py

Role: Immutable records passed between the four managers. No I/O and no business rules.
Class in this file: FinalDecision
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.check_result import CheckResult


@dataclass(frozen=True)
class FinalDecision:
    """What the human administrator confirmed, overrode or rejected."""

    priority: str
    teams: tuple[str, ...]
    action: str
    note: str
    reviewed_by: str
    reviewed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "priority": self.priority,
            "teams": list(self.teams),
            "action": self.action,
            "note": self.note,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at,
        }

    @classmethod
    def from_dict(cls, data: object) -> FinalDecision:
        if not isinstance(data, dict) or not isinstance(data.get("priority"), str):
            raise ValueError("final decision needs a text priority")
        return cls(
            priority=data["priority"],
            teams=CheckResult.require_str_list(data.get("teams"), "teams"),
            action=str(data.get("action", "")),
            note=str(data.get("note", "")),
            reviewed_by=str(data.get("reviewed_by", "")),
            reviewed_at=str(data.get("reviewed_at", "")),
        )
