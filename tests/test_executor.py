import pytest

from cinerocket.database.executor import QueryExecutor
from cinerocket.domain.errors import QueryExecutionError


def test_caps_rows_and_flags_truncation(executor: QueryExecutor) -> None:
    result = executor.execute("SELECT titulo FROM dim_movies ORDER BY titulo")

    assert result.columns == ["titulo"]
    assert result.rows == [["Barbie"], ["Duna"]]
    assert result.truncated is True


def test_reports_database_errors(executor: QueryExecutor) -> None:
    with pytest.raises(QueryExecutionError, match="no such column"):
        executor.execute("SELECT coluna_inexistente FROM dim_movies")
