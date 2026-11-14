"""LOGIC MANAGER - logic_manager/triage_rule.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing, duplicates and summary reports.
Class in this file: TriageRule
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.ai_analysis import AIAnalysis
from logic_manager.rule_result import RuleResult


class TriageRule(ABC):
    """Abstract base: one business rule that may raise the priority level."""

    @abstractmethod
    def apply(self, analysis: AIAnalysis, level: int) -> RuleResult:
        """Return the new level (never lower than ``level``) and a reason if the rule fired."""
