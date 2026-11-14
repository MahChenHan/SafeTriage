"""LOGIC MANAGER - logic_manager/base_severity_rule.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing, duplicates and summary reports.
Class in this file: BaseSeverityRule
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from constants import PRIORITY_LEVELS
from domain.ai_analysis import AIAnalysis
from logic_manager.rule_result import RuleResult
from logic_manager.triage_rule import TriageRule


class BaseSeverityRule(TriageRule):
    """Rule 1: the starting level comes from the AI severity (1-5)."""

    @staticmethod
    def level_for(severity: int) -> int:
        if severity >= 5:
            return 3
        if severity == 4:
            return 2
        if severity == 3:
            return 1
        return 0

    def apply(self, analysis: AIAnalysis, level: int) -> RuleResult:
        base = self.level_for(analysis.severity)
        return RuleResult(base, f"Base level {PRIORITY_LEVELS[base]} from AI severity {analysis.severity}/5")
