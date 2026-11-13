"""DOMAIN MODELS (shared) - domain/hazard_report.py

Role: Immutable records passed between the four managers. No I/O and no business rules.
Class in this file: HazardReport
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HazardReport:
    """What the employee typed (already validated by IOManager)."""

    reporter_id: str
    location: str
    description: str
