from datetime import UTC, datetime

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from cinerocket.domain.models import ChatResponse
from cinerocket.storage.sqlite import SqliteStore


class SQLiteSessionStore(SqliteStore):
    schema = """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        messages BLOB NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS session_turns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        response TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS ix_session_turns_session_id ON session_turns (session_id);
    """

    def load_messages(self, session_id: str) -> list[ModelMessage]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT messages FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        return ModelMessagesTypeAdapter.validate_json(row[0]) if row else []

    def save_turn(self, session_id: str, messages: list[ModelMessage], response: ChatResponse) -> None:
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO sessions (session_id, messages, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT (session_id) DO UPDATE SET messages = excluded.messages, "
                "updated_at = excluded.updated_at",
                (session_id, ModelMessagesTypeAdapter.dump_json(messages), now),
            )
            connection.execute(
                "INSERT INTO session_turns (session_id, response, created_at) VALUES (?, ?, ?)",
                (session_id, response.model_dump_json(), now),
            )

    def transcript(self, session_id: str) -> list[ChatResponse]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT response FROM session_turns WHERE session_id = ? ORDER BY id", (session_id,)
            ).fetchall()
        return [ChatResponse.model_validate_json(row[0]) for row in rows]

    def delete(self, session_id: str) -> bool:
        with self._connect() as connection:
            deleted = connection.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,)).rowcount
            turns = connection.execute(
                "DELETE FROM session_turns WHERE session_id = ?", (session_id,)
            ).rowcount
        return bool(deleted or turns)
