"""Logic layer for SafeTriage: the domain brain.

Pure functions that turn validated AI output into a priority, teams to contact,
and a recommended action. No printing, no file access, no API calls.
"""

PRIORITY_LEVELS = ("Low", "Medium", "High", "Critical")
LEVEL_HIGH = 2
LEVEL_CRITICAL = 3


def severity_to_level(severity: int) -> int:
    """Map AI severity (1-5) to a base priority index."""
    if severity >= 5:
        return 3
    if severity == 4:
        return 2
    if severity == 3:
        return 1
    return 0


def escalate(level: int, steps: int = 1) -> int:
    """Raise a priority index, capped at Critical."""
    return min(level + steps, len(PRIORITY_LEVELS) - 1)