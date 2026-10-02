from datetime import UTC, datetime, timedelta
from pathlib import Path

from cinerocket.domain.models import ChatResponse
from cinerocket.storage.sqlite import SqliteStore


class SQLiteResponseCache(SqliteStore):
    schema = """
    CREATE TABLE IF NOT EXISTS response_cache (
        cache_key TEXT PRIMARY KEY,
        response TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """

    def __init__(self, path: Path, ttl_seconds: int) -> None:
        super().__init__(path)
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, key: str) -> ChatResponse | None:
        if not self._ttl:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT response, created_at FROM response_cache WHERE cache_key = ?", (key,)
            ).fetchone()
        if row is None or datetime.fromisoformat(row[1]) + self._ttl < datetime.now(UTC):
            return None
        return ChatResponse.model_validate_json(row[0])

    def set(self, key: str, response: ChatResponse) -> None:
        if not self._ttl:
            return
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO response_cache (cache_key, response, created_at) VALUES (?, ?, ?)",
                (key, response.model_dump_json(), datetime.now(UTC).isoformat()),
            )
