"""Logic manager test script: verifies logic_manager independently of the live AI API.

Every test feeds logic_manager HARDCODED sample AI responses (shaped exactly like
ai_manager.analyse_report() output), so no API key, network or extra package is needed.

Run it:
    python test_logic_manager.py           (plain Python, prints a summary)
    python -m pytest test_logic_manager.py (also works if pytest is installed)

Exit code is 0 when every test passes, 1 otherwise. Functions only: no classes.
"""
import sys
import traceback

import logic_manager


# ======================================================================
# Hardcoded sample AI responses
# ======================================================================
def make_analysis(**changes) -> dict:
    """A valid AI analysis. Defaults describe a minor slip hazard; override any field."""
    analysis = {
        "is_hazard_report": True,
        "hazard_types": ["slip_trip"],
        "severity": 2,
        "injury_present": False,
        "people_exposed": 1,
        "confidence": 0.9,
        "summary": "Wet floor near the pantry.",
    }
    analysis.update(changes)
    return analysis


def make_result(**changes) -> dict:
    """A successful ai_manager result wrapping make_analysis(**changes)."""
    return {"ok": True, "analysis": make_analysis(**changes), "model": "sample",
            "attempts": 1, "error_type": "", "error": ""}


# Proposal example: electrical + water, severity 5, 6 people, confidence 0.96
SAMPLE_ELECTRICAL_WATER = make_result(
    hazard_types=["electrical", "water"], severity=5, people_exposed=6, confidence=0.96,
    summary="Water leaking onto a live power socket.",
)
# Small fire with one person burned
SAMPLE_FIRE_INJURY = make_result(
    hazard_types=["fire"], severity=2, injury_present=True, people_exposed=2,
    summary="Small bin fire, one person burned their hand.",
)
# Cracked ceiling above a full lecture theatre
SAMPLE_STRUCTURAL_CROWD = make_result(
    hazard_types=["structural"], severity=2, people_exposed=40,
    summary="Crack in ceiling above lecture theatre seating.",
)
# Not a hazard at all
SAMPLE_NOT_A_HAZARD = make_result(
    is_hazard_report=False, hazard_types=[], severity=1, people_exposed=0,
    summary="User is asking about the cafeteria menu.",
)
# The AI layer gave up after its retries (e.g. network down, bad key)
SAMPLE_API_FAILURE = {"ok": False, "analysis": None, "model": "sample", "attempts": 3,
                      "error_type": "api_failure", "error": "ConnectionError: network unreachable"}
# The AI kept returning text that failed schema validation
SAMPLE_MALFORMED = {"ok": False, "analysis": None, "model": "sample", "attempts": 3,
                    "error_type": "malformed_response", "error": "missing keys: severity"}


# ======================================================================
# Severity mapping and escalation
# ======================================================================
def test_severity_to_level_maps_each_severity():
    expected = {1: 0, 2: 0, 3: 1, 4: 2, 5: 3}
    for severity, level in expected.items():
        assert logic_manager.severity_to_level(severity) == level, severity


def test_escalate_is_capped_at_critical():
    assert logic_manager.escalate(1) == 2
    assert logic_manager.escalate(3) == 3
    assert logic_manager.escalate(2, steps=5) == 3


# ======================================================================
# Business rules (determine_priority), including multi-condition rules
# ======================================================================
def test_low_severity_single_hazard_is_low():
    priority, reasons = logic_manager.determine_priority(make_analysis(severity=1))
    assert priority == "Low"
    assert len(reasons) == 1  # only the base-level reason


def test_each_severity_gives_expected_base_priority():
    expected = {1: "Low", 2: "Low", 3: "Medium", 4: "High", 5: "Critical"}
    for severity, priority in expected.items():
        assert logic_manager.determine_priority(make_analysis(severity=severity))[0] == priority


def test_two_hazards_escalate_one_level():
    priority, reasons = logic_manager.determine_priority(
        make_analysis(hazard_types=["slip_trip", "chemical"], severity=3))
    assert priority == "High"
    assert any("Escalated one level" in reason for reason in reasons)


