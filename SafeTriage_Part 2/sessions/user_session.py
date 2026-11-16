"""SESSIONS (application layer) - sessions/user_session.py

Role: The user and admin workflows. They call the four managers; they hold no business rules of
their own.
Class in this file: UserSession
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from constants import OUTCOME_REJECTED, STATUS_AUTO_REJECTED, STATUS_PENDING
from domain.hazard_report import HazardReport
from domain.incident import Incident
from errors.storage_error import StorageError
from sessions.session import Session


class UserSession(Session):
    """Employee terminal: collect a report, analyse it, triage it, save it."""

    def run(self) -> None:
        loaded = self._load()
        self._io.show_user_welcome(len(loaded.incidents))
        while True:
            self._handle_one_report()
            if not self._io.confirm("\nReport another hazard?"):
                break
        self._io.show_message("Thank you. Stay safe.")

    def _handle_one_report(self) -> None:
        reporter_id, location, description = self._io.collect_report()
        report = HazardReport(reporter_id, location, description)
        reported_at = self._data.current_timestamp()

        self._io.show_message("\nAnalysing your report with AI, please wait...")
        ai_result = self._ai.analyse_report(report)
        decision = self._logic.triage(ai_result)

        open_incidents = self._load(status=STATUS_PENDING).incidents
        duplicate_id, reason = self._logic.find_duplicate(
            report.location, ai_result.analysis, reported_at, open_incidents
        )
        decision = self._logic.flag_duplicate(decision, duplicate_id, reason)

        status = STATUS_AUTO_REJECTED if decision.outcome == OUTCOME_REJECTED else STATUS_PENDING
        incident = Incident(
            reporter_id=report.reporter_id, location=report.location, description=report.description,
            ai=ai_result, decision=decision, status=status, reported_at=reported_at,
        )
        try:
            saved = self._data.add_incident(incident)
        except StorageError as error:
            self._io.show_error(f"{error} Your report was NOT saved. Please try again.")
            return
        self._io.show_submission(saved)
