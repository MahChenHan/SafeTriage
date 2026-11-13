"""IO MANAGER - io_manager/input_validator.py

Role: Collects and validates user input; displays records, lists, results and summaries. Terminal input/output lives only here.
Class in this file: InputValidator
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import re


class InputValidator:
    """Validation rules for everything a person can type. Each returns '' when acceptable."""

    ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{2,20}$")
    MIN_DESCRIPTION_LENGTH = 10
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_LOCATION_LENGTH = 100
    MAX_NOTE_LENGTH = 300
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 50

    @classmethod
    def validate_id(cls, text: str) -> str:
        if not cls.ID_PATTERN.match(text):
            return "Use 2-20 letters, digits, '-' or '_' (no spaces)."
        return ""

    @classmethod
    def validate_name(cls, text: str) -> str:
        """A person's name: letters and spaces only (no digits or symbols)."""
        if not text:
            return "Please input a valid name."
        if not all(character.isalpha() or character == " " for character in text):
            return "Please input a valid name (letters and spaces only)."
        if not cls.MIN_NAME_LENGTH <= len(text) <= cls.MAX_NAME_LENGTH:
            return f"Please input a valid name ({cls.MIN_NAME_LENGTH}-{cls.MAX_NAME_LENGTH} characters)."
        return ""

    @classmethod
    def validate_location(cls, text: str) -> str:
        if not text:
            return "Location cannot be empty."
        if len(text) > cls.MAX_LOCATION_LENGTH:
            return f"Location must be at most {cls.MAX_LOCATION_LENGTH} characters."
        return ""

    @classmethod
    def validate_description(cls, text: str) -> str:
        if len(text) < cls.MIN_DESCRIPTION_LENGTH:
            return f"Please describe the hazard in at least {cls.MIN_DESCRIPTION_LENGTH} characters."
        if len(text) > cls.MAX_DESCRIPTION_LENGTH:
            return f"Description must be at most {cls.MAX_DESCRIPTION_LENGTH} characters."
        if not any(character.isalpha() for character in text):
            return "Description must contain words, not only numbers or symbols."
        return ""

    @classmethod
    def validate_note(cls, text: str) -> str:
        if not text:
            return "A note is required for this action."
        if len(text) > cls.MAX_NOTE_LENGTH:
            return f"Note must be at most {cls.MAX_NOTE_LENGTH} characters."
        return ""

    @staticmethod
    def parse_number_list(text: str, maximum: int) -> list[int] | None:
        """Parse '1, 3' into [1, 3]. Returns None if any entry is invalid or the list is empty."""
        parts = [part for part in re.split(r"[,\s]+", text.strip()) if part]
        if not parts or not all(part.isdecimal() for part in parts):
            return None
        numbers: list[int] = []
        for part in parts:
            number = int(part)
            if not 1 <= number <= maximum:
                return None
            if number not in numbers:
                numbers.append(number)
        return numbers
