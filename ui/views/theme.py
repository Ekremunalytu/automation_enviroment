"""Theme page renderer."""

from __future__ import annotations

import streamlit as st
from components import render_page_hero, render_spacer
from config import DEFAULT_CHART_THEME, THEME_OPTIONS


def render_theme_page() -> None:
    render_page_hero(
        "Visual",
        "Theme",
        "Customize the look and feel of your analysis dashboard.",
    )
    render_spacer()

    selected_theme = st.select_slider(
        "Chart Color Palette",
        options=THEME_OPTIONS,
        value=st.session_state.get("chart_theme", DEFAULT_CHART_THEME),
    )
    if selected_theme != st.session_state.get("chart_theme"):
        st.session_state["chart_theme"] = selected_theme
        st.rerun()

    st.info("Additional theme settings will go here in the future.")
