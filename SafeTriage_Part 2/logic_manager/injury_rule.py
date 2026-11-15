"""LOGIC MANAGER - logic_manager/injury_rule.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing, duplicates and summary reports.
Class in this file: InjuryRule
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from constants import LEVEL_HIGH
from domain.ai_analysis import AIAnalysis
from logic_manager.minimum_level_rule import MinimumLevelRule


class InjuryRule(MinimumLevelRule):
    """Rule 3: any reported injury is at least High."""

    floor = LEVEL_HIGH

    def applies(self, analysis: AIAnalysis) -> bool:
        return analysis.injury_present

    def reason(self, analysis: AIAnalysis) -> str:
        return "Raised to High: injury reported"
