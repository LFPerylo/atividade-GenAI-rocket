import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from cinerocket.domain.errors import DatabaseNotFoundError

PROGRESS_HANDLER_STEPS = 10_000


class ReadOnlyDatabase:
    def __init__(self, path: Path, timeout_seconds: float) -> None:
        self._path = path
        self._timeout_seconds = timeout_seconds

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.is_file()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        if not self.exists():
            raise DatabaseNotFoundError(f"Banco de dados não encontrado em '{self._path}'.")
        connection = sqlite3.connect(f"{self._path.resolve().as_uri()}?mode=ro", uri=True)
        try:
            connection.execute("PRAGMA query_only = ON")
            deadline = time.monotonic() + self._timeout_seconds
            connection.set_progress_handler(lambda: int(time.monotonic() > deadline), PROGRESS_HANDLER_STEPS)
            yield connection
        finally:
            connection.close()
