"""LOGIC MANAGER - logic_manager/logic_manager.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing, duplicates and summary reports.
Class in this file: LogicManager
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from typing import Iterable

from constants import LOW_CONFIDENCE_THRESHOLD, OUTCOME_DISPATCH, OUTCOME_MANUAL, OUTCOME_REJECTED, PRIORITY_LEVELS, PURGEABLE_STATUSES, URGENCY_RANK
from domain.ai_analysis import AIAnalysis
from domain.ai_result import AIResult
from domain.decision import Decision
from domain.final_decision import FinalDecision
from domain.incident import Incident
from logic_manager.base_severity_rule import BaseSeverityRule
from logic_manager.duplicate_detector import DuplicateDetector
from logic_manager.electrical_water_rule import ElectricalWaterRule
from logic_manager.fire_injury_rule import FireInjuryRule
from logic_manager.injury_rule import InjuryRule
from logic_manager.multi_hazard_escalation_rule import MultiHazardEscalationRule
from logic_manager.structural_crowd_rule import StructuralCrowdRule
from logic_manager.summary_report import SummaryReport
from logic_manager.summary_report_builder import SummaryReportBuilder
from logic_manager.team_router import TeamRouter
from logic_manager.triage_rule import TriageRule


class LogicManager:
    """Applies the domain rules to AI-enriched records."""

    def __init__(self, extra_rules: Iterable[TriageRule] = ()) -> None:
        # Composition: these parts are created here and live and die with the manager.
        self._base_rule = BaseSeverityRule()
        self._rules: list[TriageRule] = [
            MultiHazardEscalationRule(),
            InjuryRule(),
            StructuralCrowdRule(),
            ElectricalWaterRule(),
            FireInjuryRule(),
            *extra_rules,
        ]
        self._router = TeamRouter()                    # composition: owns the routing rules
        self._duplicates = DuplicateDetector()
        self._reports = SummaryReportBuilder()

    # ------------------------------------------------------------ extension
    def add_rule(self, rule: TriageRule) -> None:
        """Plug in another business rule without touching existing code (Open/Closed)."""
        self._rules.append(rule)

    @property
    def rule_names(self) -> list[str]:
        return [type(rule).__name__ for rule in self._rules]

    # ------------------------------------------------------------- priority
    def determine_priority(self, analysis: AIAnalysis) -> tuple[str, list[str]]:
        """Run every rule in order. Returns (priority, reasons for each rule that fired)."""
        start = self._base_rule.apply(analysis, 0)
        level, reasons = start.level, [start.reason]
        for rule in self._rules:  # polymorphism: same call, different rule behaviour
            result = rule.apply(analysis, level)
            if result.fired:
                level = result.level
                reasons.append(result.reason)
        return PRIORITY_LEVELS[level], reasons

    @staticmethod
    def needs_manual_review(analysis: AIAnalysis) -> bool:
        """Flag low-confidence AI output for extra human attention."""
        return analysis.confidence < LOW_CONFIDENCE_THRESHOLD

    def triage(self, ai_result: AIResult) -> Decision:
        """Turn an AIResult into a Decision (outcome, priority, teams, action, reasons)."""
        if not ai_result.ok or ai_result.analysis is None:
            reason = f"AI analysis unavailable ({ai_result.error_type or 'unknown'}): {ai_result.error}"
            return Decision(
                outcome=OUTCOME_MANUAL, priority="Unrated", teams=("Workplace Safety",),
                action=self._router.action_for("Unrated", []), notify_staff=True,
                needs_manual_review=True, reasons=(reason,),
            )

        analysis = ai_result.analysis
        if not analysis.is_hazard_report:
            return Decision(
                outcome=OUTCOME_REJECTED, priority="Rejected", teams=(),
                action=self._router.action_for("Rejected", []), notify_staff=False,
                needs_manual_review=False,
                reasons=("AI judged this text is not a workplace hazard report",),
            )

        priority, reasons = self.determine_priority(analysis)
        teams = self._router.teams_for(analysis, priority)
        manual = self.needs_manual_review(analysis)
        if manual:
            reasons.append(f"Low AI confidence ({analysis.confidence:.2f}): human check advised")
        return Decision(
            outcome=OUTCOME_DISPATCH, priority=priority, teams=tuple(teams),
            action=self._router.action_for(priority, teams),
            notify_staff=priority in ("High", "Critical") or manual,
            needs_manual_review=manual, reasons=tuple(reasons),
        )

    # ----------------------------------------------------------- duplicates
    def find_duplicate(self, location: str, analysis: AIAnalysis | None, reported_at: str,
                       open_incidents: Iterable[Incident]) -> tuple[str, str]:
        return self._duplicates.find(location, analysis, reported_at, open_incidents)

    @staticmethod
    def flag_duplicate(decision: Decision, duplicate_id: str, reason: str) -> Decision:
        """Mark a decision as a possible duplicate. Priority is unchanged: a human decides."""
        return decision.flagged_duplicate(duplicate_id, reason) if duplicate_id else decision

    # -------------------------------------------------------- admin helpers
    @staticmethod
    def is_urgent(decision: Decision | FinalDecision) -> bool:
        """True when an admin should look at this straight away."""
        return decision.priority in ("Critical", "High", "Unrated")

    @staticmethod
    def sort_by_urgency(incidents: Iterable[Incident]) -> list[Incident]:
        """Most urgent first; oldest first within the same urgency."""
        return sorted(
            incidents,
            key=lambda item: (-URGENCY_RANK.get(item.effective_priority, 0), item.reported_at),
        )

    def build_final_decision(self, priority: str, teams: Iterable[str], note: str,
                             admin_id: str, reviewed_at: str) -> FinalDecision:
        """The admin-confirmed decision stored on a reviewed incident."""
        team_list = tuple(teams)
        return FinalDecision(
            priority=priority, teams=team_list, action=self._router.action_for(priority, team_list),
            note=note, reviewed_by=admin_id, reviewed_at=reviewed_at,
        )

    @staticmethod
    def can_purge(incident: Incident) -> bool:
        """Only incidents that never led to a dispatch may be permanently deleted."""
        return incident.status in PURGEABLE_STATUSES

    # -------------------------------------------------------------- reports
    def summarise(self, incidents: list[Incident]) -> SummaryReport:
        return self._reports.build(incidents)
