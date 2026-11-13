"""ERRORS (shared) - errors/ai_timeout_error.py

Role: Exception types raised and handled across the managers.
Class in this file: AITimeoutError
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from errors.safe_triage_error import SafeTriageError


class AITimeoutError(SafeTriageError, TimeoutError):
    """The AI provider did not answer within the allowed time."""
