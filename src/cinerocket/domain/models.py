from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

CellValue = str | int | float | None


class QueryResult(BaseModel):
    sql: str
    columns: list[str]
    rows: list[list[CellValue]]
    truncated: bool = False
    elapsed_ms: float = 0.0

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def records(self) -> list[dict[str, CellValue]]:
        return [dict(zip(self.columns, row, strict=True)) for row in self.rows]

    def preview(self, limit: int) -> dict[str, Any]:
        return {
            "columns": self.columns,
            "rows": self.rows[:limit],
            "row_count": self.row_count,
            "truncated": self.truncated,
        }


class ChartSpec(BaseModel):
    kind: Literal["bar", "horizontal_bar", "line", "scatter"] = Field(
        description=(
            "bar ou horizontal_bar para rankings e categorias, line para séries temporais, "
            "scatter para correlação entre duas métricas"
        )
    )
    x: str = Field(description="Nome exato da coluna do resultado usada no eixo X ou como rótulo")
    y: str = Field(description="Nome exato da coluna numérica do resultado usada no eixo Y (ou valores)")
    title: str = Field(description="Título curto do gráfico em português")


class AgentAnswer(BaseModel):
    answer: str = Field(
        description=(
            "Resposta final em português, clara para um usuário de negócio, com os números relevantes "
            "formatados (R$ com separador de milhar) e sem expor detalhes técnicos de SQL"
        )
    )
    sql: str | None = Field(
        default=None,
        description="Consulta SQL final, já testada com run_sql, cujo resultado sustenta a resposta",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Premissas e interpretações adotadas para responder (filtros, critérios, desempates)",
    )
    chart: ChartSpec | None = Field(
        default=None,
        description="Sugestão de gráfico quando o resultado tiver uma dimensão e uma métrica comparáveis",
    )
    out_of_scope: bool = Field(
        default=False,
        description="True quando a pergunta não pode ser respondida com o catálogo de filmes",
    )


class MovieMatch(BaseModel):
    movie_id: str
    title: str
    release_year: int | None
    score: float


class UsageStats(BaseModel):
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


class ChatResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    sql: str | None = None
    result: QueryResult | None = None
    chart: ChartSpec | None = None
    assumptions: list[str] = Field(default_factory=list)
    out_of_scope: bool = False
    cached: bool = False
    model: str | None = None
    usage: UsageStats = Field(default_factory=UsageStats)
    created_at: datetime


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool


class ForeignKeyInfo(BaseModel):
    column: str
    references_table: str
    references_column: str


class TableInfo(BaseModel):
    name: str
    columns: list[ColumnInfo]
    foreign_keys: list[ForeignKeyInfo] = Field(default_factory=list)
    row_count: int

    @property
    def column_names(self) -> list[str]:
        return [column.name for column in self.columns]
