"""LOGIC MANAGER - logic_manager/team_router.py

Role: Decides which teams to contact for a prioritised incident, and the action text shown to staff.
Class in this file: TeamRouter
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from collections.abc import Iterable

from constants import ACTIONS, HAZARD_PRECEDENCE, TEAM_BY_HAZARD
from domain.ai_analysis import AIAnalysis


class TeamRouter:
    """Routing rules: the hazard types (and a Critical injury) choose the teams; the priority chooses the action text."""

    def teams_for(self, analysis: AIAnalysis, priority: str) -> list[str]:
        """Ordered, de-duplicated list of teams to contact."""
        teams: list[str] = []
        if analysis.injury_present and priority == "Critical":
            teams.append("Emergency Response")
        for hazard in HAZARD_PRECEDENCE:
            if hazard in analysis.hazard_types:
                team = TEAM_BY_HAZARD[hazard]
                if team not in teams:
                    teams.append(team)
        if not teams:
            teams.append("Workplace Safety")
        return teams

    def action_for(self, priority: str, teams: Iterable[str]) -> str:
        """The instruction text for this priority, naming the teams."""
        template = ACTIONS.get(priority, ACTIONS["Unrated"])
        return template.format(teams=", ".join(teams))
