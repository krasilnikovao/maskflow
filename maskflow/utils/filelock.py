"""Простой кроссплатформенный файловый lock.

Используется для синхронизации записи общих словарей (entity cache,
reversible mapping) между процессами в ProcessPoolExecutor.
"""

import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from types import TracebackType
from typing import IO

# Windows msvcrt.locking требует явного числа байт для блокировки.
# Значение 1 байт исторически использовалось как символическое, но создаёт
# риск: два процесса могут одновременно получить блокировку разных байт.
# 64 KB — достаточно, чтобы гарантированно перекрыть любой реальный lock-файл.
_WIN_LOCK_SIZE = 64 * 1024


class FileLock:
    def __init__(self, path: Path, timeout: float = 30.0, poll_interval: float = 0.05) -> None:
        self.path = path
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._handle: IO[bytes] | None = None

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.release()

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout

        while True:
            try:
                self._handle = self.path.open("a+b")
                _do_lock(self._handle)
                return
            except (OSError, BlockingIOError) as error:
                if self._handle is not None:
                    self._handle.close()
                    self._handle = None
                if time.monotonic() > deadline:
                    raise TimeoutError(
                        f"Could not acquire file lock: {self.path}"
                    ) from error
                time.sleep(self.poll_interval)

    def release(self) -> None:
        if self._handle is None:
            return
        try:
            _do_unlock(self._handle)
        finally:
            self._handle.close()
            self._handle = None


if sys.platform == "win32":
    import msvcrt

    def _do_lock(handle: IO[bytes]) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, _WIN_LOCK_SIZE)

    def _do_unlock(handle: IO[bytes]) -> None:
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, _WIN_LOCK_SIZE)
        except OSError:
            pass
else:
    import fcntl

    def _do_lock(handle: IO[bytes]) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _do_unlock(handle: IO[bytes]) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def file_lock(path: Path, timeout: float = 30.0) -> Generator[None, None, None]:
    lock = FileLock(path, timeout=timeout)
    lock.acquire()
    try:
        yield
    finally:
        lock.release()
