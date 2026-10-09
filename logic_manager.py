"""Logic layer for SafeTriage: the domain brain.

Pure functions that turn validated AI output into a priority, teams to contact,
and a recommended action. No printing, no file access, no API calls.
"""

PRIORITY_LEVELS = ("Low", "Medium", "High", "Critical")
LEVEL_HIGH = 2
LEVEL_CRITICAL = 3
MANY_PEOPLE_THRESHOLD = 5

ALL_TEAMS = (
    "Maintenance",
    "Electrical",
    "Fire Safety",
    "Workplace Safety",
    "Security",
    "Emergency Response",
)

TEAM_BY_HAZARD = {
    "fire": "Fire Safety",
    "electrical": "Electrical",
    "chemical": "Workplace Safety",
    "structural": "Maintenance",
    "water": "Maintenance",
    "slip_trip": "Maintenance",
    "other": "Workplace Safety",
}
HAZARD_PRECEDENCE = ("fire", "electrical", "chemical", "structural", "water", "slip_trip", "other")



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

def determine_priority(analysis: dict) -> tuple[str, list[str]]:
    """Apply the business rules. Returns (priority, reasons explaining each rule that fired)."""
    hazards = set(analysis["hazard_types"])
    severity = analysis["severity"]
    injured = analysis["injury_present"]

    level = severity_to_level(severity)
    reasons = [f"Base level {PRIORITY_LEVELS[level]} from AI severity {severity}/5"]

    if len(hazards) >= 2:
        level = escalate(level)
        reasons.append(f"Escalated one level: {len(hazards)} hazards present ({', '.join(sorted(hazards))})")
    if injured and level < LEVEL_HIGH:
        level = LEVEL_HIGH
        reasons.append("Raised to High: injury reported")
    if "structural" in hazards and analysis["people_exposed"] >= MANY_PEOPLE_THRESHOLD and level < LEVEL_HIGH:
        level = LEVEL_HIGH
        reasons.append(f"Raised to High: structural hazard with {analysis['people_exposed']} people exposed")
    if {"electrical", "water"} <= hazards and severity >= 3 and level < LEVEL_CRITICAL:
        level = LEVEL_CRITICAL
        reasons.append("Raised to Critical: electrical + water hazard at severity 3 or above")
    if "fire" in hazards and injured and level < LEVEL_CRITICAL:
        level = LEVEL_CRITICAL
        reasons.append("Raised to Critical: fire hazard with injury")

    return PRIORITY_LEVELS[level], reasons

def determine_teams(analysis: dict, priority: str) -> list[str]:
    """Ordered, de-duplicated list of teams to contact."""
    teams: list[str] = []
    if analysis["injury_present"] and priority == "Critical":
        teams.append("Emergency Response")
    for hazard in HAZARD_PRECEDENCE:
        if hazard in analysis["hazard_types"]:
            team = TEAM_BY_HAZARD[hazard]
            if team not in teams:
                teams.append(team)
    if not teams:
        teams.append("Workplace Safety")
    return teams