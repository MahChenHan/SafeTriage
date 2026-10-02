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

