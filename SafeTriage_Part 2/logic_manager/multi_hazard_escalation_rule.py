"""LOGIC MANAGER - logic_manager/multi_hazard_escalation_rule.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing, duplicates and summary reports.
Class in this file: MultiHazardEscalationRule
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from constants import PRIORITY_LEVELS
from domain.ai_analysis import AIAnalysis
from logic_manager.rule_result import RuleResult
from logic_manager.triage_rule import TriageRule


class MultiHazardEscalationRule(TriageRule):
    """Rule 2: two or more distinct hazards escalate one level (capped at Critical)."""

    def apply(self, analysis: AIAnalysis, level: int) -> RuleResult:
        hazards = set(analysis.hazard_types)
        if len(hazards) < 2:
            return RuleResult(level)
        raised = min(level + 1, len(PRIORITY_LEVELS) - 1)
        return RuleResult(
            raised, f"Escalated one level: {len(hazards)} hazards present ({', '.join(sorted(hazards))})"
        )
