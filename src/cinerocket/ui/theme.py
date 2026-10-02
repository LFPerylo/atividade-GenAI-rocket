from pathlib import Path

import streamlit as st

STYLESHEET = Path(__file__).with_name("styles.css")


def apply_theme() -> None:
    st.html(f"<style>{STYLESHEET.read_text(encoding='utf-8')}</style>")