def test_escalation_never_goes_above_critical():
    priority, _ = logic_manager.determine_priority(make_analysis(hazard_types=["fire", "chemical"], severity=5))
    assert priority == "Critical"


def test_injury_alone_raises_to_high():
    priority, reasons = logic_manager.determine_priority(make_analysis(severity=1, injury_present=True))
    assert priority == "High"
    assert "Raised to High: injury reported" in reasons


def test_rule_electrical_plus_water_at_severity_3_is_critical():
    priority, reasons = logic_manager.determine_priority(
        make_analysis(hazard_types=["electrical", "water"], severity=3))
    assert priority == "Critical"
    assert any("electrical + water" in reason for reason in reasons)


def test_rule_electrical_plus_water_below_severity_3_is_not_critical():
    priority, _ = logic_manager.determine_priority(make_analysis(hazard_types=["electrical", "water"], severity=2))
    assert priority == "Medium"  # Low base, +1 for two hazards; critical rule needs severity >= 3


def test_rule_electrical_alone_is_not_critical():
    priority, _ = logic_manager.determine_priority(make_analysis(hazard_types=["electrical"], severity=3))
    assert priority == "Medium"


def test_rule_fire_with_injury_is_critical():
    priority, reasons = logic_manager.determine_priority(SAMPLE_FIRE_INJURY["analysis"])
    assert priority == "Critical"
    assert any("fire hazard with injury" in reason for reason in reasons)


def test_rule_fire_without_injury_follows_severity():
    priority, _ = logic_manager.determine_priority(make_analysis(hazard_types=["fire"], severity=2))
    assert priority == "Low"


def test_rule_structural_with_many_people_is_high():
    priority, reasons = logic_manager.determine_priority(SAMPLE_STRUCTURAL_CROWD["analysis"])
    assert priority == "High"
    assert any("structural hazard" in reason for reason in reasons)


def test_rule_structural_threshold_is_five_people():
    at_threshold = make_analysis(hazard_types=["structural"], severity=2, people_exposed=5)
    below_threshold = make_analysis(hazard_types=["structural"], severity=2, people_exposed=4)
    assert logic_manager.determine_priority(at_threshold)[0] == "High"
    assert logic_manager.determine_priority(below_threshold)[0] == "Low"


# ======================================================================
# Routing (teams) and action text
# ======================================================================
def test_teams_for_fire_injury_add_emergency_response_first():
    teams = logic_manager.determine_teams(SAMPLE_FIRE_INJURY["analysis"], "Critical")
    assert teams == ["Emergency Response", "Fire Safety"]


def test_teams_follow_hazard_precedence():
    teams = logic_manager.determine_teams(make_analysis(hazard_types=["water", "electrical"]), "High")
    assert teams == ["Electrical", "Maintenance"]


def test_teams_have_no_duplicates():
    teams = logic_manager.determine_teams(make_analysis(hazard_types=["water", "slip_trip", "structural"]), "Low")
    assert teams == ["Maintenance"]


def test_injury_below_critical_does_not_call_emergency_response():
    teams = logic_manager.determine_teams(make_analysis(injury_present=True), "High")
    assert "Emergency Response" not in teams


def test_action_text_matches_priority_and_names_teams():
    assert "IMMEDIATE" in logic_manager.determine_action("Critical", ["Fire Safety"])
    high = logic_manager.determine_action("High", ["Electrical", "Maintenance"])
    assert "Electrical, Maintenance" in high and "1 hour" in high
    assert "today" in logic_manager.determine_action("Medium", ["Maintenance"])
    assert "routine" in logic_manager.determine_action("Low", ["Maintenance"])
    assert "Manual triage" in logic_manager.determine_action("Unknown", [])


def test_low_confidence_needs_manual_review():
    assert logic_manager.needs_manual_review(make_analysis(confidence=0.59)) is True
    assert logic_manager.needs_manual_review(make_analysis(confidence=0.6)) is False


# ======================================================================
# Full outcome decision (triage_incident): dispatch / reject / manual / flag
# ======================================================================
def test_triage_proposal_example_is_critical_dispatch():
    decision = logic_manager.triage_incident(SAMPLE_ELECTRICAL_WATER)
    assert decision["outcome"] == logic_manager.OUTCOME_DISPATCH
    assert decision["priority"] == "Critical"
    assert decision["teams"] == ["Electrical", "Maintenance"]
    assert decision["notify_staff"] is True
    assert decision["needs_manual_review"] is False


