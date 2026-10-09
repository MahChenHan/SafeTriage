"""SafeTriage entry point: coordinates the four managers.

    user    # terminal 1: employees report hazards
    admin   # terminal 2: safety staff review and dispatch

Flow: io_manager -> ai_manager -> logic_manager -> data_manager.
The managers never import each other; this file passes data between them.
"""
import logging
import os
import sys

import ai_manager
import data_manager
import io_manager
import logic_manager

# Gemini API key, linked automatically at startup.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def setup_logging(data_dir: str) -> None:
    """Send logs to a file (never the terminal, which io_manager owns)."""
    try:
        os.makedirs(data_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(data_dir, "safetriage.log"),
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    except OSError:
        logging.disable(logging.CRITICAL)