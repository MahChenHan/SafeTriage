"""LOGIC MANAGER - logic_manager/electrical_water_rule.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing, duplicates and summary reports.
Class in this file: ElectricalWaterRule
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from constants import LEVEL_CRITICAL
from domain.ai_analysis import AIAnalysis
from logic_manager.minimum_level_rule import MinimumLevelRule


class ElectricalWaterRule(MinimumLevelRule):
    """Rule 5 (multi-condition): electrical AND water hazards AND severity >= 3 is Critical."""

    floor = LEVEL_CRITICAL

    def applies(self, analysis: AIAnalysis) -> bool:
        return {"electrical", "water"} <= set(analysis.hazard_types) and analysis.severity >= 3

    def reason(self, analysis: AIAnalysis) -> str:
        return "Raised to Critical: electrical + water hazard at severity 3 or above"