def test_triage_rejects_non_hazard():
    decision = logic_manager.triage_incident(SAMPLE_NOT_A_HAZARD)
    assert decision["outcome"] == logic_manager.OUTCOME_REJECTED
    assert decision["priority"] == "Rejected"
    assert decision["teams"] == []
    assert decision["notify_staff"] is False


def test_triage_api_failure_goes_to_manual_triage():
    decision = logic_manager.triage_incident(SAMPLE_API_FAILURE)
    assert decision["outcome"] == logic_manager.OUTCOME_MANUAL
    assert decision["priority"] == "Unrated"
    assert decision["teams"] == ["Workplace Safety"]
    assert decision["needs_manual_review"] is True
    assert decision["notify_staff"] is True
    assert "api_failure" in decision["reasons"][0]


def test_triage_malformed_ai_output_goes_to_manual_triage():
    decision = logic_manager.triage_incident(SAMPLE_MALFORMED)
    assert decision["priority"] == "Unrated"
    assert "malformed_response" in decision["reasons"][0]


def test_triage_low_confidence_is_flagged_and_notifies():
    decision = logic_manager.triage_incident(make_result(severity=1, confidence=0.4))
    assert decision["priority"] == "Low"
    assert decision["needs_manual_review"] is True
    assert decision["notify_staff"] is True
    assert any("Low AI confidence" in reason for reason in decision["reasons"])


def test_triage_low_priority_high_confidence_does_not_notify():
    decision = logic_manager.triage_incident(make_result(severity=1, confidence=0.95))
    assert decision["notify_staff"] is False


def test_triage_is_deterministic_for_the_same_ai_output():
    assert logic_manager.triage_incident(SAMPLE_STRUCTURAL_CROWD) == logic_manager.triage_incident(SAMPLE_STRUCTURAL_CROWD)


# ======================================================================
# Duplicate report rule (location + shared hazard + time window)
# ======================================================================
NOW = "2026-10-12T10:00:00+00:00"


def open_incident(incident_id: str, location: str, hazards: list[str], reported_at: str) -> dict:
    return {"id": incident_id, "status": "pending_review", "location": location, "reported_at": reported_at,
            "ai": {"analysis": make_analysis(hazard_types=hazards)}, "decision": {"priority": "Low", "teams": []}}


def test_normalise_location_ignores_case_and_spaces():
    assert logic_manager.normalise_location("  Lab   3 ") == logic_manager.normalise_location("lab 3")


def test_hours_between_and_bad_timestamps():
    assert logic_manager.hours_between("2026-10-12T08:00:00+00:00", NOW) == 2.0
    assert logic_manager.hours_between("not a date", NOW) is None


def test_duplicate_found_for_same_place_shared_hazard_within_window():
    existing = [open_incident("INC-0001", "Lab 3", ["water", "electrical"], "2026-10-12T09:30:00+00:00")]
    duplicate_id, reason = logic_manager.find_duplicate("  lab   3 ", make_analysis(hazard_types=["water"]), NOW, existing)
    assert duplicate_id == "INC-0001"
    assert "30 min apart" in reason and "water" in reason


def test_no_duplicate_when_any_condition_fails():
    analysis = make_analysis(hazard_types=["water"])
    other_place = [open_incident("INC-0001", "Lobby", ["water"], "2026-10-12T09:30:00+00:00")]
    other_hazard = [open_incident("INC-0002", "Lab 3", ["fire"], "2026-10-12T09:30:00+00:00")]
    too_old = [open_incident("INC-0003", "Lab 3", ["water"], "2026-10-12T05:00:00+00:00")]
    for existing in (other_place, other_hazard, too_old):
        assert logic_manager.find_duplicate("Lab 3", analysis, NOW, existing) == ("", "")


