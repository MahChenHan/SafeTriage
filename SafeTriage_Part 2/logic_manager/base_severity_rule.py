"""LOGIC MANAGER - logic_manager/base_severity_rule.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing,
duplicates and summary reports.
Class in this file: BaseSeverityRule
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from constants import (
    LEVEL_CRITICAL, LEVEL_HIGH, LEVEL_LOW, LEVEL_MEDIUM, MAX_SEVERITY, PRIORITY_LEVELS,
    SEVERITY_MODERATE, SEVERITY_SERIOUS,
)
from domain.ai_analysis import AIAnalysis
from logic_manager.rule_result import RuleResult
from logic_manager.triage_rule import TriageRule


class BaseSeverityRule(TriageRule):
    """Rule 1: the starting level comes from the AI severity (1-5). Ignores the incoming level."""

    @staticmethod
    def level_for(severity: int) -> int:
        if severity >= MAX_SEVERITY:
            return LEVEL_CRITICAL
        if severity == SEVERITY_SERIOUS:
            return LEVEL_HIGH
        if severity == SEVERITY_MODERATE:
            return LEVEL_MEDIUM
        return LEVEL_LOW

    def apply(self, analysis: AIAnalysis, level: int) -> RuleResult:
        base = self.level_for(analysis.severity)
        reason = f"Base level {PRIORITY_LEVELS[base]} from AI severity {analysis.severity}/{MAX_SEVERITY}"
        return RuleResult(base, reason)
