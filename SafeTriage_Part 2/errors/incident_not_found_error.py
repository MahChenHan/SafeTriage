"""ERRORS (shared) - errors/incident_not_found_error.py

Role: Exception types raised and handled across the managers.
Class in this file: IncidentNotFoundError
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from errors.storage_error import StorageError


class IncidentNotFoundError(StorageError):
    """No incident exists with the requested id."""
