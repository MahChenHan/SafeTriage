"""DATA MANAGER - data_manager/incident_filter.py

Role: Saves and loads incidents (JSON or SQLite), queries and filters them, and handles missing, corrupt or locked files.
Class in this file: IncidentFilter
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from domain.incident import Incident


class IncidentFilter:
    """Shared in-memory filter: an empty argument means 'do not filter on this'.

    Priority is matched against the admin's final decision when there is one,
    otherwise against the rule engine's recommendation.
    """

    @staticmethod
    def apply(incidents: list[Incident], status: str = "", priority: str = "") -> list[Incident]:
        return [
            item for item in incidents
            if (not status or item.status == status) and (not priority or item.effective_priority == priority)
        ]
