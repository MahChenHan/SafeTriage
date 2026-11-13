"""LOGIC MANAGER - logic_manager/summary_report.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing, duplicates and summary reports.
Class in this file: SummaryReport
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SummaryReport:
    """Overview of every stored incident (Part 2 new feature)."""

    total: int
    by_status: dict[str, int] = field(default_factory=dict)
    by_priority: dict[str, int] = field(default_factory=dict)
    by_hazard: dict[str, int] = field(default_factory=dict)
    hotspots: list[tuple[str, int]] = field(default_factory=list)
    pending_urgent: int = 0
    low_confidence: int = 0
    ai_unavailable: int = 0
    reviewed: int = 0
    overridden: int = 0
    override_rate: float = 0.0
    average_review_minutes: float | None = None
