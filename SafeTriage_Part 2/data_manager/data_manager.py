"""DATA MANAGER - data_manager/data_manager.py

Role: Saves and loads incidents (JSON or SQLite), queries and filters them, and handles missing, corrupt or locked files.
Class in this file: DataManager
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from constants import STATUS_PENDING
from data_manager.incident_repository import IncidentRepository
from data_manager.load_result import LoadResult
from domain.final_decision import FinalDecision
from domain.incident import Incident


class DataManager:
    """Saves, loads, queries and deletes incidents through any IncidentRepository."""

    def __init__(self, repository: IncidentRepository) -> None:
        self._repository = repository    # aggregation: injected, not created here

    @property
    def repository(self) -> IncidentRepository:
        return self._repository

    @staticmethod
    def current_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def add_incident(self, incident: Incident) -> Incident:
        """Raises StorageError when the incident cannot be saved."""
        stamped = incident if incident.reported_at else replace(incident, reported_at=self.current_timestamp())
        return self._repository.add(stamped)

    def load_incidents(self) -> LoadResult:
        return self._repository.list_all()

    def find_incidents(self, status: str = "", priority: str = "") -> LoadResult:
        return self._repository.query(status, priority)

    def open_incidents(self) -> LoadResult:
        """Incidents still awaiting review (used by the duplicate check)."""
        return self._repository.query(status=STATUS_PENDING)

    def get_incident(self, incident_id: str) -> Incident | None:
        return self._repository.get(incident_id)

    def record_review(self, incident: Incident, status: str, final: FinalDecision) -> Incident:
        """Save an admin decision. Fails with ConflictError if the incident is no longer pending."""
        reviewed = incident.with_review(status, final, self.current_timestamp())
        return self._repository.update(reviewed, expected_status=incident.status)

    def delete_incident(self, incident_id: str) -> None:
        self._repository.delete(incident_id)
