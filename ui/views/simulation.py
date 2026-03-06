"""Simulation page renderer."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from components import metric_card, render_page_hero, render_spacer
from data_processing import (
    build_file_log,
    build_network_log,
    process_file_data,
    process_network_data,
)
from state import load_scan_report, sync_active_scan_job

_FRAGMENT_DECORATOR = getattr(
    st, "fragment", getattr(st, "experimental_fragment", None)
)


def _auto_refresh_fragment(run_every: int | float | str | None):
    if _FRAGMENT_DECORATOR is None:
        return lambda func: func
    return _FRAGMENT_DECORATOR(run_every=run_every)


def render_scan_status(scan_job: dict) -> None:
    step_titles = {
        "reset_sandbox": "Resetting sandbox state",
        "install_extension": "Installing extension in sandbox",
        "build_triggers": "Resolving trigger coverage",
        "run_monitoring": "Running Playwright automation",
        "finalize_report": "Collecting report output",
    }
    state_map = {
        "queued": "running",
        "running": "running",
        "completed": "complete",
        "failed": "error",
    }
    extension_id = (
        f"{scan_job.get('publisher', 'unknown')}.{scan_job.get('name', 'unknown')}"
        f"@{scan_job.get('version', 'unknown')}"
    )

    with st.status(
        f"Sandbox analysis — {extension_id}",
        state=state_map.get(scan_job.get("status", "queued"), "running"),
        expanded=True,
    ):
        st.caption(scan_job.get("message", "Waiting for sandbox analysis status."))
        total_steps = max(len(scan_job.get("steps", [])), 1)
        for index, step in enumerate(scan_job.get("steps", []), start=1):
            title = step_titles.get(step.get("name", ""), step.get("name", "Step"))
            status = step.get("status", "pending")
            prefix = {
                "completed": "✓",
                "failed": "✕",
                "running": "•",
                "pending": "…",
                "skipped": "○",
            }.get(status, "…")
            st.write(f"**{index}/{total_steps}** — {prefix} {title}")
            st.caption(step.get("message", ""))

        if scan_job.get("error_detail"):
            st.error(scan_job["error_detail"])
        elif scan_job.get("status") == "running" and scan_job.get("report_path"):
            st.info(f"Live report is updating: `{scan_job['report_path']}`")
        elif scan_job.get("report_path"):
            st.success(f"Report ready: `{scan_job['report_path']}`")

        if scan_job.get("install_output") or scan_job.get("automation_output"):
            with st.expander("Execution Logs", expanded=False):
                col_install, col_auto = st.columns(2)
                with col_install:
                    st.caption("Install Output")
                    st.code(
                        scan_job.get("install_output") or "(no output)", language="text"
                    )
                with col_auto:
                    st.caption("Automation Output")
                    st.code(
                        scan_job.get("automation_output") or "(no output)",
                        language="text",
                    )


def get_active_scenario_name(report: dict) -> str | None:
    traces = report.get("scenario_traces", [])
    if not isinstance(traces, list):
        return None

    for trace in reversed(traces):
        if trace.get("status") == "running":
            return trace.get("name")
    return None


def render_simulation_page(
    scan_job: dict | None,
    live_report: dict | None,
    sync_error: str | None = None,
    report_error: str | None = None,
) -> None:
    render_page_hero(
        "Live",
        "Simulation",
        "Monitor sandbox execution, active automations, and incoming telemetry in real time.",
    )
    render_spacer()

    if sync_error:
        st.warning(sync_error)

    if not scan_job:
        st.info("No active simulation. Start an analysis from Marketplace.")
        return

    extension_id = (
        f"{scan_job.get('publisher', 'unknown')}.{scan_job.get('name', 'unknown')}"
        f"@{scan_job.get('version', 'unknown')}"
    )
    active_scenario = get_active_scenario_name(live_report or {})
    summary = (live_report or {}).get("summary", {})
    network_summary = (live_report or {}).get("network_summary", {})
    file_summary = (live_report or {}).get("file_summary", {})

    hero_left, hero_right = st.columns([3, 1])
    with hero_left:
        scenario_label = active_scenario or "Waiting for scenario telemetry"
        st.markdown(
            f"""
            <div class="glass-card" style="min-height: 150px;">
                <div class="kpi-label">Sandbox Target</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #f4f4f5; margin: 12px 0 18px 0;">{extension_id}</div>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    <div style="padding: 8px 12px; border-radius: 999px; background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.28); color: #6ee7b7; font-size: 0.85rem;">
                        Active Automation: <strong>{scenario_label}</strong>
                    </div>
                    <div style="padding: 8px 12px; border-radius: 999px; background: rgba(6,182,212,0.12); border: 1px solid rgba(6,182,212,0.28); color: #67e8f9; font-size: 0.85rem;">
                        Status: <strong>{scan_job.get('status', 'queued').title()}</strong>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with hero_right:
        st.markdown(
            metric_card(
                "🧪",
                "Telemetry Events",
                str(
                    summary.get("total_activated", 0)
                    + network_summary.get("total_events", 0)
                    + file_summary.get("total_events", 0)
                ),
                "#8b5cf6",
            ),
            unsafe_allow_html=True,
        )

    render_spacer()
    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        st.markdown(
            metric_card(
                "⚡", "Activations", str(summary.get("total_activated", 0)), "#8b5cf6"
            ),
            unsafe_allow_html=True,
        )
    with stat2:
        st.markdown(
            metric_card(
                "🌐", "Network", str(network_summary.get("total_events", 0)), "#10b981"
            ),
            unsafe_allow_html=True,
        )
    with stat3:
        st.markdown(
            metric_card(
                "🗂️", "File I/O", str(file_summary.get("total_events", 0)), "#22d3ee"
            ),
            unsafe_allow_html=True,
        )
    with stat4:
        st.markdown(
            metric_card(
                "🛡️",
                "Sensitive Hits",
                str(file_summary.get("sensitive_events", 0)),
                "#f43f5e",
            ),
            unsafe_allow_html=True,
        )

    render_spacer()
    render_scan_status(scan_job)

    if report_error and scan_job.get("status") not in {"completed", "failed"}:
        st.info("Preparing live simulation report...")
    elif report_error:
        st.warning(report_error)

    sim_tabs = st.tabs(["🔴 Live Pulse", "🌐 Network Stream", "🗂️ File Stream"])

    with sim_tabs[0]:
        if live_report:
            traces = pd.DataFrame(live_report.get("scenario_traces", []))
            if traces.empty:
                st.info("Scenario timeline has not started streaming yet.")
            else:
                traces["status_label"] = traces["status"].fillna("running").str.title()
                st.dataframe(
                    traces[["name", "status_label", "started_at", "ended_at"]],
                    column_config={
                        "name": st.column_config.TextColumn("Automation"),
                        "status_label": st.column_config.TextColumn("Status"),
                        "started_at": st.column_config.NumberColumn("Started At"),
                        "ended_at": st.column_config.NumberColumn("Ended At"),
                    },
                    hide_index=True,
                    height=240,
                )
        else:
            st.info("Waiting for live report telemetry...")

    with sim_tabs[1]:
        network_df = process_network_data(live_report or {})
        if network_df.empty:
            st.info("No network telemetry yet.")
        else:
            with st.container(height=320):
                st.code(build_network_log(network_df), language="log")

    with sim_tabs[2]:
        file_df = process_file_data(live_report or {})
        if file_df.empty:
            st.info("No file telemetry yet.")
        else:
            with st.container(height=320):
                st.code(build_file_log(file_df), language="log")

    if st.button("Clear simulation state", key="clear_scan_state"):
        st.session_state.pop("last_scan_status", None)
        st.session_state.pop("active_scan_job_id", None)
        st.session_state.pop("pending_report", None)
        st.session_state["pending_nav_page"] = "Dashboard"
        st.rerun()


@_auto_refresh_fragment(run_every=2)
def render_live_simulation_fragment() -> None:
    current_scan_job, scan_finished, sync_error = sync_active_scan_job()
    live_report, report_error = load_scan_report(current_scan_job)

    if (
        _FRAGMENT_DECORATOR is None
        and current_scan_job
        and current_scan_job.get("status") == "running"
    ):
        st.caption(
            "Automatic live refresh requires Streamlit fragment support. "
            "Use System Refresh while the analysis is running."
        )

    render_simulation_page(current_scan_job, live_report, sync_error, report_error)

    if scan_finished:
        st.rerun()
