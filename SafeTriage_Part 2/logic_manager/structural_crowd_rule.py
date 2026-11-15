"""LOGIC MANAGER - logic_manager/structural_crowd_rule.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing, duplicates and summary reports.
Class in this file: StructuralCrowdRule
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from constants import LEVEL_HIGH, MANY_PEOPLE_THRESHOLD
from domain.ai_analysis import AIAnalysis
from logic_manager.minimum_level_rule import MinimumLevelRule


class StructuralCrowdRule(MinimumLevelRule):
    """Rule 4 (multi-condition): structural hazard AND >= 5 people exposed is at least High."""

    floor = LEVEL_HIGH

    def applies(self, analysis: AIAnalysis) -> bool:
        return "structural" in analysis.hazard_types and analysis.people_exposed >= MANY_PEOPLE_THRESHOLD

    def reason(self, analysis: AIAnalysis) -> str:
        return f"Raised to High: structural hazard with {analysis.people_exposed} people exposed"
