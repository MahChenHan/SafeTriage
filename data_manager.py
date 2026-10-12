"""Data layer for SafeTriage: JSON persistence shared by the user and admin terminals.

Every write re-reads the file first, so two terminals working at once do not
overwrite each other's records. Writes are atomic (temp file + rename), and a
missing or corrupt file never crashes the program.
"""
from contextlib import contextmanager
import json
import logging
import os
import tempfile
from datetime import datetime, timezone

logger = logging.getLogger("safetriage.data")

INCIDENTS_FILENAME = "incidents.json"

STATUS_PENDING = "pending_review"
STATUS_APPROVED = "approved"
STATUS_OVERRIDDEN = "overridden"
STATUS_REJECTED = "rejected"
STATUS_AUTO_REJECTED = "auto_rejected"
STATUSES = (STATUS_PENDING, STATUS_APPROVED, STATUS_OVERRIDDEN, STATUS_REJECTED, STATUS_AUTO_REJECTED)

# Fields a stored AI analysis must have for the record to be displayed safely
ANALYSIS_KEYS = ("hazard_types", "severity", "injury_present", "people_exposed", "confidence", "summary")


def get_data_dir() -> str:
    return os.environ.get("DATA_DIR", "data")


def get_incidents_path(data_dir: str) -> str:
    return os.path.join(data_dir, INCIDENTS_FILENAME)


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


def is_valid_decision(decision: object) -> bool:
    """Check priority, team names and optional explanation reasons."""
    if not isinstance(decision, dict) or not isinstance(decision.get("priority"), str):
        return False

    teams = decision.get("teams")
    if not isinstance(teams, list) or not all(isinstance(team, str) for team in teams):
        return False

    reasons = decision.get("reasons", [])
    return isinstance(reasons, list) and all(isinstance(reason, str) for reason in reasons)


def is_valid_analysis(analysis: object) -> bool:
    """A stored AI analysis is either None (AI was unavailable) or has every field the display uses."""
    if analysis is None:
        return True
    if not isinstance(analysis, dict) or any(key not in analysis for key in ANALYSIS_KEYS):
        return False
    hazards = analysis["hazard_types"]
    confidence = analysis["confidence"]
    return (
        isinstance(hazards, list)
        and all(isinstance(hazard, str) for hazard in hazards)
        and isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
    )


def is_usable_record(record: dict) -> bool:
    """True when a record has everything the review and history screens rely on."""
    if not isinstance(record.get("id"), str) or not isinstance(record.get("status"), str):
        return False
    if not isinstance(record.get("reported_at", ""), str):
        return False
    if not is_valid_decision(record.get("decision")):
        return False
    final = record.get("final")
    if final is not None and not is_valid_decision(final):
        return False
    ai = record.get("ai")
    if ai is None:
        return True
    return isinstance(ai, dict) and is_valid_analysis(ai.get("analysis"))


def split_usable_incidents(incidents: list[dict]) -> tuple[list[dict], str]:
    """Keep only records that are safe to display. Returns (usable, warning).

    Damaged records are only hidden from the screens, never deleted: they stay
    in the file untouched so nothing is lost and they can be repaired by hand.
    """
    usable = [record for record in incidents if is_usable_record(record)]
    skipped = len(incidents) - len(usable)
    warning = ""
    if skipped:
        warning = f"{skipped} damaged incident(s) were skipped. They are left unchanged in the data file."
        logger.warning(warning)
    return usable, warning


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


def _add_incident_unlocked(path: str, record: dict) -> tuple[dict | None, str]:
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


def _update_incident_unlocked(path: str, incident_id: str, changes: dict) -> tuple[dict | None, str]:
    """Merge changes into one record. Returns (updated_record, message)."""
    incidents, warning = load_incidents(path)
    for record in incidents:
        if record.get("id") == incident_id:
            record.update(changes)
            record["updated_at"] = current_timestamp()
            saved, error = save_incidents(path, incidents)
            if not saved:
                return None, error
            return record, warning
    return None, f"Incident {incident_id} was not found."


def filter_incidents(incidents: list[dict], status: str = "", priority: str = "") -> list[dict]:
    """Filter records by status and/or priority. An empty argument means 'do not filter on this'.

    Priority is matched against the admin's final decision when there is one,
    otherwise against the rule engine's recommendation.
    """
    results = []
    for record in incidents:
        shown = record.get("final") or record.get("decision") or {}
        if status and record.get("status") != status:
            continue
        if priority and shown.get("priority") != priority:
            continue
        results.append(record)
    return results


@contextmanager
def incident_file_lock(path: str):
    """Lock storage during an incident read/update/save operation."""
    lock_path = path + ".lock"
    os.makedirs(os.path.dirname(lock_path) or ".", exist_ok=True)

    with open(lock_path, "a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def add_incident(path: str, record: dict) -> tuple[dict | None, str]:
    """Append a report while holding the shared storage lock."""
    try:
        with incident_file_lock(path):
            return _add_incident_unlocked(path, record)
    except OSError as error:
        logger.error("Could not access incidents for adding: %s", error)
        return None, f"Could not access incident storage: {error}"


def update_incident(path: str, incident_id: str, changes: dict) -> tuple[dict | None, str]:
    """Update a report while holding the shared storage lock."""
    try:
        with incident_file_lock(path):
            return _update_incident_unlocked(path, incident_id, changes)
    except OSError as error:
        logger.error("Could not access incidents for updating: %s", error)
        return None, f"Could not access incident storage: {error}"