"""ERRORS (shared) - errors/storage_error.py

Role: Exception types raised and handled across the managers.
Class in this file: StorageError
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from errors.safe_triage_error import SafeTriageError


class StorageError(SafeTriageError):
    """The incident store could not be read or written (disk, permissions, database)."""
