from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from cinerocket.domain.models import CellValue, ChatResponse, QueryResult

TABLE_PREVIEW_ROWS = 15


def format_cell(value: CellValue) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    if isinstance(value, int):
        return f"{value:,}".replace(",", ".")
    return value


def result_table(result: QueryResult) -> Table:
    table = Table(show_lines=False, header_style="bold cyan", expand=False)
    for column in result.columns:
        table.add_column(column, overflow="fold")
    for row in result.rows[:TABLE_PREVIEW_ROWS]:
        table.add_row(*(format_cell(value) for value in row))
    hidden = result.row_count - TABLE_PREVIEW_ROWS
    if hidden > 0 or result.truncated:
        table.caption = f"{result.row_count} linhas{' (resultado truncado)' if result.truncated else ''}"
    return table


def render_response(console: Console, response: ChatResponse, *, show_sql: bool = True) -> None:
    body: list[Markdown | Table | Syntax] = [Markdown(response.answer)]
    if response.result and response.result.rows:
        body.append(result_table(response.result))
    if response.assumptions:
        body.append(Markdown("**Premissas**\n" + "\n".join(f"- {item}" for item in response.assumptions)))
    if show_sql and response.sql:
        body.append(Syntax(response.sql, "sql", word_wrap=True, theme="ansi_dark"))
    meta = " · ".join(
        part
        for part in (
            "cache" if response.cached else response.model,
            f"{response.usage.requests} chamadas" if not response.cached else None,
            f"sessão {response.session_id}",
        )
        if part
    )
    console.print(Panel(Group(*body), title="CineRocket Analyst", subtitle=meta, border_style="magenta"))
