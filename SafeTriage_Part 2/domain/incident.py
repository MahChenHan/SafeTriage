"""DOMAIN MODELS (shared) - domain/incident.py

Role: Immutable records passed between the four managers. No I/O and no business rules.
Class in this file: Incident
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from domain.ai_result import AIResult
from domain.decision import Decision
from domain.final_decision import FinalDecision


@dataclass(frozen=True)
class Incident:
    """One stored hazard report with its AI result, recommendation and review."""

    reporter_id: str
    location: str
    description: str
    ai: AIResult
    decision: Decision
    status: str
    reported_at: str
    id: str = ""
    final: FinalDecision | None = None
    updated_at: str = ""

    @property
    def effective_decision(self) -> Decision | FinalDecision:
        """The admin's decision when there is one, otherwise the rule engine's."""
        return self.final if self.final is not None else self.decision

    @property
    def effective_priority(self) -> str:
        return self.effective_decision.priority

    @property
    def effective_teams(self) -> tuple[str, ...]:
        return self.effective_decision.teams

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "reporter_id": self.reporter_id,
            "location": self.location,
            "description": self.description,
            "ai": self.ai.to_dict(),
            "decision": self.decision.to_dict(),
            "status": self.status,
            "reported_at": self.reported_at,
        }
        if self.final is not None:
            data["final"] = self.final.to_dict()
        if self.updated_at:
            data["updated_at"] = self.updated_at
        return data

    @classmethod
    def from_dict(cls, data: object) -> Incident:
        """Rebuild a stored incident. Raises ValueError when it is too damaged to display."""
        if not isinstance(data, dict):
            raise ValueError("incident must be an object")
        if not isinstance(data.get("id"), str) or not isinstance(data.get("status"), str):
            raise ValueError("incident needs a text id and status")
        if not isinstance(data.get("reported_at", ""), str):
            raise ValueError("reported_at must be text")
        raw_final = data.get("final")
        return cls(
            id=data["id"],
            reporter_id=str(data.get("reporter_id", "")),
            location=str(data.get("location", "")),
            description=str(data.get("description", "")),
            ai=AIResult.from_dict(data.get("ai")),
            decision=Decision.from_dict(data.get("decision")),
            status=data["status"],
            reported_at=data.get("reported_at", ""),
            final=FinalDecision.from_dict(raw_final) if raw_final is not None else None,
            updated_at=str(data.get("updated_at", "")),
        )

    def with_id(self, incident_id: str) -> Incident:
        return replace(self, id=incident_id)

    def with_review(self, status: str, final: FinalDecision, updated_at: str) -> Incident:
        return replace(self, status=status, final=final, updated_at=updated_at)
