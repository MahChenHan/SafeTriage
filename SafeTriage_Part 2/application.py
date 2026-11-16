"""APPLICATION (composition root) - application.py

Role: Creates the four managers once and hands them to a session.
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import logging
import os

from ai_manager.ai_manager import AIManager
from ai_manager.ai_provider import AIProvider
from ai_manager.fallback_ai_provider import FallbackAIProvider
from ai_manager.gemini_provider import GeminiProvider
from ai_manager.groq_provider import GroqProvider
from constants import REQUEST_TIMEOUT_SECONDS, TIMEOUT_MARGIN_SECONDS
from data_manager.data_manager import DataManager
from data_manager.repository_factory import RepositoryFactory
from errors.storage_error import StorageError
from io_manager.io_manager import IOManager
from logic_manager.logic_manager import LogicManager
from sessions.admin_session import AdminSession
from sessions.session import Session
from sessions.user_session import UserSession


class Application:
    """Composition root: creates the managers once and hands them to a session."""

    SESSIONS: dict[str, type[Session]] = {"user": UserSession, "admin": AdminSession}

    def __init__(self, io: IOManager, ai: AIManager, logic: LogicManager, data: DataManager) -> None:
        # Aggregation: the application holds the managers, which exist independently of it.
        self._io = io
        self._ai = ai
        self._logic = logic
        self._data = data

    # --------------------------------------------------------------- startup
    @staticmethod
    def _load_setting(name: str) -> str:
        """A setting from an untracked secrets_local.py (never committed), else from the environment.

        Docker passes settings through --env-file. A local "python main.py" run has no .env loading,
        so secrets_local.py is how the keys reach the program there.
        """
        try:
            import secrets_local  # type: ignore[import-not-found]
        except ImportError:
            return os.environ.get(name, "")
        return str(getattr(secrets_local, name, "") or os.environ.get(name, ""))

    @classmethod
    def _load_api_key(cls) -> str:
        return cls._load_setting("GEMINI_API_KEY")

    @staticmethod
    def _configure_logging(data_dir: str) -> None:
        """Send logs to a file (never the terminal, which IOManager owns)."""
        try:
            os.makedirs(data_dir, exist_ok=True)
            logging.basicConfig(
                filename=os.path.join(data_dir, "safetriage.log"),
                level=logging.INFO,
                format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            )
        except OSError:
            logging.disable(logging.CRITICAL)

    @classmethod
    def _ai_providers(cls) -> list[AIProvider]:
        """Primary: Gemini. Backup (optional): Groq, added only when GROQ_API_KEY is set."""
        providers: list[AIProvider] = [GeminiProvider(cls._load_api_key() or None)]
        groq_key = cls._load_setting("GROQ_API_KEY")
        if groq_key:
            providers.append(GroqProvider(api_key=groq_key, model=cls._load_setting("GROQ_MODEL") or None))
        return providers

    @classmethod
    def _build_ai_manager(cls) -> AIManager:
        """One provider is used directly. Two or more are wrapped in a fallback chain."""
        providers = cls._ai_providers()
        if len(providers) == 1:
            return AIManager(providers[0])
        # Each provider gets its own time limit, so a hung Gemini call still leaves time for Groq.
        # The manager's own limit must then cover the whole chain.
        chain = FallbackAIProvider(providers, timeout_seconds=REQUEST_TIMEOUT_SECONDS)
        chain_limit = (chain.total_timeout or REQUEST_TIMEOUT_SECONDS) + TIMEOUT_MARGIN_SECONDS
        return AIManager(chain, timeout_seconds=chain_limit)

    @classmethod
    def from_environment(cls) -> Application:
        io = IOManager()
        cls._configure_logging(os.environ.get("DATA_DIR", "data"))
        try:
            repository = RepositoryFactory.from_environment()
        except StorageError as error:
            io.show_error(str(error))
            raise SystemExit(1) from error
        return cls(io, cls._build_ai_manager(), LogicManager(), DataManager(repository))

    # ------------------------------------------------------------------- run
    def run(self, arguments: list[str]) -> int:
        try:
            mode = arguments[0] if arguments else self._io.prompt_mode()
        except (KeyboardInterrupt, EOFError):
            return 0
        session_class = self.SESSIONS.get(mode)
        if session_class is None:
            self._io.show_usage()
            return 2
        session = session_class(self._io, self._ai, self._logic, self._data)
        try:
            session.run()          # polymorphic call: user or admin workflow
        except (KeyboardInterrupt, EOFError):
            self._io.show_message("\nSession ended.")
        return 0
