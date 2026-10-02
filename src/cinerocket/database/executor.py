import sqlite3
import time

from cinerocket.database.connection import ReadOnlyDatabase
from cinerocket.domain.errors import QueryExecutionError, QueryTimeoutError
from cinerocket.domain.models import CellValue, QueryResult
from cinerocket.guardrails.sql import SqlGuard


def to_cell(value: object) -> CellValue:
    if value is None or isinstance(value, str | int | float):
        return value
    if isinstance(value, bytes):
        return value.hex()
    return str(value)


class QueryExecutor:
    def __init__(self, database: ReadOnlyDatabase, guard: SqlGuard, max_rows: int) -> None:
        self._database = database
        self._guard = guard
        self._max_rows = max_rows

    def execute(self, sql: str) -> QueryResult:
        statement = self._guard.validate(sql)
        started = time.perf_counter()
        try:
            with self._database.connect() as connection:
                cursor = connection.execute(statement)
                columns = [description[0] for description in cursor.description or ()]
                fetched = cursor.fetchmany(self._max_rows + 1)
        except sqlite3.OperationalError as error:
            if "interrupted" in str(error).lower():
                raise QueryTimeoutError(
                    "A consulta excedeu o tempo limite. Simplifique-a ou adicione filtros."
                ) from error
            raise QueryExecutionError(f"Erro ao executar a consulta: {error}") from error
        except sqlite3.Error as error:
            raise QueryExecutionError(f"Erro ao executar a consulta: {error}") from error
        rows = [[to_cell(value) for value in row] for row in fetched[: self._max_rows]]
        return QueryResult(
            sql=statement,
            columns=columns,
            rows=rows,
            truncated=len(fetched) > self._max_rows,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
