from dataclasses import dataclass
from html import escape
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from cinerocket.application.charts import chart_for
from cinerocket.domain.models import ChatResponse, QueryResult
from cinerocket.ui.charts import build_figure
from cinerocket.ui.examples import EXAMPLE_QUESTIONS

USER_AVATAR = ":material/person:"
ASSISTANT_AVATAR = ":material/movie:"


@dataclass(frozen=True)
class Turn:
    question: str
    response: ChatResponse | None = None
    error: str | None = None


def render_intro() -> None:
    st.title("Pergunte ao catálogo")
    st.html(
        '<p class="cr-lede">Faça perguntas em português sobre bilheteria, notas, elenco, gêneros, produtoras '
        "e avaliações de 95 mil filmes. Cada resposta vem com a tabela, o SQL executado na camada Gold e as "
        "premissas adotadas.</p>"
    )


def render_empty_state() -> str | None:
    st.html('<p class="cr-section-label">Comece por uma destas</p>')
    starters = [questions[0] for questions in EXAMPLE_QUESTIONS.values()]
    choice = st.pills("Sugestões", starters, label_visibility="collapsed", key="starter")
    return choice if isinstance(choice, str) else None


def render_turn(turn: Turn) -> None:
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(turn.question)
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        if turn.error:
            st.error(turn.error)
        elif turn.response:
            render_response(turn.response)


def render_response(response: ChatResponse) -> None:
    st.markdown(response.answer)
    result = response.result
    figure = response_figure(response)
    tabs = [
        label
        for label, available in (
            ("Gráfico", figure is not None),
            ("Dados", result is not None),
            ("SQL", bool(response.sql)),
            ("Premissas", bool(response.assumptions)),
        )
        if available
    ]
    containers = dict(zip(tabs, st.tabs(tabs), strict=True)) if tabs else {}
    if figure is not None:
        with containers["Gráfico"]:
            st.plotly_chart(figure, config={"displayModeBar": False}, key=f"chart-{id(response)}")
    if result is not None:
        with containers["Dados"]:
            render_result_table(result)
    if response.sql:
        with containers["SQL"]:
            st.code(response.sql, language="sql", wrap_lines=True)
    if response.assumptions:
        with containers["Premissas"]:
            st.markdown("\n".join(f"- {item}" for item in response.assumptions))
    render_meta(response)


def response_figure(response: ChatResponse) -> go.Figure | None:
    result = response.result
    if result is None or not result.rows:
        return None
    spec = chart_for(response.chart, result)
    return build_figure(spec, result) if spec else None


def render_result_table(result: QueryResult) -> None:
    if not result.rows:
        st.info("A consulta não retornou linhas.")
        return
    frame = pd.DataFrame(result.rows, columns=result.columns)
    numeric = frame.select_dtypes("number").columns
    config: dict[str, Any] = {column: st.column_config.NumberColumn(format="localized") for column in numeric}
    st.dataframe(frame, hide_index=True, column_config=config, width="stretch")
    footer = f"{result.row_count} linhas"
    if result.truncated:
        footer += " · resultado limitado"
    left, right = st.columns([3, 1], vertical_alignment="center")
    left.caption(footer)
    right.download_button(
        "Baixar CSV",
        frame.to_csv(index=False).encode("utf-8"),
        file_name="cinerocket.csv",
        mime="text/csv",
        key=f"csv-{id(result)}",
        width="stretch",
    )


def render_meta(response: ChatResponse) -> None:
    if response.cached:
        parts = ["<strong>Resposta em cache</strong>", "nenhuma chamada ao modelo"]
    else:
        tokens = response.usage.input_tokens + response.usage.output_tokens
        parts = [
            f"<strong>{escape(short_model_name(response.model))}</strong>",
            f"{response.usage.requests} chamadas ao modelo",
            f"{tokens:,} tokens".replace(",", "."),
        ]
    if response.result:
        parts.append(f"SQL em {response.result.elapsed_ms:,.0f} ms".replace(",", "."))
    st.html(f'<p class="cr-meta">{" · ".join(parts)}</p>')


def short_model_name(model: str | None) -> str:
    if not model:
        return "modelo"
    return model.split("/")[-1].removesuffix(":free")


def render_examples() -> str | None:
    st.html('<p class="cr-section-label">Perguntas de exemplo</p>')
    for category, questions in EXAMPLE_QUESTIONS.items():
        with st.expander(category):
            for index, question in enumerate(questions):
                if st.button(question, key=f"example-{category}-{index}", width="stretch"):
                    return question
    return None


def render_status(health: dict[str, Any] | None, quota: dict[str, Any] | None) -> None:
    st.html('<p class="cr-section-label">Ambiente</p>')
    if health is None:
        st.warning("API indisponível. Rode `cinerocket serve` e recarregue a página.")
        return
    rows = [
        ("Banco", "conectado" if health.get("database") else "não encontrado"),
        ("Busca semântica", "ativa" if health.get("semantic_index") else "sem índice"),
        ("Modelos", str(len(health.get("models", [])))),
    ]
    daily = (quota or {}).get("free_model_daily_requests") or {}
    if daily.get("remaining") is not None:
        rows.append(("Cota gratuita hoje", f"{daily['remaining']} de {daily.get('limit')}"))
    items = "".join(f"<dt>{escape(label)}</dt><dd>{escape(value)}</dd>" for label, value in rows)
    st.html(f'<dl class="cr-status">{items}</dl>')
