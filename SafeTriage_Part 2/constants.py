"""SHARED CONSTANTS - constants.py

Role: Named values (statuses, priorities, teams, thresholds) used by the managers. No classes.
See README section "Where each manager lives" for the full map.
"""

HAZARD_TYPES = ("electrical", "fire", "structural", "water", "chemical", "slip_trip", "other")

STATUS_PENDING = "pending_review"

STATUS_APPROVED = "approved"

STATUS_OVERRIDDEN = "overridden"

STATUS_REJECTED = "rejected"

STATUS_AUTO_REJECTED = "auto_rejected"

STATUSES = (STATUS_PENDING, STATUS_APPROVED, STATUS_OVERRIDDEN, STATUS_REJECTED, STATUS_AUTO_REJECTED)

DEFAULT_MODEL = "gemini-3.8-flash"

MAX_ATTEMPTS = 3

RETRY_DELAY_SECONDS = 1.0

REQUEST_TIMEOUT_SECONDS = 30.0

# Extra seconds AIManager allows on top of a fallback chain, so the chain can finish switching providers.
TIMEOUT_MARGIN_SECONDS = 5.0

ERROR_API_FAILURE = "api_failure"

ERROR_MALFORMED = "malformed_response"

INCIDENTS_FILENAME = "incidents.json"

DATABASE_FILENAME = "incidents.db"

BACKEND_JSON = "json"

BACKEND_SQLITE = "sqlite"

LINE = "=" * 70

THIN = "-" * 70

PRIORITY_LEVELS = ("Low", "Medium", "High", "Critical")

LEVEL_HIGH = 2

LEVEL_CRITICAL = 3

MANY_PEOPLE_THRESHOLD = 5

LOW_CONFIDENCE_THRESHOLD = 0.6

DUPLICATE_WINDOW_HOURS = 4

OUTCOME_DISPATCH = "dispatch_recommended"

OUTCOME_MANUAL = "manual_triage"

OUTCOME_REJECTED = "rejected"

ALL_TEAMS = (
    "Maintenance", "Electrical", "Fire Safety", "Workplace Safety", "Security", "Emergency Response",
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

ALL_PRIORITIES = ("Critical", "High", "Medium", "Low", "Unrated", "Rejected")

URGENCY_RANK = {"Critical": 4, "High": 3, "Unrated": 3, "Medium": 2, "Low": 1, "Rejected": 0}

PURGEABLE_STATUSES = (STATUS_REJECTED, STATUS_AUTO_REJECTED)

# Backup AI provider (Groq, free tier). Used only if the primary (Gemini) fails.
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"