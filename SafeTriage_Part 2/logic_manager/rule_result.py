"""LOGIC MANAGER - logic_manager/rule_result.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing,
duplicates and summary reports.
Class in this file: RuleResult
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleResult:
    """What a rule did: the (possibly new) level and, if it fired, why."""

    level: int
    reason: str = ""

    @property
    def fired(self) -> bool:
        return bool(self.reason)
