"""LOGIC MANAGER - logic_manager/summary_report_builder.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing, duplicates and summary reports.
Class in this file: SummaryReportBuilder
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from collections import Counter

from constants import ALL_PRIORITIES, STATUS_PENDING
from domain.incident import Incident
from logic_manager.duplicate_detector import DuplicateDetector
from logic_manager.summary_report import SummaryReport


class SummaryReportBuilder:
    """Counts, rankings and urgent-backlog figures over a list of incidents."""

    def __init__(self, hotspot_count: int = 3) -> None:
        self._hotspot_count = hotspot_count

    def build(self, incidents: list[Incident]) -> SummaryReport:
        by_status = Counter(item.status for item in incidents)
        by_priority = Counter(item.effective_priority for item in incidents)
        hazards: Counter[str] = Counter()
        places: Counter[str] = Counter()
        place_label: dict[str, str] = {}
        for item in incidents:
            if item.ai.analysis is not None:
                hazards.update(item.ai.analysis.hazard_types)
            key = DuplicateDetector.normalise_location(item.location)
            places[key] += 1
            place_label.setdefault(key, item.location.strip())

        ranked_places = sorted(places.items(), key=lambda pair: (-pair[1], pair[0]))[: self._hotspot_count]
        return SummaryReport(
            total=len(incidents),
            by_status={status: by_status[status] for status in by_status},
            by_priority={p: by_priority[p] for p in ALL_PRIORITIES if by_priority[p]},
            by_hazard=dict(sorted(hazards.items(), key=lambda pair: (-pair[1], pair[0]))),
            hotspots=[(place_label[key], count) for key, count in ranked_places],
            pending_urgent=sum(
                1 for item in incidents
                if item.status == STATUS_PENDING and item.effective_priority in ("Critical", "High", "Unrated")
            ),
            low_confidence=sum(1 for item in incidents if item.decision.needs_manual_review),
            ai_unavailable=sum(1 for item in incidents if not item.ai.ok),
        )