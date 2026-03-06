"""Dashboard page renderer."""

from __future__ import annotations

import time

import streamlit as st
from api import fetch_report
from components import metric_card
from config import DEFAULT_CHART_THEME
from data_processing import prepare_report_context
from views.dashboard_tabs import (
    render_file_tab,
    render_grid_tab,
    render_host_logs_tab,
    render_network_tab,
    render_performance_tab,
    render_raw_tab,
    render_visual_tab,
)


def render_dashboard_page(target: str | None) -> None:
    if not target:
        st.markdown(
            "<div style='text-align: center; margin-top: 20vh; color: #52525b;'>"
            "Select a completed analysis report from the sidebar.</div>",
            unsafe_allow_html=True,
        )
        return

    raw_data, report_error = fetch_report(target)
    if report_error:
        if st.session_state.get("pending_report") == target:
            st.info("Finalizing completed report...")
            time.sleep(2)
            st.rerun()
        st.error(report_error)
        return

    if not raw_data:
        st.error("Failed to load report data.")
        return

    context = prepare_report_context(raw_data)
    chart_theme = st.session_state.get("chart_theme", DEFAULT_CHART_THEME)

    col_header, col_status = st.columns([3, 1])
    with col_header:
        target_extension = raw_data.get("_metadata", {}).get("filename", "Unknown")
        scenarios = context.summary.get("scenarios_run", [])
        scenarios_badges = (
            " ".join(
                f'<span style="background: rgba(139, 92, 246, 0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; margin-right: 4px; border: 1px solid rgba(139, 92, 246, 0.4);">{scenario}</span>'
                for scenario in scenarios
            )
            if scenarios
            else ""
        )
        st.markdown(
            f"""
            <h1 style="font-size: 2.5rem; margin-bottom: 0;">
                Analysis <span class="gradient-text">Dashboard</span>
            </h1>
            <div style="margin-top: 12px; margin-bottom: 12px; display: inline-block; padding: 6px 12px; background: rgba(34, 211, 238, 0.1); border: 1px solid rgba(34, 211, 238, 0.3); border-radius: 8px;">
                <span style="color: #a1a1aa; font-size: 0.9rem;">Target Extension: </span>
                <strong style="color: #22d3ee; font-size: 1.1rem; letter-spacing: 0.02em;">{target_extension}</strong>
            </div>
            """
            + (
                f"""<div style="margin-bottom: 8px;"><span style="color: #a1a1aa; font-size: 0.85rem; margin-right: 8px;">Automations Run:</span>{scenarios_badges}</div>"""
                if scenarios_badges
                else ""
            ),
            unsafe_allow_html=True,
        )

    with col_status:
        st.markdown(
            """
            <div style="
                display: flex;
                align-items: center;
                justify-content: flex-end;
                height: 100%;
                gap: 10px;
            ">
                <span style="color: #10b981; font-weight: 600; font-size: 0.9rem; letter-spacing: 0.05em;">LIVE MONITORING</span>
                <div class="status-dot"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 32px'></div>", unsafe_allow_html=True)

    summary_cards = st.columns(5)
    with summary_cards[0]:
        st.markdown(
            metric_card(
                "⚡", "Total Events", f"{len(context.activations):,}", "#8b5cf6"
            ),
            unsafe_allow_html=True,
        )
    with summary_cards[1]:
        st.markdown(
            metric_card(
                "📦",
                "Extensions",
                str(context.summary.get("unique_extensions", 0)),
                "#06b6d4",
            ),
            unsafe_allow_html=True,
        )
    with summary_cards[2]:
        st.markdown(
            metric_card(
                "🌐",
                "Network Events",
                str(context.network_summary.get("total_events", len(context.network))),
                "#10b981",
            ),
            unsafe_allow_html=True,
        )
    with summary_cards[3]:
        st.markdown(
            metric_card(
                "🛰️",
                "Network Hosts",
                str(
                    context.network_summary.get(
                        "unique_hosts",
                        context.network["host_display"].nunique()
                        if not context.network.empty
                        else 0,
                    )
                ),
                "#f97316",
            ),
            unsafe_allow_html=True,
        )
    with summary_cards[4]:
        duration = context.summary.get("monitoring_duration_s", 0)
        st.markdown(
            metric_card("⏱️", "Duration", f"{duration:.1f}s", "#f59e0b"),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 48px'></div>", unsafe_allow_html=True)

    tabs = st.tabs(
        [
            "📊 Visual Intelligence",
            "🌐 Network Telemetry",
            "🗂️ File I/O Intelligence",
            "⚡ Performance Matrix",
            "💾 Data Grid",
            "🔍 Raw Inspector",
            "📝 Extension Host Logs",
        ]
    )
    with tabs[0]:
        render_visual_tab(context.activations, chart_theme)
    with tabs[1]:
        render_network_tab(context.network, context.network_summary, chart_theme)
    with tabs[2]:
        render_file_tab(context.files, context.file_summary)
    with tabs[3]:
        render_performance_tab(context.activations, context.running_extensions)
    with tabs[4]:
        render_grid_tab(context.activations)
    with tabs[5]:
        render_raw_tab(raw_data)
    with tabs[6]:
        render_host_logs_tab(raw_data)
