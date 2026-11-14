"""LOGIC MANAGER - logic_manager/minimum_level_rule.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing, duplicates and summary reports.
Class in this file: MinimumLevelRule
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from abc import abstractmethod

from constants import LEVEL_HIGH
from domain.ai_analysis import AIAnalysis
from logic_manager.rule_result import RuleResult
from logic_manager.triage_rule import TriageRule


class MinimumLevelRule(TriageRule):
    """Abstract specialisation: when ``applies`` is true, raise to at least ``floor``.

    The shared behaviour (compare, raise, never lower, build the reason) lives here
    once; subclasses only say WHEN they apply (template method pattern).
    """

    floor: int = LEVEL_HIGH

    @abstractmethod
    def applies(self, analysis: AIAnalysis) -> bool:
        """True when this rule's condition holds for the analysis."""

    @abstractmethod
    def reason(self, analysis: AIAnalysis) -> str:
        """Human-readable explanation shown to the admin when the rule fires."""

    def apply(self, analysis: AIAnalysis, level: int) -> RuleResult:
        if self.applies(analysis) and level < self.floor:
            return RuleResult(self.floor, self.reason(analysis))
        return RuleResult(level)
