"""DOMAIN MODELS (shared) - domain/check_result.py

Role: Immutable records passed between the four managers. No I/O and no business rules.
Class in this file: CheckResult
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations


class CheckResult:
    """Tiny type checks shared by the ``from_dict`` methods (internal to this module)."""

    @staticmethod
    def is_int(value: object) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    @staticmethod
    def is_number(value: object) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @staticmethod
    def require_str_list(value: object, label: str) -> tuple[str, ...]:
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"{label} must be a list of text values")
        return tuple(value)
