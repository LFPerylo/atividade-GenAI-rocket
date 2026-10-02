import sqlite3
from pathlib import Path

import pytest

from cinerocket.database.catalog import SchemaCatalog
from cinerocket.database.connection import ReadOnlyDatabase
from cinerocket.database.executor import QueryExecutor
from cinerocket.guardrails.sql import SqlGuard

SCHEMA = """
CREATE TABLE dim_movies (
    sk_movie_id VARCHAR(64) PRIMARY KEY,
    titulo VARCHAR(500) NOT NULL,
    ano_lancamento INTEGER,
    status_filme VARCHAR(50),
    sinopse VARCHAR(4000)
);
CREATE TABLE fact_movies_performance (
    sk_movie_id VARCHAR(64) PRIMARY KEY REFERENCES dim_movies (sk_movie_id),
    receita_brl NUMERIC(18, 2),
    orcamento_brl NUMERIC(18, 2),
    lucro_brl NUMERIC(18, 2) NOT NULL,
    nota_imdb DOUBLE
);
CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY);
"""

MOVIES = [
    ("m1", "Duna", 2021, "Lançado", "A noble family rules a desert planet.", 2_000.0, 1_000.0, 1_000.0, 8.0),
    ("m2", "Barbie", 2023, "Lançado", "A doll leaves her perfect world.", 7_000.0, 700.0, 6_300.0, 6.9),
    ("m3", "Projeto X", 2027, "Planejado", "A secret project.", None, None, 0.0, None),
]


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    path = tmp_path / "cinerocket.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        connection.executemany(
            "INSERT INTO dim_movies VALUES (?, ?, ?, ?, ?)", [movie[:5] for movie in MOVIES]
        )
        connection.executemany(
            "INSERT INTO fact_movies_performance VALUES (?, ?, ?, ?, ?)",
            [(movie[0], *movie[5:]) for movie in MOVIES],
        )
    return path


@pytest.fixture
def database(database_path: Path) -> ReadOnlyDatabase:
    return ReadOnlyDatabase(database_path, timeout_seconds=5)


@pytest.fixture
def catalog(database: ReadOnlyDatabase) -> SchemaCatalog:
    return SchemaCatalog(database, excluded_tables={"alembic_version"})


@pytest.fixture
def guard(catalog: SchemaCatalog) -> SqlGuard:
    return SqlGuard(catalog.table_names)


@pytest.fixture
def executor(database: ReadOnlyDatabase, guard: SqlGuard) -> QueryExecutor:
    return QueryExecutor(database, guard, max_rows=2)
