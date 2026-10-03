import sqlite3
from pathlib import Path

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from cinerocket.config import Settings
from cinerocket.container import Container, build_container
from cinerocket.database.catalog import SchemaCatalog
from cinerocket.database.connection import ReadOnlyDatabase
from cinerocket.database.executor import QueryExecutor
from cinerocket.guardrails.sql import SqlGuard
from cinerocket.llm.factory import ModelChain

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
    return SqlGuard(lambda: catalog.table_names)


@pytest.fixture
def executor(database: ReadOnlyDatabase, guard: SqlGuard) -> QueryExecutor:
    return QueryExecutor(database, guard, max_rows=2)


@pytest.fixture
def settings(database_path: Path, tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        database_path=database_path,
        app_db_path=tmp_path / "app.db",
        index_dir=tmp_path / "index",
        openrouter_api_key=None,
        google_api_key=None,
        few_shot_limit=0,
    )


class ScriptedModel:
    def __init__(self, sql: str) -> None:
        self.sql = sql
        self.calls: list[list[ModelMessage]] = []
        self.model = FunctionModel(self._respond, model_name="scripted")

    def _respond(self, messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        self.calls.append(messages)
        last_parts = messages[-1].parts
        if not any(isinstance(part, ToolReturnPart) and part.tool_name == "run_sql" for part in last_parts):
            return ModelResponse(parts=[ToolCallPart("run_sql", {"sql": self.sql})])
        answer = {
            "answer": "Barbie lidera a receita.",
            "sql": self.sql,
            "assumptions": ["Receita em R$"],
            "chart": {"kind": "bar", "x": "titulo", "y": "receita_brl", "title": "Receita"},
        }
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, answer)])


@pytest.fixture
def scripted_model() -> ScriptedModel:
    return ScriptedModel(
        "SELECT m.titulo, f.receita_brl FROM dim_movies m "
        "JOIN fact_movies_performance f USING (sk_movie_id) "
        "WHERE f.receita_brl > 0 ORDER BY f.receita_brl DESC"
    )


@pytest.fixture
def container(settings: Settings, scripted_model: ScriptedModel) -> Container:
    return build_container(settings, ModelChain(model=scripted_model.model, names=("scripted",)))
