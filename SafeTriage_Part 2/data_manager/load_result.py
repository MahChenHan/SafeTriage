"""DATA MANAGER - data_manager/load_result.py

Role: Saves and loads incidents (JSON or SQLite), queries and filters them, and handles missing, corrupt or locked files.
Class in this file: LoadResult
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.incident import Incident


@dataclass(frozen=True)
class LoadResult:
    """Usable incidents plus any warnings produced while loading them."""

    incidents: list[Incident] = field(default_factory=list)
    warnings: tuple[str, ...] = ()
