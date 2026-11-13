"""DATA MANAGER - data_manager/file_lock.py

Role: Saves and loads incidents (JSON or SQLite), queries and filters them, and handles missing, corrupt or locked files.
Class in this file: FileLock
See README section "Where each manager lives" for the full map.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator


class FileLock:
    """Cross-process lock so two terminals never overwrite each other's records."""

    def __init__(self, path: str) -> None:
        self._lock_path = path + ".lock"

    @contextmanager
    def held(self) -> Iterator[None]:
        os.makedirs(os.path.dirname(self._lock_path) or ".", exist_ok=True)
        with open(self._lock_path, "a+b") as handle:
            if os.name == "nt":
                import msvcrt

                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
