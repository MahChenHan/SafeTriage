"""DOMAIN MODELS (shared) - domain/decision.py

Role: Immutable records passed between the four managers. No I/O and no business rules.
Class in this file: Decision
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from domain.check_result import CheckResult


@dataclass(frozen=True)
class Decision:
    """The rule engine's recommendation for one incident."""

    outcome: str
    priority: str
    teams: tuple[str, ...]
    action: str
    notify_staff: bool = False
    needs_manual_review: bool = False
    reasons: tuple[str, ...] = ()
    duplicate_of: str = ""

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "outcome": self.outcome,
            "priority": self.priority,
            "teams": list(self.teams),
            "action": self.action,
            "notify_staff": self.notify_staff,
            "needs_manual_review": self.needs_manual_review,
            "reasons": list(self.reasons),
        }
        if self.duplicate_of:
            data["duplicate_of"] = self.duplicate_of
        return data

    @classmethod
    def from_dict(cls, data: object) -> Decision:
        if not isinstance(data, dict) or not isinstance(data.get("priority"), str):
            raise ValueError("decision needs a text priority")
        return cls(
            outcome=str(data.get("outcome", "")),
            priority=data["priority"],
            teams=CheckResult.require_str_list(data.get("teams"), "teams"),
            action=str(data.get("action", "")),
            notify_staff=bool(data.get("notify_staff", False)),
            needs_manual_review=bool(data.get("needs_manual_review", False)),
            reasons=CheckResult.require_str_list(data.get("reasons", []), "reasons"),
            duplicate_of=str(data.get("duplicate_of", "")),
        )

    def flagged_duplicate(self, duplicate_id: str, reason: str) -> Decision:
        """Copy of this decision marked as a possible duplicate. Priority is unchanged."""
        return replace(
            self,
            duplicate_of=duplicate_id,
            needs_manual_review=True,
            reasons=self.reasons + (reason,),
        )