def test_no_duplicate_check_for_non_hazard_or_failed_ai():
    existing = [open_incident("INC-0001", "Lab 3", ["water"], "2026-10-12T09:30:00+00:00")]
    assert logic_manager.find_duplicate("Lab 3", None, NOW, existing) == ("", "")
    assert logic_manager.find_duplicate("Lab 3", SAMPLE_NOT_A_HAZARD["analysis"], NOW, existing) == ("", "")


def test_duplicate_picks_most_recent_match():
    existing = [
        open_incident("INC-0001", "Lab 3", ["water"], "2026-10-12T08:00:00+00:00"),
        open_incident("INC-0002", "Lab 3", ["water"], "2026-10-12T09:00:00+00:00"),
        open_incident("INC-0003", "Lab 3", ["water"], "not a date"),
    ]
    duplicate_id, _ = logic_manager.find_duplicate("Lab 3", make_analysis(hazard_types=["water"]), NOW, existing)
    assert duplicate_id == "INC-0002"


def test_flag_duplicate_keeps_priority_and_marks_for_review():
    decision = logic_manager.triage_incident(make_result(severity=1, confidence=0.95))
    flagged = logic_manager.flag_duplicate(decision, "INC-0001", "Possible duplicate of INC-0001")
    assert flagged["priority"] == decision["priority"]
    assert flagged["duplicate_of"] == "INC-0001"
    assert flagged["needs_manual_review"] is True
    assert flagged["reasons"][-1] == "Possible duplicate of INC-0001"
    assert "duplicate_of" not in decision  # original decision left untouched
    assert logic_manager.flag_duplicate(decision, "", "") is decision


# ======================================================================
# Admin review helpers: urgency, sorting, final decision
# ======================================================================
def test_is_urgent():
    for priority in ("Critical", "High", "Unrated"):
        assert logic_manager.is_urgent({"priority": priority})
    for priority in ("Medium", "Low", "Rejected"):
        assert not logic_manager.is_urgent({"priority": priority})


def test_sort_by_urgency_most_urgent_then_oldest_first():
    records = [
        {"id": "INC-0001", "reported_at": "2026-10-01T09:00:00", "decision": {"priority": "Low"}},
        {"id": "INC-0002", "reported_at": "2026-10-01T10:00:00", "decision": {"priority": "Critical"}},
        {"id": "INC-0003", "reported_at": "2026-10-01T08:00:00", "decision": {"priority": "Critical"}},
        {"id": "INC-0004", "reported_at": "2026-10-01T07:00:00", "decision": {"priority": "Medium"}},
    ]
    order = [record["id"] for record in logic_manager.sort_by_urgency(records)]
    assert order == ["INC-0003", "INC-0002", "INC-0004", "INC-0001"]


def test_sort_uses_admin_final_decision_over_recommendation():
    records = [
        {"id": "A", "reported_at": "1", "decision": {"priority": "Critical"}, "final": {"priority": "Low"}},
        {"id": "B", "reported_at": "2", "decision": {"priority": "Medium"}},
    ]
    assert [record["id"] for record in logic_manager.sort_by_urgency(records)] == ["B", "A"]


def test_build_final_decision():
    final = logic_manager.build_final_decision("High", ["Security"], "checked on site", "admin01", "2026-10-12T10:00:00")
    assert final["priority"] == "High"
    assert final["teams"] == ["Security"]
    assert final["note"] == "checked on site"
    assert final["reviewed_by"] == "admin01"
    assert "Security" in final["action"]


# ======================================================================
# Plain-Python runner (no pytest needed)
# ======================================================================
def run_all_tests() -> int:
    """Run every test_* function in this file. Returns the number of failures."""
    tests = [(name, item) for name, item in sorted(globals().items())
             if name.startswith("test_") and callable(item)]
    failures = []
    for name, test in tests:
        try:
            test()
        except Exception:  # report every failure and keep going
            failures.append(name)
            sys.stdout.write(f"FAIL  {name}\n{traceback.format_exc()}\n")
        else:
            sys.stdout.write(f"PASS  {name}\n")
    sys.stdout.write(f"\n{len(tests) - len(failures)} passed, {len(failures)} failed (no live API used)\n")
    return len(failures)


if __name__ == "__main__":
    sys.exit(1 if run_all_tests() else 0)
