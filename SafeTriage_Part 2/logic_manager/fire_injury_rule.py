"""LOGIC MANAGER - logic_manager/fire_injury_rule.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing, duplicates and summary reports.
Class in this file: FireInjuryRule
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from constants import LEVEL_CRITICAL
from domain.ai_analysis import AIAnalysis
from logic_manager.minimum_level_rule import MinimumLevelRule


class FireInjuryRule(MinimumLevelRule):
    """Rule 6 (multi-condition): a fire hazard AND an injury is Critical."""

    floor = LEVEL_CRITICAL

    def applies(self, analysis: AIAnalysis) -> bool:
        return "fire" in analysis.hazard_types and analysis.injury_present

    def reason(self, analysis: AIAnalysis) -> str:
        return "Raised to Critical: fire hazard with injury"
