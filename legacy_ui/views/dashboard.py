"""Dashboard page renderer."""

from __future__ import annotations

import time

import streamlit as st
from api import fetch_report
from config import DEFAULT_CHART_THEME
from data_processing import prepare_report_context
from views.dashboard_tabs import (
    render_dashboard_focus_bar,
    render_evidence_timeline_tab,
    render_overview_tab,
    render_provenance_tab,
    render_rule_workbench_tab,
)


def render_dashboard_page(target: str | None) -> None:
    if not target:
        st.markdown(
            "<div style='text-align: center; margin-top: 20vh; color: #71717a;'>"
            "Select a completed analysis report from the sidebar.</div>",
            unsafe_allow_html=True,
        )
        return

    raw_data, report_error = fetch_report(target)
    if report_error:
        if st.session_state.get("pending_report") == target:
            st.info("Finalizing completed report…")
            time.sleep(2)
            st.rerun()
        st.error(report_error)
        return

    if not raw_data:
        st.error("Failed to load report data.")
        return

    context = prepare_report_context(raw_data)
    chart_theme = st.session_state.get("chart_theme", DEFAULT_CHART_THEME)
    metadata = raw_data.get("_metadata", {})
    target_extension = metadata.get("filename", "Unknown report")
    scenarios = context.summary.get("scenarios_run", []) or []

    st.markdown(
        f"""
        <div class="hero-panel">
            <div>
                <div class="eyebrow">Analyst Console</div>
                <h1>Evidence-Centric Investigation</h1>
                <p>Single-run provenance, collector attribution and rule drafting for extension telemetry.</p>
            </div>
            <div class="hero-meta">
                <div class="hero-chip"><span>Report</span><strong>{target_extension}</strong></div>
                <div class="hero-chip"><span>Events</span><strong>{len(context.evidence):,}</strong></div>
                <div class="hero-chip"><span>Scenarios</span><strong>{len(scenarios)}</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_dashboard_focus_bar(context, key_prefix="dashboard")

    tabs = st.tabs(
        [
            "Overview",
            "Evidence Timeline",
            "Provenance",
            "Rule Workbench",
        ]
    )
    with tabs[0]:
        render_overview_tab(context, chart_theme)
        if raw_data.get("extension_host_output"):
            with st.expander("Extension Host Output", expanded=False):
                st.caption(
                    f"{raw_data.get('extension_host_output_lines', 0)} total lines "
                    "(showing up to last 500)"
                )
                with st.container(height=360):
                    st.code(raw_data["extension_host_output"], language="log")
    with tabs[1]:
        render_evidence_timeline_tab(context, chart_theme, key_prefix="dashboard")
    with tabs[2]:
        render_provenance_tab(context, key_prefix="dashboard")
    with tabs[3]:
        render_rule_workbench_tab(context, key_prefix="dashboard")
