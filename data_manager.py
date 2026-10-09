import os
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