"""Minimal filelock-compatible module for offline environments."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

__all__ = ["FileLock", "Timeout"]


class Timeout(Exception):
    """Raised when acquiring a lock exceeds the timeout."""


class FileLock:
    def __init__(
        self, lock_file: str | os.PathLike, timeout: float = 10.0, delay: float = 0.1
    ):
        self.lock_file = str(lock_file)
        self.timeout = timeout
        self.delay = delay
        self._handle: Optional[int] = None

    def acquire(self, blocking: bool = True) -> bool:
        start_time = time.time()
        lock_path = Path(self.lock_file)
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        while True:
            try:
                self._handle = os.open(
                    self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                )
                return True
            except FileExistsError:
                if not blocking:
                    return False
                if (time.time() - start_time) >= self.timeout:
                    raise Timeout(f"Timeout waiting for lock: {self.lock_file}")
                time.sleep(self.delay)

    def release(self) -> None:
        if self._handle is not None:
            os.close(self._handle)
            self._handle = None
        try:
            os.remove(self.lock_file)
        except FileNotFoundError:
            pass

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()
