"""DATA MANAGER - data_manager/sqlite_incident_repository.py

Role: Saves and loads incidents (JSON or SQLite), queries and filters them, and handles missing, corrupt or locked files.
Class in this file: SqliteIncidentRepository
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from data_manager.incident_repository import IncidentRepository
from data_manager.load_result import LoadResult
from domain.incident import Incident
from errors.conflict_error import ConflictError
from errors.incident_not_found_error import IncidentNotFoundError
from errors.storage_error import StorageError


logger = logging.getLogger("safetriage.data")


class SqliteIncidentRepository(IncidentRepository):
    """Stores incidents in a SQLite database (advanced feature: database integration).

    Flat fields are real columns so they can be queried with SQL; the nested AI result
    and decisions are stored as JSON text columns.
    """

    _SCHEMA = """
        CREATE TABLE IF NOT EXISTS incidents (
            seq                INTEGER PRIMARY KEY AUTOINCREMENT,
            id                 TEXT UNIQUE,
            reporter_id        TEXT NOT NULL,
            location           TEXT NOT NULL,
            description        TEXT NOT NULL,
            status             TEXT NOT NULL,
            reported_at        TEXT NOT NULL,
            updated_at         TEXT NOT NULL DEFAULT '',
            effective_priority TEXT NOT NULL,
            ai_json            TEXT NOT NULL,
            decision_json      TEXT NOT NULL,
            final_json         TEXT
        )
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._startup_warning = ""
        self.__prepare_database()

    @property
    def path(self) -> str:
        return self._db_path

    # Name-mangled (truly private) helpers: nothing outside this class should call them.
    def __connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def __prepare_database(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._db_path) or ".", exist_ok=True)
            self.__create_schema()
        except sqlite3.DatabaseError as error:
            # Not a database / damaged file: set it aside (never overwrite) and start fresh.
            self._startup_warning = self.__quarantine(str(error))
            self.__create_schema_or_fail()
        except (OSError, sqlite3.Error) as error:
            raise StorageError(f"Could not open the incident database: {error}") from error

    def __create_schema(self) -> None:
        with closing(self.__connect()) as connection, connection:
            connection.execute(self._SCHEMA)
            connection.execute("SELECT COUNT(*) FROM incidents").fetchone()

    def __create_schema_or_fail(self) -> None:
        try:
            self.__create_schema()
        except (OSError, sqlite3.Error) as error:
            raise StorageError(f"Could not create a new incident database: {error}") from error

    def __quarantine(self, reason: str) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup = f"{self._db_path}.corrupt-{stamp}"
        logger.error("Corrupt database %s (%s)", self._db_path, reason)
        try:
            os.replace(self._db_path, backup)
        except OSError as error:
            raise StorageError(f"Database is unreadable ({reason}) and could not be backed up: {error}") from error
        return f"Database was unreadable ({reason}). Backed up to {backup}; starting with an empty database."

    @staticmethod
    def _to_incident(row: sqlite3.Row) -> Incident:
        """Rebuild an Incident from a row. Raises ValueError if the row is damaged."""
        try:
            data = {
                "id": row["id"], "reporter_id": row["reporter_id"], "location": row["location"],
                "description": row["description"], "status": row["status"],
                "reported_at": row["reported_at"], "updated_at": row["updated_at"],
                "ai": json.loads(row["ai_json"]), "decision": json.loads(row["decision_json"]),
            }
            if row["final_json"] is not None:
                data["final"] = json.loads(row["final_json"])
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError(str(error)) from error
        return Incident.from_dict(data)

    @staticmethod
    def _values(incident: Incident) -> dict[str, object]:
        return {
            "reporter_id": incident.reporter_id, "location": incident.location,
            "description": incident.description, "status": incident.status,
            "reported_at": incident.reported_at, "updated_at": incident.updated_at,
            "effective_priority": incident.effective_priority,
            "ai_json": json.dumps(incident.ai.to_dict(), ensure_ascii=False),
            "decision_json": json.dumps(incident.decision.to_dict(), ensure_ascii=False),
            "final_json": json.dumps(incident.final.to_dict(), ensure_ascii=False) if incident.final else None,
        }

    def _collect(self, rows: list[sqlite3.Row]) -> LoadResult:
        incidents, skipped = [], 0
        for row in rows:
            try:
                incidents.append(self._to_incident(row))
            except ValueError:
                skipped += 1
        warnings = [self._startup_warning] if self._startup_warning else []
        self._startup_warning = ""
        if skipped:
            message = f"{skipped} damaged incident(s) were skipped. They are left unchanged in the database."
            logger.warning(message)
            warnings.append(message)
        return LoadResult(incidents, tuple(warnings))

    # ------------------------------------------------------------------ CRUD
    def add(self, incident: Incident) -> Incident:
        values = self._values(incident)
        try:
            with closing(self.__connect()) as connection, connection:
                cursor = connection.execute(
                    "INSERT INTO incidents (reporter_id, location, description, status, reported_at, "
                    "updated_at, effective_priority, ai_json, decision_json, final_json) "
                    "VALUES (:reporter_id, :location, :description, :status, :reported_at, "
                    ":updated_at, :effective_priority, :ai_json, :decision_json, :final_json)",
                    values,
                )
                new_id = f"INC-{cursor.lastrowid:04d}"
                connection.execute("UPDATE incidents SET id = ? WHERE seq = ?", (new_id, cursor.lastrowid))
        except sqlite3.Error as error:
            logger.error("Could not add incident: %s", error)
            raise StorageError(f"Could not save incident: {error}") from error
        return incident.with_id(new_id)

    def list_all(self) -> LoadResult:
        return self.query()

    def query(self, status: str = "", priority: str = "") -> LoadResult:
        try:
            with closing(self.__connect()) as connection:
                rows = connection.execute(
                    "SELECT * FROM incidents WHERE (? = '' OR status = ?) "
                    "AND (? = '' OR effective_priority = ?) ORDER BY seq",
                    (status, status, priority, priority),
                ).fetchall()
        except sqlite3.Error as error:
            logger.error("Could not query incidents: %s", error)
            raise StorageError(f"Could not read incidents: {error}") from error
        return self._collect(rows)

    def get(self, incident_id: str) -> Incident | None:
        try:
            with closing(self.__connect()) as connection:
                row = connection.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
        except sqlite3.Error as error:
            raise StorageError(f"Could not read incident: {error}") from error
        if row is None:
            return None
        try:
            return self._to_incident(row)
        except ValueError:
            return None

    def update(self, incident: Incident, expected_status: str | None = None) -> Incident:
        values = self._values(incident)
        values.update(id=incident.id, expected=expected_status)
        try:
            with closing(self.__connect()) as connection, connection:
                cursor = connection.execute(
                    "UPDATE incidents SET reporter_id=:reporter_id, location=:location, "
                    "description=:description, status=:status, reported_at=:reported_at, "
                    "updated_at=:updated_at, effective_priority=:effective_priority, ai_json=:ai_json, "
                    "decision_json=:decision_json, final_json=:final_json "
                    "WHERE id=:id AND (:expected IS NULL OR status=:expected)",
                    values,
                )
                if cursor.rowcount == 0:
                    exists = connection.execute(
                        "SELECT status FROM incidents WHERE id = ?", (incident.id,)
                    ).fetchone()
                    if exists is None:
                        raise IncidentNotFoundError(f"Incident {incident.id} was not found.")
                    raise ConflictError(
                        f"Incident {incident.id} was already changed by someone else (now '{exists['status']}')."
                    )
        except sqlite3.Error as error:
            logger.error("Could not update incident: %s", error)
            raise StorageError(f"Could not save incident: {error}") from error
        return incident

    def delete(self, incident_id: str) -> None:
        try:
            with closing(self.__connect()) as connection, connection:
                cursor = connection.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
        except sqlite3.Error as error:
            logger.error("Could not delete incident: %s", error)
            raise StorageError(f"Could not delete incident: {error}") from error
        if cursor.rowcount == 0:
            raise IncidentNotFoundError(f"Incident {incident_id} was not found.")
