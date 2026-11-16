"""AI MANAGER - ai_manager/response_validator.py

Role: Builds prompts, calls the AI provider (Gemini, with Groq as backup), parses the JSON reply
and validates its schema. Every record passes through here.
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import json
import re

from constants import HAZARD_TYPES, MAX_SEVERITY, MAX_SUMMARY_LENGTH, MIN_SEVERITY
from domain.ai_analysis import AIAnalysis
from domain.check_result import CheckResult
from errors.invalid_ai_response_error import InvalidAIResponseError


class ResponseValidator:
    """Parses model text into JSON and checks it against the required schema."""

    REQUIRED_KEYS = (
        "is_hazard_report", "hazard_types", "severity", "injury_present",
        "people_exposed", "confidence", "summary",
    )

    @staticmethod
    def parse_json_text(text: object) -> dict | None:
        """Extract a JSON object from model text (tolerates markdown fences). None if impossible."""
        if not isinstance(text, str):
            return None
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            data = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None

    def validate(self, data: object) -> AIAnalysis:
        """Return a clean AIAnalysis or raise InvalidAIResponseError saying what was wrong."""
        if not isinstance(data, dict):
            raise InvalidAIResponseError("response is not a JSON object")
        missing = [key for key in self.REQUIRED_KEYS if key not in data]
        if missing:
            raise InvalidAIResponseError("missing keys: " + ", ".join(missing))

        is_hazard_report = self._flag(data, "is_hazard_report")
        hazards = self._hazards(data["hazard_types"])
        if is_hazard_report and not hazards:
            raise InvalidAIResponseError("hazard_types is empty for a hazard report")
        severity = self._severity(data["severity"])
        injury_present = self._flag(data, "injury_present")
        people_exposed = self._people_exposed(data["people_exposed"])
        confidence = self._confidence(data["confidence"])
        if not isinstance(data["summary"], str):
            raise InvalidAIResponseError("summary must be text")

        return AIAnalysis(
            is_hazard_report=is_hazard_report,
            hazard_types=hazards,
            severity=severity,
            injury_present=injury_present,
            people_exposed=people_exposed,
            confidence=confidence,
            summary=data["summary"].strip()[:MAX_SUMMARY_LENGTH],
        )

    # ------------------------------------------------- one check per field
    @staticmethod
    def _is_whole_number(value: object) -> bool:
        """True for 3 and 3.0 (models sometimes send whole numbers as floats), never for True/False."""
        if isinstance(value, bool):
            return False
        return isinstance(value, int) or (isinstance(value, float) and value.is_integer())

    @staticmethod
    def _flag(data: dict, key: str) -> bool:
        if not isinstance(data[key], bool):
            raise InvalidAIResponseError(f"{key} must be true or false")
        return data[key]

    @staticmethod
    def _hazards(value: object) -> tuple[str, ...]:
        """Known hazard names, lower-cased, in the order given, without repeats."""
        if not isinstance(value, list):
            raise InvalidAIResponseError("hazard_types must be a list")
        hazards: list[str] = []
        for item in value:
            if not isinstance(item, str) or item.strip().lower() not in HAZARD_TYPES:
                raise InvalidAIResponseError(f"unknown hazard type: {item!r}")
            name = item.strip().lower()
            if name not in hazards:
                hazards.append(name)
        return tuple(hazards)

    def _severity(self, value: object) -> int:
        if not self._is_whole_number(value) or not MIN_SEVERITY <= int(value) <= MAX_SEVERITY:
            raise InvalidAIResponseError(f"severity must be a whole number from {MIN_SEVERITY} to {MAX_SEVERITY}")
        return int(value)

    def _people_exposed(self, value: object) -> int:
        if not self._is_whole_number(value) or int(value) < 0:
            raise InvalidAIResponseError("people_exposed must be a whole number >= 0")
        return int(value)

    @staticmethod
    def _confidence(value: object) -> float:
        if not CheckResult.is_number(value) or not 0.0 <= float(value) <= 1.0:
            raise InvalidAIResponseError("confidence must be a number from 0.0 to 1.0")
        return float(value)
