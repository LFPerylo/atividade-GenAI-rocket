from contextlib import suppress
from typing import Any

import streamlit as st

from cinerocket.config import get_settings
from cinerocket.ui.client import ApiError, CineRocketClient
from cinerocket.ui.components import (
    Turn,
    render_empty_state,
    render_examples,
    render_intro,
    render_status,
    render_turn,
)
from cinerocket.ui.theme import apply_theme

SESSION_PARAM = "sessao"


@st.cache_resource
def get_client() -> CineRocketClient:
    return CineRocketClient(get_settings().api_url)


@st.cache_data(ttl=60, show_spinner=False)
def load_health() -> dict[str, Any] | None:
    try:
        return get_client().health()
    except ApiError:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def load_quota() -> dict[str, Any] | None:
    try:
        return get_client().quota()
    except ApiError:
        return None


def init_state() -> None:
    if "turns" in st.session_state:
        return
    st.session_state.turns = []
    st.session_state.session_id = st.query_params.get(SESSION_PARAM)
    if st.session_state.session_id:
        try:
            history = get_client().transcript(st.session_state.session_id)
            st.session_state.turns = [Turn(question=item.question, response=item) for item in history]
        except ApiError:
            st.session_state.session_id = None
            st.query_params.clear()


def new_conversation() -> None:
    session_id = st.session_state.get("session_id")
    if session_id:
        with suppress(ApiError):
            get_client().reset(session_id)
    st.session_state.turns = []
    st.session_state.session_id = None
    st.session_state.pop("starter", None)
    st.query_params.clear()


def ask(question: str) -> None:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"), st.spinner("Consultando a camada Gold…"):
        try:
            response = get_client().ask(question, st.session_state.session_id)
        except ApiError as error:
            st.session_state.turns.append(Turn(question=question, error=str(error)))
        else:
            st.session_state.session_id = response.session_id
            st.query_params[SESSION_PARAM] = response.session_id
            st.session_state.turns.append(Turn(question=question, response=response))
    st.rerun()


def sidebar() -> str | None:
    with st.sidebar:
        st.header("CineRocket Analytics")
        st.caption("Text-to-SQL sobre a camada Gold da CineData")
        st.button(
            "Nova conversa",
            on_click=new_conversation,
            type="primary",
            width="stretch",
            disabled=not st.session_state.turns,
        )
        chosen = render_examples()
        render_status(load_health(), load_quota())
        return chosen


def main() -> None:
    st.set_page_config(page_title="CineRocket Analytics", page_icon=":material/movie:", layout="centered")
    apply_theme()
    init_state()
    chosen = sidebar()
    render_intro()
    for turn in st.session_state.turns:
        render_turn(turn)
    typed = st.chat_input("Pergunte sobre filmes, bilheteria, notas, elenco…", max_chars=1000)
    starters = st.empty()
    if not st.session_state.turns and not typed:
        with starters.container():
            chosen = render_empty_state() or chosen
    question = typed or chosen
    if question:
        starters.empty()
        ask(question)


main()
