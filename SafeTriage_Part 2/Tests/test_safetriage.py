"""TESTS - tests/test_safetriage.py

Covers all four managers (IO, AI, Logic, Data), the domain models, sessions and the new features.
No live AI: the tests use sample responses and a fake provider.
Run: python -m unittest discover -s tests -p "test_safetriage.py" -v
"""
from __future__ import annotations
import json
import os
import unittest.mock
import sqlite3
import tempfile
import threading
import unittest
from collections.abc import Iterable
from dataclasses import replace

from ai_manager.ai_manager import AIManager
from ai_manager.ai_provider import AIProvider
from ai_manager.fallback_ai_provider import FallbackAIProvider
from ai_manager.gemini_provider import GeminiProvider
from ai_manager.groq_provider import GroqProvider
from ai_manager.prompt_builder import PromptBuilder
from ai_manager.response_validator import ResponseValidator
from application import Application
from constants import ERROR_API_FAILURE, ERROR_MALFORMED, OUTCOME_DISPATCH, OUTCOME_MANUAL, OUTCOME_REJECTED
from data_manager.data_manager import DataManager
from data_manager.incident_filter import IncidentFilter
from data_manager.incident_repository import IncidentRepository
from data_manager.json_incident_repository import JsonIncidentRepository
from data_manager.repository_factory import RepositoryFactory
from data_manager.sqlite_incident_repository import SqliteIncidentRepository
from domain.ai_analysis import AIAnalysis
from domain.ai_result import AIResult
from domain.decision import Decision
from domain.final_decision import FinalDecision
from domain.hazard_report import HazardReport
from domain.incident import Incident
from errors.ai_timeout_error import AITimeoutError
from errors.conflict_error import ConflictError
from errors.incident_not_found_error import IncidentNotFoundError
from errors.invalid_ai_response_error import InvalidAIResponseError
from errors.storage_error import StorageError
from io_manager.input_validator import InputValidator
from io_manager.io_manager import IOManager
from io_manager.screens import Screens
from logic_manager.duplicate_detector import DuplicateDetector
from logic_manager.electrical_water_rule import ElectricalWaterRule
from logic_manager.fire_injury_rule import FireInjuryRule
from logic_manager.injury_rule import InjuryRule
from logic_manager.logic_manager import LogicManager
from logic_manager.minimum_level_rule import MinimumLevelRule
from logic_manager.multi_hazard_escalation_rule import MultiHazardEscalationRule
from logic_manager.rule_result import RuleResult
from logic_manager.structural_crowd_rule import StructuralCrowdRule
from logic_manager.team_router import TeamRouter
from logic_manager.triage_rule import TriageRule
from sessions.admin_session import AdminSession
from sessions.session import Session
from sessions.user_session import UserSession


# ==========================================================================
# Shared sample data and fake providers
# ==========================================================================

"""Shared test doubles and hardcoded sample AI responses (no live API is ever used)."""




class SampleFactory:
    """Builds valid sample objects; every argument can be overridden per test."""

    @staticmethod
    def make_analysis(**changes) -> AIAnalysis:
        """A valid AI analysis. Defaults describe a minor slip hazard; override any field."""
        values = {
            "is_hazard_report": True, "hazard_types": ("slip_trip",), "severity": 2,
            "injury_present": False, "people_exposed": 1, "confidence": 0.9,
            "summary": "Wet floor near the pantry.",
        }
        values.update(changes)
        values["hazard_types"] = tuple(values["hazard_types"])
        return AIAnalysis(**values)

    @staticmethod
    def make_result(**changes) -> AIResult:
        """A successful AIResult wrapping SampleFactory.make_analysis(**changes)."""
        return AIResult(ok=True, analysis=SampleFactory.make_analysis(**changes), model="sample", attempts=1)

    @staticmethod
    def raw_reply(**changes) -> str:
        """What a well-behaved model would send back: one JSON object as text."""
        data = {
            "is_hazard_report": True, "hazard_types": ["slip_trip"], "severity": 2,
            "injury_present": False, "people_exposed": 1, "confidence": 0.9, "summary": "Wet floor.",
        }
        data.update(changes)
        return json.dumps(data)

    @staticmethod
    def make_incident(incident_id: str = "", location: str = "Lab 3", hazards=("water",),
                      reported_at: str = "2026-10-12T09:30:00+00:00", status: str = "pending_review",
                      priority: str = "Low", analysis: AIAnalysis | None = None, final: FinalDecision | None = None,
                      ai: AIResult | None = None, confidence_flag: bool = False) -> Incident:
        """A stored incident with sensible defaults, for repository, logic and session tests."""
        if ai is None:
            ai = AIResult(ok=True, analysis=analysis or SampleFactory.make_analysis(hazard_types=hazards), model="sample", attempts=1)
        decision = Decision(outcome="dispatch_recommended", priority=priority, teams=("Maintenance",),
                            action="Log for Maintenance.", needs_manual_review=confidence_flag)
        return Incident(id=incident_id, reporter_id="Alice", location=location, description="Water on the floor",
                        ai=ai, decision=decision, status=status, reported_at=reported_at, final=final)


# Proposal example: electrical + water, severity 5, 6 people, confidence 0.96
SAMPLE_ELECTRICAL_WATER = SampleFactory.make_result(
    hazard_types=["electrical", "water"], severity=5, people_exposed=6, confidence=0.96,
    summary="Water leaking onto a live power socket.")
SAMPLE_FIRE_INJURY = SampleFactory.make_result(
    hazard_types=["fire"], severity=2, injury_present=True, people_exposed=2,
    summary="Small bin fire, one person burned their hand.")
SAMPLE_STRUCTURAL_CROWD = SampleFactory.make_result(
    hazard_types=["structural"], severity=2, people_exposed=40,
    summary="Crack in ceiling above lecture theatre seating.")
SAMPLE_NOT_A_HAZARD = SampleFactory.make_result(
    is_hazard_report=False, hazard_types=[], severity=1, people_exposed=0,
    summary="User is asking about the cafeteria menu.")
SAMPLE_API_FAILURE = AIResult(ok=False, analysis=None, model="sample", attempts=3,
                              error_type="api_failure", error="ConnectionError: network unreachable")
SAMPLE_MALFORMED = AIResult(ok=False, analysis=None, model="sample", attempts=3,
                            error_type="malformed_response", error="missing keys: severity")


class ScriptedProvider(AIProvider):
    """Test double for the AIProvider interface: returns or raises the next scripted item."""

    def __init__(self, replies: Iterable[object]) -> None:
        self._replies = list(replies)
        self.calls = 0
        self.prompts: list[str] = []

    def generate(self, prompt: str, model: str) -> str:
        self.calls += 1
        self.prompts.append(prompt)
        item = self._replies[min(self.calls, len(self._replies)) - 1]
        if isinstance(item, BaseException):
            raise item
        return item  # type: ignore[return-value]


class ScriptedIO:
    """Feeds scripted answers to IOManager and records everything it prints."""

    def __init__(self, answers: Iterable[str]) -> None:
        self._answers = list(answers)
        self.output: list[str] = []

    def input(self, prompt: str) -> str:
        self.output.append(prompt)
        if not self._answers:
            raise EOFError("script ran out of answers")
        return self._answers.pop(0)

    def print(self, message: str = "") -> None:
        self.output.append(message)

    @property
    def text(self) -> str:
        return "\n".join(self.output)
