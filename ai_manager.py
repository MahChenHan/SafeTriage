"""AI layer for SafeTriage.

Builds the prompt, calls the Gemini API, and validates the JSON reply.
There is NO domain logic here: this module never decides priority or routing.
"""
import os

DEFAULT_MODEL = "gemini-3.8-flash"


def get_model_name() -> str:
    """Model name comes from GEMINI_MODEL, falling back to the default."""
    return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)