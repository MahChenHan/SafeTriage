"""IO MANAGER - io_manager/io_manager.py

Role: Collects and validates user input; displays records, lists, results and summaries. Terminal input/output lives only here.
Class in this file: IOManager
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from constants import LINE
from domain.incident import Incident
from io_manager.input_validator import InputValidator
from io_manager.screens import Screens
from logic_manager.summary_report import SummaryReport


class IOManager:
    """All terminal input and output for both the user and admin terminals.

    Composition: IOManager owns its Screens, which only build text. IOManager is the only object that prints.
    """

    def __init__(self, input_fn: Callable[[str], str] = input, output_fn: Callable[[str], None] = print) -> None:
        self._input = input_fn
        self._output = output_fn
        self._screens = Screens()

    # ---------------------------------------------------------------- basics
    def say(self, message: str = "") -> None:
        self._output(message)

    def say_lines(self, lines: Sequence[str]) -> None:
        for line in lines:
            self.say(line)

    def ask(self, prompt: str) -> str:
        return self._input(prompt).strip()

    def show_message(self, message: str) -> None:
        self.say(message)

    def show_error(self, message: str) -> None:
        self.say(f"[ERROR] {message}")

    def show_warning(self, message: str) -> None:
        self.say(f"[WARNING] {message}")

    def show_warnings(self, messages: Sequence[str]) -> None:
        for message in messages:
            if message:
                self.show_warning(message)

    def show_heading(self, title: str) -> None:
        self.say()
        self.say(LINE)
        self.say(title)
        self.say(LINE)

    def prompt_mode(self) -> str:
        """Ask which terminal this is when no command-line argument was given."""
        choice = self.prompt_choice(
            "Which terminal is this?", ["User (report hazards)", "Admin (review and dispatch incidents)"]
        )
        return "user" if choice.startswith("User") else "admin"

    def show_usage(self) -> None:
        self.say("Usage: python main.py user   (report hazards)")
        self.say("       python main.py admin  (review and dispatch incidents)")

    # --------------------------------------------------------------- prompts
    def prompt_field(self, label: str, validator: Callable[[str], str]) -> str:
        while True:
            text = self.ask(f"{label}: ")
            problem = validator(text)
            if not problem:
                return text
            self.show_error(problem)

    def prompt_choice(self, label: str, options: Sequence[str]) -> str:
        while True:
            self.say(label)
            for number, option in enumerate(options, start=1):
                self.say(f"  {number}. {option}")
            text = self.ask("Enter number: ")
            if text.isdecimal() and 1 <= int(text) <= len(options):
                return options[int(text) - 1]
            self.show_error(f"Please enter a number from 1 to {len(options)}.")

    def prompt_multi_choice(self, label: str, options: Sequence[str]) -> list[str]:
        while True:
            self.say(label)
            for number, option in enumerate(options, start=1):
                self.say(f"  {number}. {option}")
            numbers = InputValidator.parse_number_list(
                self.ask("Enter one or more numbers, separated by commas: "), len(options)
            )
            if numbers is not None:
                return [options[number - 1] for number in numbers]
            self.show_error(f"Please enter numbers from 1 to {len(options)}, e.g. 1,3")

    def confirm(self, question: str) -> bool:
        while True:
            text = self.ask(f"{question} (y/n): ").lower()
            if text in ("y", "yes"):
                return True
            if text in ("n", "no"):
                return False
            self.show_error("Please answer y or n.")

    # --------------------------------------------------------- user terminal
    def collect_report(self) -> tuple[str, str, str]:
        """Returns (reporter_id, location, description), each already validated."""
        self.show_heading("NEW HAZARD REPORT")
        reporter_id = self.prompt_field("Your name", InputValidator.validate_name)
        location = self.prompt_field("Location (e.g. Discussion Room 01-02)", InputValidator.validate_location)
        description = self.prompt_field("Describe the hazard in your own words", InputValidator.validate_description)
        return reporter_id, location, description

    def show_user_welcome(self, record_count: int) -> None:
        self.show_heading("SAFETRIAGE - HAZARD REPORTING")
        self.say("Describe what you see and safety staff will be alerted.")
        self.say(f"({record_count} incident(s) currently on file)")

    def show_submission(self, record: Incident) -> None:
        self.say()
        self.say_lines(self._screens.submission(record))

    # -------------------------------------------------------- admin terminal
    def show_incident_detail(self, record: Incident) -> None:
        self.say()
        self.say(LINE)
        self.say(self._screens.incident_detail(record))
        self.say(LINE)

    def show_incident_table(self, incidents: Sequence[Incident], title: str) -> None:
        self.say()
        self.say_lines(self._screens.incident_table(incidents, title))

    def show_pending_list(self, pending: Sequence[Incident], urgent_count: int) -> None:
        """Shown only when the admin chooses to review: an alert line plus the pending table."""
        if urgent_count:
            self.say()
            self.say(f"!!! ALERT: {urgent_count} urgent incident(s) need attention !!!")
        self.show_incident_table(pending, "PENDING REVIEW (most urgent first)")

    def show_admin_welcome(self, record_count: int, pending_count: int) -> None:
        self.show_heading("SAFETRIAGE - ADMIN CONSOLE")
        self.say(f"{record_count} incident(s) on file, {pending_count} awaiting review.")

    def admin_menu(self) -> str:
        options = {
            "Review a pending incident": "review",
            "History": "history",
            "Summary report": "summary",
            "Delete a rejected incident": "purge",
            "Quit": "quit",
        }
        choice = self.prompt_choice("\nWhat would you like to do?", list(options))
        return options[choice]

    def prompt_admin_id(self) -> str:
        return self.prompt_field("Admin ID", InputValidator.validate_id)

    def prompt_incident_id(self, valid_ids: Sequence[str]) -> str:
        """Ask for an incident id (or just its number). Blank returns ''."""
        while True:
            text = self.ask("Incident ID (e.g. INC-0003 or 3; blank to go back): ").upper()
            if not text:
                return ""
            if text in valid_ids:
                return text
            if text.isdecimal():
                matches = [item for item in valid_ids if item.endswith("-" + text.zfill(4))]
                if matches:
                    return matches[0]
            self.show_error("That ID is not in the list shown.")

    def prompt_review_action(self, can_approve: bool) -> str:
        options = {}
        if can_approve:
            options["Approve recommendation and dispatch"] = "approve"
        options["Override priority / teams"] = "override"
        options["Reject report (no dispatch)"] = "reject"
        options["Back"] = "back"
        if not can_approve:
            self.say("This incident has no AI-based rating, so it cannot be approved as-is.")
        return options[self.prompt_choice("Your decision:", list(options))]

    def prompt_note(self, required: bool) -> str:
        if required:
            return self.prompt_field("Note explaining your decision", InputValidator.validate_note)
        text = self.ask("Optional note (blank to skip): ")
        while len(text) > InputValidator.MAX_NOTE_LENGTH:
            self.show_error(f"Note must be at most {InputValidator.MAX_NOTE_LENGTH} characters.")
            text = self.ask("Optional note (blank to skip): ")
        return text

    def prompt_filters(self, statuses: Sequence[str], priorities: Sequence[str]) -> dict[str, str]:
        """Ask for the History filters. 'any' means do not filter on that field."""
        status = self.prompt_choice("Filter by status:", ["any", *statuses])
        priority = self.prompt_choice("Filter by priority:", ["any", *priorities])
        return {
            "status": "" if status == "any" else status,
            "priority": "" if priority == "any" else priority,
        }

    def show_dispatch_notice(self, record: Incident) -> None:
        self.say()
        self.say_lines(self._screens.dispatch_notice(record))

    # ----------------------------------------------- summary report (new feature)
    def show_summary(self, report: SummaryReport) -> None:
        self.say()
        self.say(self._screens.summary(report))
