"""LOGIC MANAGER - logic_manager/team_router.py

Role: Applies the domain business rules to AI-enriched records: scores, escalation, routing,
duplicates and summary reports.
Class in this file: TeamRouter
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from collections.abc import Iterable

from constants import (
    ACTIONS, HAZARD_PRECEDENCE, PRIORITY_CRITICAL, PRIORITY_UNRATED, TEAM_BY_HAZARD, TEAM_DEFAULT, TEAM_EMERGENCY,
)
from domain.ai_analysis import AIAnalysis


class TeamRouter:
    """Routing rules: hazard types (and a Critical injury) choose the teams; the priority chooses the action."""

    def teams_for(self, analysis: AIAnalysis, priority: str) -> list[str]:
        """Ordered, de-duplicated list of teams to contact."""
        teams: list[str] = []
        if analysis.injury_present and priority == PRIORITY_CRITICAL:
            teams.append(TEAM_EMERGENCY)
        for hazard in HAZARD_PRECEDENCE:
            if hazard in analysis.hazard_types:
                team = TEAM_BY_HAZARD[hazard]
                if team not in teams:
                    teams.append(team)
        if not teams:
            teams.append(TEAM_DEFAULT)
        return teams

    def action_for(self, priority: str, teams: Iterable[str]) -> str:
        """The instruction text for this priority, naming the teams."""
        template = ACTIONS.get(priority, ACTIONS[PRIORITY_UNRATED])
        return template.format(teams=", ".join(teams))
