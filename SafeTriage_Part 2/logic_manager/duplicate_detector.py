"""LOGIC MANAGER - logic_manager/duplicate_detector.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing, duplicates and summary reports.
Class in this file: DuplicateDetector
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from constants import DUPLICATE_WINDOW_HOURS
from domain.ai_analysis import AIAnalysis
from domain.incident import Incident


class DuplicateDetector:
    """Multi-condition duplicate rule: location + shared hazard + time window."""

    def __init__(self, window_hours: float = DUPLICATE_WINDOW_HOURS) -> None:
        self._window_hours = window_hours

    @staticmethod
    def normalise_location(text: str) -> str:
        """'  Lab 3 ' and 'lab   3' count as the same place."""
        return " ".join(str(text).lower().split())

    @staticmethod
    def hours_between(first: str, second: str) -> float | None:
        """Absolute gap in hours between two ISO timestamps, or None if either is unreadable."""
        try:
            gap = datetime.fromisoformat(second) - datetime.fromisoformat(first)
        except (TypeError, ValueError):
            return None
        return abs(gap.total_seconds()) / 3600

    def find(self, location: str, analysis: AIAnalysis | None, reported_at: str,
             open_incidents: Iterable[Incident]) -> tuple[str, str]:
        """Return (incident_id, reason) of the most recent likely duplicate, or ("", "").

        A new report is a likely duplicate of an open incident when ALL hold:
          - the new report is a real hazard report (AI analysis available)
          - same location (ignoring case and extra spaces)
          - at least one hazard type in common
          - reported within the time window of each other
        """
        if analysis is None or not analysis.is_hazard_report:
            return "", ""
        place = self.normalise_location(location)
        hazards = set(analysis.hazard_types)
        best_id, best_reason, best_time = "", "", ""

        for record in open_incidents:
            if self.normalise_location(record.location) != place:
                continue
            other = record.ai.analysis
            if other is None:
                continue
            shared = hazards & set(other.hazard_types)
            if not shared:
                continue
            gap = self.hours_between(record.reported_at, reported_at)
            if gap is None or gap > self._window_hours:
                continue
            if record.reported_at >= best_time:
                best_id, best_time = record.id, record.reported_at
                best_reason = (
                    f"Possible duplicate of {best_id}: same location, shared hazard "
                    f"({', '.join(sorted(shared))}), reported {round(gap * 60)} min apart"
                )
        return best_id, best_reason
