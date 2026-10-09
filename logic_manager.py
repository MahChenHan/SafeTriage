"""Logic layer for SafeTriage: the domain brain.

Pure functions that turn validated AI output into a priority, teams to contact,
and a recommended action. No printing, no file access, no API calls.
"""

PRIORITY_LEVELS = ("Low", "Medium", "High", "Critical")
LEVEL_HIGH = 2
LEVEL_CRITICAL = 3
MANY_PEOPLE_THRESHOLD = 5
LOW_CONFIDENCE_THRESHOLD = 0.6

OUTCOME_DISPATCH = "dispatch_recommended"
OUTCOME_MANUAL = "manual_triage"
OUTCOME_REJECTED = "rejected"

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

ACTIONS = {
    "Critical": "IMMEDIATE dispatch to {teams}. Alert safety staff now.",
    "High": "Dispatch {teams} as soon as possible (target: within 1 hour).",
    "Medium": "Assign {teams} to attend today.",
    "Low": "Log for {teams}; handle at the next routine visit.",
    "Unrated": "Manual triage required: automated AI analysis was unavailable.",
    "Rejected": "No dispatch: not recognised as a workplace hazard.",
}

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


def determine_action(priority: str, teams: list[str]) -> str:
    """Recommended action text for a priority and team list."""
    template = ACTIONS.get(priority, ACTIONS["Unrated"])
    return template.format(teams=", ".join(teams))


def needs_manual_review(analysis: dict) -> bool:
    """Flag low-confidence AI output for extra human attention."""
    return analysis["confidence"] < LOW_CONFIDENCE_THRESHOLD

def triage_incident(ai_result: dict) -> dict:
    """Turn an ai_manager result into a decision dict (outcome, priority, teams, action, reasons)."""
    if not ai_result.get("ok"):
        reason = f"AI analysis unavailable ({ai_result.get('error_type', 'unknown')}): {ai_result.get('error', '')}"
        return {
            "outcome": OUTCOME_MANUAL,
            "priority": "Unrated",
            "teams": ["Workplace Safety"],
            "action": determine_action("Unrated", []),
            "notify_staff": True,
            "needs_manual_review": True,
            "reasons": [reason],
        }

    analysis = ai_result["analysis"]
    if not analysis["is_hazard_report"]:
        return {
            "outcome": OUTCOME_REJECTED,
            "priority": "Rejected",
            "teams": [],
            "action": determine_action("Rejected", []),
            "notify_staff": False,
            "needs_manual_review": False,
            "reasons": ["AI judged this text is not a workplace hazard report"],
        }

    priority, reasons = determine_priority(analysis)
    teams = determine_teams(analysis, priority)
    manual = needs_manual_review(analysis)
    if manual:
        reasons.append(f"Low AI confidence ({analysis['confidence']:.2f}): human check advised")
    return {
        "outcome": OUTCOME_DISPATCH,
        "priority": priority,
        "teams": teams,
        "action": determine_action(priority, teams),
        "notify_staff": priority in ("High", "Critical") or manual,
        "needs_manual_review": manual,
        "reasons": reasons,
    }