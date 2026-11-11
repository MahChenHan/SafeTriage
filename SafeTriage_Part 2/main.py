"""ENTRY POINT - main.py

Role: Run with: python main.py user   or   python main.py admin
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import sys

from application import Application


if __name__ == "__main__":
    sys.exit(Application.from_environment().run(sys.argv[1:]))
