"""Sidebar navigation and report selection."""

from __future__ import annotations

from datetime import datetime

import streamlit as st
from api import fetch_report_list
from config import NAVIGATION_PAGES


def _report_timestamp(meta: dict[str, int | float]) -> str:
    modified = float(meta.get("modified", 0) or 0)
    return datetime.fromtimestamp(modified).strftime("%Y-%m-%d %H:%M")


def _current_job_label(current_job: dict[str, str]) -> str:
    publisher = current_job.get("publisher", "unknown")
    name = current_job.get("name", "unknown")
    version = current_job.get("version", "unknown")
    return f"{publisher}.{name}@{version}"


def _render_dashboard_sidebar() -> str | None:
    reports, report_list_error = fetch_report_list()
    if report_list_error:
        st.error(report_list_error)

    if not reports:
        st.warning("No reports found.")
        return None

    report_map = {report["filename"]: report for report in reports}
    pending_report = st.session_state.get("pending_report")
    report_names = list(report_map.keys())
    if pending_report and pending_report not in report_map:
        report_names = [pending_report, *report_names]

    options = ["(Latest Report)", *report_names]

    if pending_report and pending_report in report_map:
        st.session_state["selected_report"] = pending_report
        st.session_state.pop("pending_report", None)
    elif st.session_state.get("selected_report") not in options:
        st.session_state["selected_report"] = "(Latest Report)"

    selection = st.selectbox(
        "Select Analysis Session",
        options,
        key="selected_report",
    )

    if selection == "(Latest Report)":
        target = "latest"
        meta = reports[0]
    else:
        target = selection
        meta = report_map.get(
            selection,
            {"modified": 0, "size_bytes": 0},
        )

    st.markdown(
        f"""
        <div style="
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            padding: 16px;
            margin-top: 16px;
        ">
            <div style="
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
            ">
                <span style="color: #a1a1aa; font-size: 0.8rem;">Date</span>
                <span style="color: #fff; font-weight: 600; font-size: 0.8rem;">
                    {_report_timestamp(meta)}
                </span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #a1a1aa; font-size: 0.8rem;">Size</span>
                <span style="color: #fff; font-weight: 600; font-size: 0.8rem;">
                    {meta.get("size_bytes", 0) / 1024:.1f} KB
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return target


def _render_simulation_sidebar() -> None:
    current_job = st.session_state.get("last_scan_status")
    if not current_job:
        st.info("No active simulation.")
        return

    st.markdown(
        f"""
        <div style="
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            padding: 16px;
            margin-top: 16px;
        ">
            <div style="
                color: #a1a1aa;
                font-size: 0.78rem;
                margin-bottom: 8px;
            ">Live Sandbox</div>
            <div style="
                color: #fff;
                font-weight: 700;
                font-size: 0.95rem;
                line-height: 1.5;
            ">
                {_current_job_label(current_job)}
            </div>
            <div style="margin-top: 10px; color: #67e8f9; font-size: 0.8rem;">
                Status: {current_job.get("status", "queued").title()}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, str | None]:
    target = None

    with st.sidebar:
        st.markdown(
            """
            <div style="margin-bottom: 20px;">
                <h2 style="margin:0; font-size: 1.4rem;">⚡ ExTrace</h2>
                <div style="
                    font-size: 0.8rem;
                    color: #a1a1aa;
                    letter-spacing: 0.05em;
                ">INTELLIGENCE SUITE</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        page = st.radio(
            "Navigation",
            NAVIGATION_PAGES,
            key="nav_page",
            label_visibility="collapsed",
        )

        st.markdown("---")

        if page == "Dashboard":
            target = _render_dashboard_sidebar()
        elif page == "Simulation":
            _render_simulation_sidebar()

        st.markdown("---")
        if st.button("🔄 System Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown(
            """
            <div style="
                position: fixed;
                bottom: 20px;
                font-size: 0.7rem;
                color: #52525b;
            ">
                v2.1.0 • SYSTEM ONLINE
            </div>
            """,
            unsafe_allow_html=True,
        )

    return page, target
