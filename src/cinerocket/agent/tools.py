from typing import Any

from pydantic_ai import ModelRetry, RunContext
from pydantic_ai.tools import ToolDefinition

from cinerocket.agent.deps import AgentDeps
from cinerocket.domain.errors import QueryExecutionError, SemanticIndexUnavailableError, UnsafeQueryError
from cinerocket.domain.models import CellValue


def describe_table(ctx: RunContext[AgentDeps], table_name: str) -> dict[str, Any]:
    """Mostra colunas, chaves estrangeiras, total de linhas e 3 linhas de exemplo de uma tabela.

    Args:
        table_name: nome exato da tabela do schema.
    """
    try:
        table = ctx.deps.catalog.resolve_table(table_name)
        columns, rows = ctx.deps.catalog.sample_rows(table.name)
    except QueryExecutionError as error:
        raise ModelRetry(str(error)) from error
    return {"table": table.model_dump(), "sample": {"columns": columns, "rows": rows}}


def distinct_values(
    ctx: RunContext[AgentDeps], table_name: str, column_name: str, limit: int = 20
) -> list[CellValue]:
    """Lista os valores mais frequentes de uma coluna, para confirmar filtros textuais antes de usá-los.

    Args:
        table_name: nome exato da tabela.
        column_name: nome exato da coluna.
        limit: quantidade máxima de valores (até 50).
    """
    try:
        return ctx.deps.catalog.distinct_values(table_name, column_name, min(max(limit, 1), 50))
    except QueryExecutionError as error:
        raise ModelRetry(str(error)) from error


def run_sql(ctx: RunContext[AgentDeps], sql: str) -> dict[str, Any]:
    """Executa uma consulta SQL de leitura (SQLite) e retorna colunas e as primeiras linhas do resultado.

    Use para testar e validar a consulta antes de responder. Erros retornam a mensagem do banco para correção.

    Args:
        sql: consulta SELECT ou WITH única.
    """
    try:
        result = ctx.deps.execute(sql)
    except (UnsafeQueryError, QueryExecutionError) as error:
        raise ModelRetry(f"{error} Corrija a consulta e tente novamente.") from error
    return result.preview(ctx.deps.preview_rows)


def search_synopses(ctx: RunContext[AgentDeps], query: str) -> list[dict[str, Any]]:
    """Busca semântica nas sinopses: encontra filmes cujo enredo é parecido com a descrição informada.

    Retorna movie_id (use em sk_movie_id no SQL), título, ano e score de similaridade (0 a 1).

    Args:
        query: tema ou descrição do enredo, em qualquer idioma (ex.: "viagem no tempo", "heist in Paris").
    """
    if ctx.deps.semantic is None:
        raise ModelRetry("A busca semântica não está disponível. Responda usando apenas SQL.")
    try:
        matches = ctx.deps.semantic.search(query, ctx.deps.semantic_limit)
    except SemanticIndexUnavailableError as error:
        raise ModelRetry(f"{error} Responda usando apenas SQL.") from error
    return [match.model_dump() for match in matches]


async def only_with_semantic_index(
    ctx: RunContext[AgentDeps], definition: ToolDefinition
) -> ToolDefinition | None:
    semantic = ctx.deps.semantic
    return definition if semantic is not None and semantic.is_available() else None
