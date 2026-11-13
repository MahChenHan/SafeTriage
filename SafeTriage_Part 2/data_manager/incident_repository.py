"""DATA MANAGER - data_manager/incident_repository.py

Role: Saves and loads incidents (JSON or SQLite), queries and filters them, and handles missing, corrupt or locked files.
Class in this file: IncidentRepository
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from data_manager.load_result import LoadResult
from domain.incident import Incident


class IncidentRepository(ABC):
    """Contract every storage backend must honour."""

    @abstractmethod
    def add(self, incident: Incident) -> Incident:
        """Create: store a new incident and return it with its newly assigned id."""

    @abstractmethod
    def get(self, incident_id: str) -> Incident | None:
        """Read one incident, or None when it does not exist (or is too damaged to read)."""

    @abstractmethod
    def list_all(self) -> LoadResult:
        """Read every usable incident, oldest first."""

    @abstractmethod
    def query(self, status: str = "", priority: str = "") -> LoadResult:
        """Read incidents filtered by status and/or priority."""

    @abstractmethod
    def update(self, incident: Incident, expected_status: str | None = None) -> Incident:
        """Update: replace the stored incident with the same id.

        Raises IncidentNotFoundError if it is missing, ConflictError if ``expected_status``
        is given and the stored status is different (someone else changed it first).
        """

    @abstractmethod
    def delete(self, incident_id: str) -> None:
        """Delete: remove an incident. Raises IncidentNotFoundError if it is missing."""
