"""I/O layer for SafeTriage.

Every print() and input() call in the project lives in this module. It collects
and validates user input (re-prompting on bad data) and formats records for display.
"""
import re
from collections.abc import Callable

LINE = "=" * 70
THIN = "-" * 70
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{2,20}$")
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