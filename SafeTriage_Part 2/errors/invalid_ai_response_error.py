"""ERRORS (shared) - errors/invalid_ai_response_error.py

Role: Exception types raised and handled across the managers.
Class in this file: InvalidAIResponseError
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from errors.safe_triage_error import SafeTriageError


class InvalidAIResponseError(SafeTriageError, ValueError):
    """The AI reply was not valid JSON or did not match the required schema."""
