"""IO MANAGER - io_manager/screens.py

Role: Turns records, tables and summaries into lines of text. It never prints or reads input, so every screen can be tested as plain text.
Class in this file: Screens
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from collections.abc import Sequence

from constants import LINE, THIN
from domain.incident import Incident
from logic_manager.summary_report import SummaryReport


class Screens:
    """Builds the text for every screen. IOManager decides when and where the text is printed."""

    @staticmethod
    def teams(teams: Sequence[str]) -> str:
        return ", ".join(teams) if teams else "-"

    def incident_line(self, record: Incident) -> str:
        """One row of an incident table (the priority and teams shown are the final ones when reviewed)."""
        shown = record.effective_decision
        duplicate_of = record.decision.duplicate_of
        return (
            f"{record.id or '?':<9}"
            f"{shown.priority:<10}"
            f"{record.status:<16}"
            f"{record.location[:20]:<21}"
            f"{self.teams(shown.teams)}"
            + (f"  [dup of {duplicate_of}]" if duplicate_of else "")
        )

    def incident_table(self, incidents: Sequence[Incident], title: str) -> list[str]:
        lines = [title]
        if not incidents:
            return lines + ["  (none)"]
        lines.append(f"{'ID':<9}{'PRIORITY':<10}{'STATUS':<16}{'LOCATION':<21}CONTACT")
        lines.append(THIN)
        return lines + [self.incident_line(record) for record in incidents]

    def incident_detail(self, record: Incident) -> str:
        decision, ai, analysis = record.decision, record.ai, record.ai.analysis
        lines = [
            f"ID              : {record.id}",
            f"Status          : {record.status}",
            f"Reported        : {record.reported_at} by {record.reporter_id}",
            f"Location        : {record.location}",
            f"Description     : {record.description}",
            THIN,
        ]
        if analysis:
            lines += [
                "AI ANALYSIS",
                f"  Hazards        : {', '.join(analysis.hazard_types) or '-'}",
                f"  Severity       : {analysis.severity}/5",
                f"  Injury present : {'yes' if analysis.injury_present else 'no'}",
                f"  People exposed : {analysis.people_exposed}",
                f"  Confidence     : {analysis.confidence:.2f}",
                f"  Summary        : {analysis.summary}",
            ]
        else:
            lines.append(f"AI ANALYSIS UNAVAILABLE ({ai.error_type or 'unknown'}): {ai.error}")
        lines += [
            THIN,
            "RULE ENGINE RECOMMENDATION",
            f"  Priority       : {decision.priority}",
            f"  Contact        : {self.teams(decision.teams)}",
            f"  Action         : {decision.action}",
        ]
        for reason in decision.reasons:
            lines.append(f"  - {reason}")
        if decision.needs_manual_review:
            lines.append("  ! Flagged for extra human checking")
        if decision.duplicate_of:
            lines.append(f"  ! Possible duplicate of {decision.duplicate_of} (reject with a note if it is the same hazard)")
        if record.final:
            lines += [
                THIN,
                "ADMIN DECISION",
                f"  Priority       : {record.final.priority}",
                f"  Contact        : {self.teams(record.final.teams)}",
                f"  Reviewed by    : {record.final.reviewed_by} at {record.final.reviewed_at}",
                f"  Note           : {record.final.note or '-'}",
            ]
        return "\n".join(lines)

    def submission(self, record: Incident) -> list[str]:
        """What the employee sees after a report is saved."""
        decision = record.decision
        analysis = record.ai.analysis
        lines = [THIN, f"Report saved as {record.id or '?'}"]
        if record.status == "auto_rejected":
            lines += [
                "This did not look like a workplace hazard, so it was not dispatched.",
                "If you meant to report a hazard, please submit again with more detail.",
            ]
        elif analysis is None:
            lines += [
                "Automated analysis was unavailable. Safety staff have been notified to triage this manually.",
                # Technical detail (exception text) is for admins and the log, not for the reporter.
                f"Reason: {record.ai.error_type or 'unknown'}",
            ]
        else:
            lines += [
                f"Hazards detected     : {', '.join(analysis.hazard_types)}",
                f"Provisional priority : {decision.priority}",
                f"Recommended team(s)  : {self.teams(decision.teams)}",
                f"Recommended action   : {decision.action}",
            ]
            if decision.notify_staff:
                lines.append("Safety staff have been notified and will review this report.")
            else:
                lines.append("Safety staff will review this report.")
            if decision.duplicate_of:
                lines.append(
                    f"Note: this looks like the same hazard as {decision.duplicate_of}, "
                    "which is already awaiting review. Staff will link the two."
                )
        return lines + [THIN]

    def dispatch_notice(self, record: Incident) -> list[str]:
        final = record.final
        lines = [THIN, f"{record.id} marked '{record.status}'."]
        if final and final.teams:
            lines.append(f"DISPATCH NOTICE -> {self.teams(final.teams)} | Priority {final.priority}")
            lines.append(f"Location: {record.location}")
            lines.append(f"Action  : {final.action}")
        return lines + [THIN]

    @staticmethod
    def counts(counts: dict[str, int]) -> list[str]:
        return [f"  {name.replace('_', ' ').capitalize():<22}{count:>4}" for name, count in counts.items()] or [
            "  (none)"
        ]

    @staticmethod
    def _section(title: str, body: list[str]) -> list[str]:
        return [THIN, f"  {title}", THIN, *body, ""]

    def summary(self, report: SummaryReport) -> str:
        lines = [
            LINE,
            "  SAFETRIAGE SUMMARY REPORT",
            LINE,
            *self._section("OVERVIEW", [
                f"  Total incidents on file : {report.total}",
                f"  Urgent and still pending: {report.pending_urgent}",
                f"  AI unavailable          : {report.ai_unavailable}",
                f"  Low confidence / flagged: {report.low_confidence}",
            ]),
            *self._section("BY PRIORITY  (final decision where reviewed)", self.counts(report.by_priority)),
            *self._section("BY STATUS", self.counts(report.by_status)),
            *self._section("HAZARD TYPES MENTIONED  (most frequent first)", self.counts(report.by_hazard)),
            *self._section("HOTSPOT LOCATIONS", [
                f"  {place[:30]:<32}{count:>4}" for place, count in report.hotspots
            ] or ["  (none)"]),
            LINE,
        ]
        return "\n".join(lines)
