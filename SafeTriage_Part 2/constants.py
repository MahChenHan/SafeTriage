"""SHARED CONSTANTS - constants.py

Role: Named values (statuses, priorities, teams, thresholds) used by the managers. No classes.
Keeping them here means no manager hides a "magic number" or repeats a label.
See README section "Where each manager lives" for the full map.
"""

# ------------------------------------------------------------------ hazards
HAZARD_TYPES = ("electrical", "fire", "structural", "water", "chemical", "slip_trip", "other")
HAZARD_PRECEDENCE = ("fire", "electrical", "chemical", "structural", "water", "slip_trip", "other")

# ------------------------------------------------------------ AI analysis
# Range of the AI severity score, and the scores that map to each starting priority.
MIN_SEVERITY = 1
MAX_SEVERITY = 5            # imminent danger to life -> Critical
SEVERITY_SERIOUS = 4        # -> High
SEVERITY_MODERATE = 3       # -> Medium
MAX_SUMMARY_LENGTH = 300
LOW_CONFIDENCE_THRESHOLD = 0.6

# ----------------------------------------------------------------- statuses
STATUS_PENDING = "pending_review"
STATUS_APPROVED = "approved"
STATUS_OVERRIDDEN = "overridden"
STATUS_REJECTED = "rejected"
STATUS_AUTO_REJECTED = "auto_rejected"
STATUSES = (STATUS_PENDING, STATUS_APPROVED, STATUS_OVERRIDDEN, STATUS_REJECTED, STATUS_AUTO_REJECTED)
PURGEABLE_STATUSES = (STATUS_REJECTED, STATUS_AUTO_REJECTED)

# --------------------------------------------------------------- priorities
PRIORITY_LOW = "Low"
PRIORITY_MEDIUM = "Medium"
PRIORITY_HIGH = "High"
PRIORITY_CRITICAL = "Critical"
PRIORITY_UNRATED = "Unrated"      # the AI was unavailable, so a person must rate it
PRIORITY_REJECTED = "Rejected"    # not a workplace hazard

# The rule engine works with levels: a level is an index into PRIORITY_LEVELS.
PRIORITY_LEVELS = (PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_CRITICAL)
LEVEL_LOW = 0
LEVEL_MEDIUM = 1
LEVEL_HIGH = 2
LEVEL_CRITICAL = 3

ALL_PRIORITIES = (
    PRIORITY_CRITICAL, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW, PRIORITY_UNRATED, PRIORITY_REJECTED,
)
URGENT_PRIORITIES = (PRIORITY_CRITICAL, PRIORITY_HIGH, PRIORITY_UNRATED)   # an admin should look now
NOTIFY_PRIORITIES = (PRIORITY_HIGH, PRIORITY_CRITICAL)                     # safety staff are alerted
URGENCY_RANK = {
    PRIORITY_CRITICAL: 4, PRIORITY_HIGH: 3, PRIORITY_UNRATED: 3,
    PRIORITY_MEDIUM: 2, PRIORITY_LOW: 1, PRIORITY_REJECTED: 0,
}

# ------------------------------------------------------- business thresholds
MULTI_HAZARD_MINIMUM = 2            # this many distinct hazards escalates one level
MANY_PEOPLE_THRESHOLD = 5           # structural hazard with this many people exposed -> High
ELECTRICAL_WATER_MIN_SEVERITY = 3   # electrical + water at this severity -> Critical
DUPLICATE_WINDOW_HOURS = 4
HOTSPOT_COUNT = 3                   # locations listed in the summary report

# -------------------------------------------------------- triage outcomes
OUTCOME_DISPATCH = "dispatch_recommended"
OUTCOME_MANUAL = "manual_triage"
OUTCOME_REJECTED = "rejected"

# -------------------------------------------------------------------- teams
TEAM_EMERGENCY = "Emergency Response"
TEAM_DEFAULT = "Workplace Safety"
ALL_TEAMS = (
    "Maintenance", "Electrical", "Fire Safety", TEAM_DEFAULT, "Security", TEAM_EMERGENCY,
)
TEAM_BY_HAZARD = {
    "fire": "Fire Safety",
    "electrical": "Electrical",
    "chemical": TEAM_DEFAULT,
    "structural": "Maintenance",
    "water": "Maintenance",
    "slip_trip": "Maintenance",
    "other": TEAM_DEFAULT,
}
ACTIONS = {
    PRIORITY_CRITICAL: "IMMEDIATE dispatch to {teams}. Alert safety staff now.",
    PRIORITY_HIGH: "Dispatch {teams} as soon as possible (target: within 1 hour).",
    PRIORITY_MEDIUM: "Assign {teams} to attend today.",
    PRIORITY_LOW: "Log for {teams}; handle at the next routine visit.",
    PRIORITY_UNRATED: "Manual triage required: automated AI analysis was unavailable.",
    PRIORITY_REJECTED: "No dispatch: not recognised as a workplace hazard.",
}

# --------------------------------------------------------------- AI calls
DEFAULT_MODEL = "gemini-3.8-flash"
MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 30.0
# Extra seconds AIManager allows on top of a fallback chain, so the chain can finish switching providers.
TIMEOUT_MARGIN_SECONDS = 5.0
ERROR_API_FAILURE = "api_failure"
ERROR_MALFORMED = "malformed_response"

# Backup AI provider (Groq, free tier). Used only if the primary (Gemini) fails.
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

# ------------------------------------------------------------------ storage
INCIDENTS_FILENAME = "incidents.json"
DATABASE_FILENAME = "incidents.db"
BACKEND_JSON = "json"
BACKEND_SQLITE = "sqlite"
INCIDENT_ID_PREFIX = "INC-"

# ------------------------------------------------------------------ display
LINE = "=" * 70
THIN = "-" * 70
