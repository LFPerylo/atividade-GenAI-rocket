from datetime import date

import pytest
from pydantic_ai import ModelRetry

from cinerocket.agent.deps import AgentDeps
from cinerocket.agent.validation import validate_answer
from cinerocket.database.catalog import SchemaCatalog
from cinerocket.database.executor import QueryExecutor
from cinerocket.domain.models import AgentAnswer

SQL = "SELECT titulo FROM dim_movies"


@pytest.fixture
def deps(catalog: SchemaCatalog, executor: QueryExecutor) -> AgentDeps:
    return AgentDeps(
        catalog=catalog,
        executor=executor,
        semantic=None,
        today=date(2026, 10, 2),
        preview_rows=5,
        semantic_limit=5,
    )


@pytest.mark.parametrize(
    "answer",
    [
        AgentAnswer(answer="  ", sql=SQL),
        AgentAnswer(answer="Resposta", sql=None),
        AgentAnswer(answer="Resposta", sql=SQL),
    ],
)
def test_rejects_empty_unsupported_or_untested_answers(deps: AgentDeps, answer: AgentAnswer) -> None:
    with pytest.raises(ModelRetry):
        validate_answer(deps, answer)


def test_rejects_out_of_scope_after_querying_the_catalog(deps: AgentDeps) -> None:
    deps.execute(SQL)

    with pytest.raises(ModelRetry):
        validate_answer(deps, AgentAnswer(answer="Não sei", out_of_scope=True))


def test_accepts_tested_answer_and_normalizes_escaped_newlines(deps: AgentDeps) -> None:
    deps.execute(SQL)

    validated = validate_answer(deps, AgentAnswer(answer="Linha 1\\nLinha 2", sql=SQL))

    assert validated.answer == "Linha 1\nLinha 2"
