import os
import tempfile
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("safetriage.data")

INCIDENTS_FILENAME = "incidents.json"


def get_data_dir() -> str:
    return os.environ.get("DATA_DIR", "data")


def get_incidents_path(data_dir: str) -> str:
    return os.path.join(data_dir, INCIDENTS_FILENAME)

STATUS_PENDING = "pending_review"
STATUS_APPROVED = "approved"
STATUS_OVERRIDDEN = "overridden"
STATUS_REJECTED = "rejected"
STATUS_AUTO_REJECTED = "auto_rejected"
STATUSES = (STATUS_PENDING, STATUS_APPROVED, STATUS_OVERRIDDEN, STATUS_REJECTED, STATUS_AUTO_REJECTED)

def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def quarantine_corrupt_file(path: str, reason: str) -> str:
    """Move a corrupt data file aside so it is never overwritten. Returns a warning message."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = f"{path}.corrupt-{stamp}"
    logger.error("Corrupt data file %s (%s)", path, reason)
    try:
        os.replace(path, backup)
    except OSError as error:
        return f"Data file was unreadable ({reason}) and could not be backed up ({error}). Starting empty."
    return f"Data file was unreadable ({reason}). Backed up to {backup}; starting with an empty list."


def load_incidents(path: str) -> tuple[list[dict], str]:
    """Load all records. Returns (records, warning); warning is "" when everything is fine."""
    if not os.path.exists(path):
        return [], ""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return [], quarantine_corrupt_file(path, str(error))
    if not isinstance(data, list):
        return [], quarantine_corrupt_file(path, "top level is not a list")

    records = [item for item in data if isinstance(item, dict)]
    warning = ""
    if len(records) != len(data):
        warning = f"{len(data) - len(records)} malformed entries in the data file were ignored."
        logger.warning(warning)
    return records, warning

def save_incidents(path: str, incidents: list[dict]) -> tuple[bool, str]:
    """Atomically write all records. Returns (ok, error_message)."""
    directory = os.path.dirname(path) or "."
    temp_path = ""
    try:
        os.makedirs(directory, exist_ok=True)
        handle_fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
        with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
            json.dump(incidents, handle, indent=2, ensure_ascii=False)
        os.replace(temp_path, path)
    except (OSError, TypeError, ValueError) as error:
        logger.error("Could not save incidents: %s", error)
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        return False, f"Could not save incidents: {error}"
    return True, ""

def next_incident_id(incidents: list[dict]) -> str:
    highest = 0
    for record in incidents:
        text = str(record.get("id", ""))
        if text.startswith("INC-") and text[4:].isdecimal():
            highest = max(highest, int(text[4:]))
    return f"INC-{highest + 1:04d}"


def add_incident(path: str, record: dict) -> tuple[dict | None, str]:
    """Append a new record (id and timestamp added). Returns (saved_record, message)."""
    incidents, warning = load_incidents(path)
    new_record = dict(record)
    new_record["id"] = next_incident_id(incidents)
    new_record.setdefault("reported_at", current_timestamp())
    incidents.append(new_record)
    saved, error = save_incidents(path, incidents)
    if not saved:
        return None, error
    return new_record, warning
