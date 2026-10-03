"""I/O layer for SafeTriage.

Every print() and input() call in the project lives in this module. It collects
and validates user input (re-prompting on bad data) and formats records for display.
"""
import re
from collections.abc import Callable

LINE = "=" * 70
THIN = "-" * 70
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{2,20}$")
MIN_DESCRIPTION_LENGTH = 10
MAX_DESCRIPTION_LENGTH = 1000
MAX_LOCATION_LENGTH = 100
MAX_NOTE_LENGTH = 300
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 50

# ---------------------------------------------------------------- basic I/O
def say(message: str = "") -> None:
    print(message)


def ask(prompt: str) -> str:
    return input(prompt).strip()


def show_message(message: str) -> None:
    say(message)


def show_error(message: str) -> None:
    say(f"[ERROR] {message}")


def show_warning(message: str) -> None:
    say(f"[WARNING] {message}")


def show_heading(title: str) -> None:
    say()
    say(LINE)
    say(title)
    say(LINE)

# --------------------------------------------------------------- validators
# Each validator returns an error message, or "" when the text is acceptable.
def validate_id(text: str) -> str:
    if not ID_PATTERN.match(text):
        return "Use 2-20 letters, digits, '-' or '_' (no spaces)."
    return ""


def validate_name(text: str) -> str:
    """A person's name: letters and spaces only (no digits or symbols)."""
    if not text:
        return "Please input a valid name."
    if not all(character.isalpha() or character == " " for character in text):
        return "Please input a valid name (letters and spaces only)."
    if not MIN_NAME_LENGTH <= len(text) <= MAX_NAME_LENGTH:
        return f"Please input a valid name ({MIN_NAME_LENGTH}-{MAX_NAME_LENGTH} characters)."
    return ""

def validate_location(text: str) -> str:
    if not text:
        return "Location cannot be empty."
    if len(text) > MAX_LOCATION_LENGTH:
        return f"Location must be at most {MAX_LOCATION_LENGTH} characters."
    return ""


def validate_description(text: str) -> str:
    if len(text) < MIN_DESCRIPTION_LENGTH:
        return f"Please describe the hazard in at least {MIN_DESCRIPTION_LENGTH} characters."
    if len(text) > MAX_DESCRIPTION_LENGTH:
        return f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters."
    if not any(character.isalpha() for character in text):
        return "Description must contain words, not only numbers or symbols."
    return ""


def validate_note(text: str) -> str:
    if not text:
        return "A note is required for this action."
    if len(text) > MAX_NOTE_LENGTH:
        return f"Note must be at most {MAX_NOTE_LENGTH} characters."
    return ""

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