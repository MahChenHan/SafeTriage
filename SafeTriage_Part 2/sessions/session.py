"""SESSIONS (application layer) - sessions/session.py

Role: The user and admin workflows. They call the four managers; they hold no business rules of
their own.
Class in this file: Session
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai_manager.ai_manager import AIManager
from data_manager.data_manager import DataManager
from data_manager.load_result import LoadResult
from errors.storage_error import StorageError
from io_manager.io_manager import IOManager
from logic_manager.logic_manager import LogicManager


class Session(ABC):
    """Shared plumbing for both terminals."""

    def __init__(self, io: IOManager, ai: AIManager, logic: LogicManager, data: DataManager) -> None:
        self._io = io
        self._ai = ai
        self._logic = logic
        self._data = data

    @abstractmethod
    def run(self) -> None:
        """Run the whole terminal session until the person finishes."""

    def _load(self, status: str = "", priority: str = "", show_warnings: bool = True) -> LoadResult:
        """Read incidents; a storage failure is shown to the person and treated as 'nothing loaded'."""
        try:
            result = self._data.find_incidents(status, priority)
        except StorageError as error:
            self._io.show_error(str(error))
            return LoadResult()
        if show_warnings:
            self._io.show_warnings(result.warnings)
        return result
