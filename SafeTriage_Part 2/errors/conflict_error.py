"""ERRORS (shared) - errors/conflict_error.py

Role: Exception types raised and handled across the managers.
Class in this file: ConflictError
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from errors.storage_error import StorageError


class ConflictError(StorageError):
    """The incident changed since it was read (for example, another admin already reviewed it)."""
