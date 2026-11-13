"""ERRORS (shared) - errors/safe_triage_error.py

Role: Exception types raised and handled across the managers.
Class in this file: SafeTriageError
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations


class SafeTriageError(Exception):
    """Base class for every error raised on purpose by SafeTriage."""
