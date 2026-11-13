"""DATA MANAGER - data_manager/json_incident_repository.py

Role: Saves and loads incidents (JSON or SQLite), queries and filters them, and handles missing, corrupt or locked files.
Class in this file: JsonIncidentRepository
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from data_manager.file_lock import FileLock
from data_manager.incident_filter import IncidentFilter
from data_manager.incident_repository import IncidentRepository
from data_manager.load_result import LoadResult
from domain.incident import Incident
from errors.conflict_error import ConflictError
from errors.incident_not_found_error import IncidentNotFoundError
from errors.storage_error import StorageError


logger = logging.getLogger("safetriage.data")


class JsonIncidentRepository(IncidentRepository):
    """Stores all incidents in one JSON list (the Part 1 file format)."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = FileLock(path)        # composition: owned and used only here

    @property
    def path(self) -> str:
        return self._path

    # ----------------------------------------------------------- file access
    def _quarantine(self, reason: str) -> str:
        """Move a corrupt data file aside so it is never overwritten. Returns a warning."""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup = f"{self._path}.corrupt-{stamp}"
        logger.error("Corrupt data file %s (%s)", self._path, reason)
        try:
            os.replace(self._path, backup)
        except OSError as error:
            return f"Data file was unreadable ({reason}) and could not be backed up ({error}). Starting empty."
        return f"Data file was unreadable ({reason}). Backed up to {backup}; starting with an empty list."

    def _read_raw(self) -> tuple[list[dict], str]:
        """Return (raw record dicts, warning). Damaged-but-dict records are kept as-is."""
        if not os.path.exists(self._path):
            return [], ""
        try:
            with open(self._path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            return [], self._quarantine(str(error))
        if not isinstance(data, list):
            return [], self._quarantine("top level is not a list")
        records = [item for item in data if isinstance(item, dict)]
        warning = ""
        if len(records) != len(data):
            warning = f"{len(data) - len(records)} malformed entries in the data file were ignored."
            logger.warning(warning)
        return records, warning

    def _write_raw(self, records: list[dict]) -> None:
        """Atomically write all records (temp file + rename). Raises StorageError."""
        directory = os.path.dirname(self._path) or "."
        temp_path = ""
        try:
            os.makedirs(directory, exist_ok=True)
            handle_fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
            with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
                json.dump(records, handle, indent=2, ensure_ascii=False)
            os.replace(temp_path, self._path)
        except (OSError, TypeError, ValueError) as error:
            logger.error("Could not save incidents: %s", error)
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            raise StorageError(f"Could not save incidents: {error}") from error

    @staticmethod
    def _next_id(records: list[dict]) -> str:
        highest = 0
        for record in records:
            text = str(record.get("id", ""))
            if text.startswith("INC-") and text[4:].isdecimal():
                highest = max(highest, int(text[4:]))
        return f"INC-{highest + 1:04d}"

    @contextmanager
    def _locked(self) -> Iterator[None]:
        try:
            with self._lock.held():
                yield
        except OSError as error:
            logger.error("Could not lock incident storage: %s", error)
            raise StorageError(f"Could not access incident storage: {error}") from error

    # ------------------------------------------------------------------ CRUD
    def add(self, incident: Incident) -> Incident:
        with self._locked():
            records, _ = self._read_raw()
            saved = incident.with_id(self._next_id(records))
            records.append(saved.to_dict())
            self._write_raw(records)
        return saved

    def list_all(self) -> LoadResult:
        records, warning = self._read_raw()
        incidents: list[Incident] = []
        for record in records:
            try:
                incidents.append(Incident.from_dict(record))
            except ValueError:
                continue
        warnings = [warning] if warning else []
        skipped = len(records) - len(incidents)
        if skipped:
            message = f"{skipped} damaged incident(s) were skipped. They are left unchanged in the data file."
            logger.warning(message)
            warnings.append(message)
        return LoadResult(incidents, tuple(warnings))

    def get(self, incident_id: str) -> Incident | None:
        return next((item for item in self.list_all().incidents if item.id == incident_id), None)

    def query(self, status: str = "", priority: str = "") -> LoadResult:
        result = self.list_all()
        return LoadResult(IncidentFilter.apply(result.incidents, status, priority), result.warnings)

    def update(self, incident: Incident, expected_status: str | None = None) -> Incident:
        with self._locked():
            records, _ = self._read_raw()
            for index, record in enumerate(records):
                if record.get("id") != incident.id:
                    continue
                if expected_status is not None and record.get("status") != expected_status:
                    raise ConflictError(
                        f"Incident {incident.id} was already changed by someone else "
                        f"(now '{record.get('status')}')."
                    )
                records[index] = incident.to_dict()
                self._write_raw(records)
                return incident
        raise IncidentNotFoundError(f"Incident {incident.id} was not found.")

    def delete(self, incident_id: str) -> None:
        with self._locked():
            records, _ = self._read_raw()
            remaining = [record for record in records if record.get("id") != incident_id]
            if len(remaining) == len(records):
                raise IncidentNotFoundError(f"Incident {incident_id} was not found.")
            self._write_raw(remaining)
