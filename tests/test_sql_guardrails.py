import pytest

from cinerocket.domain.errors import UnsafeQueryError
from cinerocket.guardrails.sql import SqlGuard


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM dim_movies",
        "UPDATE dim_movies SET titulo = 'x'",
        "INSERT INTO dim_movies (sk_movie_id, titulo) VALUES ('x', 'y')",
        "DROP TABLE dim_movies",
        "CREATE TABLE x (id INTEGER)",
        "PRAGMA table_info(dim_movies)",
        "ATTACH DATABASE 'other.db' AS other",
        "VACUUM",
        "SELECT 1; DROP TABLE dim_movies",
        "SELECT * FROM sqlite_master",
        "SELECT * FROM alembic_version",
        "SELECT * FROM pragma_table_info('dim_movies')",
        "SELECT load_extension('evil')",
        "SELEC titulo FROM dim_movies",
        "   ",
    ],
)
def test_rejects_unsafe_or_invalid_sql(guard: SqlGuard, sql: str) -> None:
    with pytest.raises(UnsafeQueryError):
        guard.validate(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT titulo FROM dim_movies;",
        "WITH top AS (SELECT sk_movie_id FROM fact_movies_performance) SELECT * FROM top",
        "SELECT m.titulo FROM dim_movies m JOIN fact_movies_performance f USING (sk_movie_id)",
        "SELECT titulo FROM dim_movies UNION SELECT titulo FROM dim_movies",
    ],
)
def test_accepts_read_only_queries(guard: SqlGuard, sql: str) -> None:
    assert guard.validate(sql) == sql.rstrip(";")
