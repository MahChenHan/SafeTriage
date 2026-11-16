"""LOGIC MANAGER - logic_manager/electrical_water_rule.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing,
duplicates and summary reports.
Class in this file: ElectricalWaterRule
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from constants import ELECTRICAL_WATER_MIN_SEVERITY, LEVEL_CRITICAL
from domain.ai_analysis import AIAnalysis
from logic_manager.minimum_level_rule import MinimumLevelRule


class ElectricalWaterRule(MinimumLevelRule):
    """Rule 5 (multi-condition): electrical AND water hazards AND severity >= 3 is Critical."""

    floor = LEVEL_CRITICAL

    def applies(self, analysis: AIAnalysis) -> bool:
        has_both = {"electrical", "water"} <= set(analysis.hazard_types)
        return has_both and analysis.severity >= ELECTRICAL_WATER_MIN_SEVERITY

    def reason(self, analysis: AIAnalysis) -> str:
        return f"Raised to Critical: electrical + water hazard at severity {ELECTRICAL_WATER_MIN_SEVERITY} or above"
