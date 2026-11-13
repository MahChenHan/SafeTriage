"""DATA MANAGER - data_manager/repository_factory.py

Role: Saves and loads incidents (JSON or SQLite), queries and filters them, and handles missing, corrupt or locked files.
Class in this file: RepositoryFactory
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import os

from constants import BACKEND_JSON, BACKEND_SQLITE, DATABASE_FILENAME, INCIDENTS_FILENAME
from data_manager.incident_repository import IncidentRepository
from data_manager.json_incident_repository import JsonIncidentRepository
from data_manager.sqlite_incident_repository import SqliteIncidentRepository
from errors.storage_error import StorageError


class RepositoryFactory:
    """Chooses the storage backend. Add a new backend by registering one more entry."""

    _BUILDERS = {
        BACKEND_JSON: lambda data_dir: JsonIncidentRepository(os.path.join(data_dir, INCIDENTS_FILENAME)),
        BACKEND_SQLITE: lambda data_dir: SqliteIncidentRepository(os.path.join(data_dir, DATABASE_FILENAME)),
    }

    @classmethod
    def create(cls, backend: str, data_dir: str) -> IncidentRepository:
        try:
            builder = cls._BUILDERS[backend.strip().lower()]
        except KeyError:
            raise StorageError(
                f"Unknown storage backend '{backend}'. Choose one of: {', '.join(cls._BUILDERS)}."
            ) from None
        return builder(data_dir)

    @classmethod
    def from_environment(cls) -> IncidentRepository:
        """DATA_DIR (default 'data') and SAFETRIAGE_STORAGE ('json' default, or 'sqlite')."""
        return cls.create(
            os.environ.get("SAFETRIAGE_STORAGE", BACKEND_JSON),
            os.environ.get("DATA_DIR", "data"),
        )
