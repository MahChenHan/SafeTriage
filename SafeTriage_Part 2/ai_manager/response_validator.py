"""AI MANAGER - ai_manager/response_validator.py

Role: Builds prompts, calls the Gemini API, parses the JSON reply and validates its schema. Every record passes through here.
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import json
import re

from constants import HAZARD_TYPES
from domain.ai_analysis import AIAnalysis
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

    @staticmethod
    def _is_whole_number(value: object) -> bool:
        if isinstance(value, bool):
            return False
        return isinstance(value, int) or (isinstance(value, float) and value.is_integer())

    @staticmethod
    def _is_number(value: object) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def validate(self, data: object) -> AIAnalysis:
        """Return a clean AIAnalysis or raise InvalidAIResponseError saying what was wrong."""
        if not isinstance(data, dict):
            raise InvalidAIResponseError("response is not a JSON object")
        missing = [key for key in self.REQUIRED_KEYS if key not in data]
        if missing:
            raise InvalidAIResponseError("missing keys: " + ", ".join(missing))
        if not isinstance(data["is_hazard_report"], bool):
            raise InvalidAIResponseError("is_hazard_report must be true or false")
        if not isinstance(data["hazard_types"], list):
            raise InvalidAIResponseError("hazard_types must be a list")

        hazards: list[str] = []
        for item in data["hazard_types"]:
            if not isinstance(item, str) or item.strip().lower() not in HAZARD_TYPES:
                raise InvalidAIResponseError(f"unknown hazard type: {item!r}")
            name = item.strip().lower()
            if name not in hazards:
                hazards.append(name)
        if data["is_hazard_report"] and not hazards:
            raise InvalidAIResponseError("hazard_types is empty for a hazard report")

        if not self._is_whole_number(data["severity"]) or not 1 <= int(data["severity"]) <= 5:
            raise InvalidAIResponseError("severity must be a whole number from 1 to 5")
        if not isinstance(data["injury_present"], bool):
            raise InvalidAIResponseError("injury_present must be true or false")
        if not self._is_whole_number(data["people_exposed"]) or int(data["people_exposed"]) < 0:
            raise InvalidAIResponseError("people_exposed must be a whole number >= 0")
        if not self._is_number(data["confidence"]) or not 0.0 <= float(data["confidence"]) <= 1.0:
            raise InvalidAIResponseError("confidence must be a number from 0.0 to 1.0")
        if not isinstance(data["summary"], str):
            raise InvalidAIResponseError("summary must be text")

        return AIAnalysis(
            is_hazard_report=data["is_hazard_report"],
            hazard_types=tuple(hazards),
            severity=int(data["severity"]),
            injury_present=data["injury_present"],
            people_exposed=int(data["people_exposed"]),
            confidence=float(data["confidence"]),
            summary=data["summary"].strip()[:300],
        )
