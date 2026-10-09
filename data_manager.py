import os
from datetime import datetime, timezone

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