"""SafeTriage entry point: coordinates the four managers.

    user    # terminal 1: employees report hazards
    admin   # terminal 2: safety staff review and dispatch

Flow: io_manager -> ai_manager -> logic_manager -> data_manager.
The managers never import each other; this file passes data between them.
"""
import logging
import os
import sys

import ai_manager
import data_manager
import io_manager
import logic_manager

# Gemini API key, linked automatically at startup.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def setup_logging(data_dir: str) -> None:
    """Send logs to a file (never the terminal, which io_manager owns)."""
    try:
        os.makedirs(data_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(data_dir, "safetriage.log"),
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    except OSError:
        logging.disable(logging.CRITICAL)

def build_record(report: dict, ai_result: dict, decision: dict) -> dict:
    """Combine report + AI result + logic decision into one storable record."""
    if decision["outcome"] == logic_manager.OUTCOME_REJECTED:
        status = data_manager.STATUS_AUTO_REJECTED
    else:
        status = data_manager.STATUS_PENDING
    return {
        "reporter_id": report["reporter_id"],
        "location": report["location"],
        "description": report["description"],
        "ai": ai_result,
        "decision": decision,
        "status": status,
    }

# ------------------------------------------------------------- user terminal
def run_user_mode(path: str) -> None:
    records, warning = data_manager.load_incidents(path)
    io_manager.show_user_welcome(len(records))
    if warning:
        io_manager.show_warning(warning)

    while True:
        report = io_manager.collect_report()
        io_manager.show_message("\nAnalysing your report with AI, please wait...")
        ai_result = ai_manager.analyse_report(report)
        decision = logic_manager.triage_incident(ai_result)
        saved, message = data_manager.add_incident(path, build_record(report, ai_result, decision))
        if saved is None:
            io_manager.show_error(f"{message} Your report was NOT saved. Please try again.")
        else:
            if message:
                io_manager.show_warning(message)
            io_manager.show_submission(saved)
        if not io_manager.confirm("\nReport another hazard?"):
            break
    io_manager.show_message("Thank you. Stay safe.")

# ------------------------------------------------------------ admin terminal
def review_flow(path: str, admin_id: str) -> None:
    records, warning = data_manager.load_incidents(path)
    if warning:
        io_manager.show_warning(warning)
    pending = logic_manager.sort_by_urgency(
        data_manager.filter_incidents(records, status=data_manager.STATUS_PENDING)
    )
    if not pending:
        io_manager.show_message("No incidents are awaiting review.")
        return
    urgent = [record for record in pending if logic_manager.is_urgent(record["decision"])]
    io_manager.show_pending_list(pending, len(urgent))
    incident_id = io_manager.prompt_incident_id([record["id"] for record in pending])
    if not incident_id:
        return
    record = next(item for item in pending if item["id"] == incident_id)
    io_manager.show_incident_detail(record)

    decision = record["decision"]
    can_approve = decision["priority"] in logic_manager.PRIORITY_LEVELS
    action = io_manager.prompt_review_action(can_approve)
    if action == "back":
        return

    if action == "approve":
        priority, teams, status = decision["priority"], decision["teams"], data_manager.STATUS_APPROVED
        note = io_manager.prompt_note(required=False)
    elif action == "override":
        priority = io_manager.prompt_choice("Final priority:", list(logic_manager.PRIORITY_LEVELS))
        teams = io_manager.prompt_multi_choice("Teams to contact:", list(logic_manager.ALL_TEAMS))
        status = data_manager.STATUS_OVERRIDDEN
        note = io_manager.prompt_note(required=True)
    else:
        priority, teams, status = "Rejected", [], data_manager.STATUS_REJECTED
        note = io_manager.prompt_note(required=True)

    final = logic_manager.build_final_decision(priority, teams, note, admin_id, data_manager.current_timestamp())
    updated, message = data_manager.update_incident(path, incident_id, {"status": status, "final": final})
    if updated is None:
        io_manager.show_error(message)
    else:
        io_manager.show_dispatch_notice(updated)

def history_flow(path: str) -> None:
    records, warning = data_manager.load_incidents(path)
    if warning:
        io_manager.show_warning(warning)
    filters = io_manager.prompt_filters(list(data_manager.STATUSES))
    results = logic_manager.sort_by_urgency(data_manager.filter_incidents(records, **filters))
    io_manager.show_incident_table(results, f"{len(results)} MATCHING INCIDENT(S)")
    if results:
        incident_id = io_manager.prompt_incident_id([record["id"] for record in results])
        if incident_id:
            io_manager.show_incident_detail(next(item for item in results if item["id"] == incident_id))

def run_admin_mode(path: str) -> None:
    admin_id = io_manager.prompt_admin_id()
    while True:
        choice = io_manager.admin_menu()
        if choice == "review":
            review_flow(path, admin_id)
        elif choice == "history":
            history_flow(path)
        elif choice == "quit":
            break
    io_manager.show_message("Admin session ended.")  

def main() -> int:
    if GEMINI_API_KEY:
        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    try:
        mode = sys.argv[1] if len(sys.argv) > 1 else io_manager.prompt_mode()
    except (KeyboardInterrupt, EOFError):
        return 0
    if mode not in ("user", "admin"):
        io_manager.show_usage()
        return 2

    data_dir = data_manager.get_data_dir()
    setup_logging(data_dir)
    path = data_manager.get_incidents_path(data_dir)
    try:
        if mode == "user":
            run_user_mode(path)
        else:
            run_admin_mode(path)
    except (KeyboardInterrupt, EOFError):
        io_manager.show_message("\nSession ended.")
    return 0

if __name__ == "__main__":
    exit_code = main()
    if exit_code:
        sys.exit(exit_code)