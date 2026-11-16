"""SESSIONS (application layer) - sessions/admin_session.py

Role: The user and admin workflows. They call the four managers; they hold no business rules of
their own.
Class in this file: AdminSession
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from constants import (
    ALL_PRIORITIES, ALL_TEAMS, PRIORITY_LEVELS, PRIORITY_REJECTED, STATUS_APPROVED, STATUS_OVERRIDDEN,
    STATUS_PENDING, STATUS_REJECTED, STATUSES,
)
from errors.storage_error import StorageError
from sessions.session import Session


class AdminSession(Session):
    """Safety-staff terminal: review, history, summary report, delete rejected incidents."""

    def run(self) -> None:
        loaded = self._load(show_warnings=False)
        pending = [item for item in loaded.incidents if item.status == STATUS_PENDING]
        self._io.show_admin_welcome(len(loaded.incidents), len(pending))
        self._io.show_warnings(loaded.warnings)
        admin_id = self._io.prompt_admin_id()

        actions = {
            "review": lambda: self._review(admin_id),
            "history": self._history,
            "summary": self._summary,
            "purge": self._purge,
        }
        while True:
            choice = self._io.admin_menu()
            if choice == "quit":
                break
            actions[choice]()
        self._io.show_message("Admin session ended.")

    # ---------------------------------------------------------------- review
    def _review(self, admin_id: str) -> None:
        pending = self._logic.sort_by_urgency(self._load(status=STATUS_PENDING).incidents)
        if not pending:
            self._io.show_message("No incidents are awaiting review.")
            return
        urgent = [item for item in pending if self._logic.is_urgent(item.decision)]
        self._io.show_pending_list(pending, len(urgent))
        incident_id = self._io.prompt_incident_id([item.id for item in pending])
        if not incident_id:
            return
        record = next(item for item in pending if item.id == incident_id)
        self._io.show_incident_detail(record)

        can_approve = record.decision.priority in PRIORITY_LEVELS
        action = self._io.prompt_review_action(can_approve)
        if action == "back":
            return
        if action == "approve":
            priority, teams, status = record.decision.priority, record.decision.teams, STATUS_APPROVED
            note = self._io.prompt_note(required=False)
        elif action == "override":
            priority = self._io.prompt_choice("Final priority:", list(PRIORITY_LEVELS))
            teams = self._io.prompt_multi_choice("Teams to contact:", list(ALL_TEAMS))
            status = STATUS_OVERRIDDEN
            note = self._io.prompt_note(required=True)
        else:
            priority, teams, status = PRIORITY_REJECTED, (), STATUS_REJECTED
            note = self._io.prompt_note(required=True)

        final = self._logic.build_final_decision(priority, teams, note, admin_id, self._data.current_timestamp())
        try:
            updated = self._data.record_review(record, status, final)
        except StorageError as error:  # includes "someone else already reviewed it"
            self._io.show_error(str(error))
            return
        self._io.show_dispatch_notice(updated)

    # --------------------------------------------------------------- history
    def _history(self) -> None:
        filters = self._io.prompt_filters(list(STATUSES), list(ALL_PRIORITIES))
        results = self._logic.sort_by_urgency(self._load(**filters).incidents)
        self._io.show_incident_table(results, f"{len(results)} MATCHING INCIDENT(S)")
        if results:
            incident_id = self._io.prompt_incident_id([item.id for item in results])
            if incident_id:
                self._io.show_incident_detail(next(item for item in results if item.id == incident_id))

    # --------------------------------------------------------------- summary
    def _summary(self) -> None:
        incidents = self._load().incidents
        self._io.show_summary(self._logic.summarise(incidents))

    # ----------------------------------------------------------------- purge
    def _purge(self) -> None:
        candidates = [item for item in self._load().incidents if self._logic.can_purge(item)]
        if not candidates:
            self._io.show_message("There are no rejected incidents to delete.")
            return
        self._io.show_incident_table(candidates, "REJECTED INCIDENTS (can be deleted)")
        incident_id = self._io.prompt_incident_id([item.id for item in candidates])
        if not incident_id:
            return
        if not self._io.confirm(f"Permanently delete {incident_id}? This cannot be undone."):
            self._io.show_message("Nothing was deleted.")
            return
        try:
            self._data.delete_incident(incident_id)
        except StorageError as error:
            self._io.show_error(str(error))
            return
        self._io.show_message(f"{incident_id} was deleted.")
