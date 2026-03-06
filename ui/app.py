"""ExTrace Intelligence Suite Streamlit entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import DEFAULT_CHART_THEME  # noqa: E402
from navigation import render_sidebar  # noqa: E402
from state import apply_pending_navigation, process_pending_scan_request  # noqa: E402
from styles import apply_global_styles, configure_page  # noqa: E402
from views.dashboard import render_dashboard_page  # noqa: E402
from views.marketplace import render_marketplace_page  # noqa: E402
from views.simulation import render_live_simulation_fragment  # noqa: E402
from views.theme import render_theme_page  # noqa: E402

configure_page()
apply_global_styles()

st.session_state.setdefault("chart_theme", DEFAULT_CHART_THEME)
apply_pending_navigation()

page, target = render_sidebar()
process_pending_scan_request()

if page == "Simulation":
    render_live_simulation_fragment()
    st.stop()

if page == "Marketplace":
    render_marketplace_page()
    st.stop()

if page == "Theme":
    render_theme_page()
    st.stop()

render_dashboard_page(target)
