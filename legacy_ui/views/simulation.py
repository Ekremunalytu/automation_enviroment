"""Simulation page renderer."""

from __future__ import annotations

import streamlit as st
from components import (
    metric_card,
    render_page_hero,
    render_section_intro,
    render_spacer,
)
from data_processing import prepare_report_context
from state import load_scan_report, sync_active_scan_job
from views.dashboard_tabs import (
    render_dashboard_focus_bar,
    render_evidence_timeline_tab,
    render_provenance_tab,
    render_rule_workbench_tab,
)

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


def render_simulation_page(
    scan_job: dict | None,
    live_report: dict | None,
    sync_error: str | None = None,
    report_error: str | None = None,
) -> None:
    render_page_hero(
        "Live",
        "Simulation",
        "Monitor sandbox execution, unified evidence telemetry and "
        "provenance while a run is active.",
    )
    render_spacer()

    if sync_error:
        st.warning(sync_error)

    if not scan_job:
        st.info("No active simulation. Start an analysis from Marketplace.")
        return

    context = prepare_report_context(live_report or {})
    extension_id = (
        f"{scan_job.get('publisher', 'unknown')}.{scan_job.get('name', 'unknown')}"
        f"@{scan_job.get('version', 'unknown')}"
    )

    hero_left, hero_right = st.columns([2.5, 1], gap="large")
    with hero_left:
        st.markdown(
            f"""
            <div class="hero-panel compact">
                <div>
                    <div class="eyebrow">Sandbox Target</div>
                    <h1>{extension_id}</h1>
                    <p>Status and live evidence update from the same report stream.</p>
                </div>
                <div class="hero-meta">
                    <div class="hero-chip">
                        <span>Status</span>
                        <strong>{scan_job.get("status", "queued").title()}</strong>
                    </div>
                    <div class="hero-chip">
                        <span>Report</span>
                        <strong>{scan_job.get("report_path") or "pending"}</strong>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with hero_right:
        st.markdown(
            metric_card(
                "Live Evidence",
                str(len(context.evidence)),
                "#8b5cf6",
            ),
            unsafe_allow_html=True,
        )

    render_spacer()
    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        st.markdown(
            metric_card(
                "Activations", str(context.summary.get("total_activated", 0)), "#8b5cf6"
            ),
            unsafe_allow_html=True,
        )
    with stat2:
        st.markdown(
            metric_card(
                "Network",
                str(context.network_summary.get("total_events", 0)),
                "#10b981",
            ),
            unsafe_allow_html=True,
        )
    with stat3:
        st.markdown(
            metric_card(
                "File I/O", str(context.file_summary.get("total_events", 0)), "#22d3ee"
            ),
            unsafe_allow_html=True,
        )
    with stat4:
        st.markdown(
            metric_card(
                "Sensitive",
                str(context.file_summary.get("sensitive_events", 0)),
                "#f43f5e",
            ),
            unsafe_allow_html=True,
        )

    render_spacer()
    render_scan_status(scan_job)

    if report_error and scan_job.get("status") not in {"completed", "failed"}:
        st.info("Preparing live simulation report…")
    elif report_error:
        st.warning(report_error)

    render_dashboard_focus_bar(context, key_prefix="simulation")
    tabs = st.tabs(["Live Evidence", "Run Status", "Provenance", "Rule Workbench"])
    with tabs[0]:
        render_evidence_timeline_tab(context, "plasma", key_prefix="simulation")
    with tabs[1]:
        render_section_intro(
            "Scenario Progress",
            "Executed sandbox scenarios and runtime status for the current job.",
        )
        if context.scenarios.empty:
            st.info("No scenario telemetry has been emitted yet.")
        else:
            st.dataframe(
                context.scenarios[
                    ["name", "status", "started_at", "ended_at", "duration_s"]
                ],
                column_config={
                    "name": st.column_config.TextColumn("Scenario"),
                    "status": st.column_config.TextColumn("Status"),
                    "started_at": st.column_config.NumberColumn(
                        "Started At", format="%.3f"
                    ),
                    "ended_at": st.column_config.NumberColumn(
                        "Ended At", format="%.3f"
                    ),
                    "duration_s": st.column_config.NumberColumn(
                        "Duration (s)", format="%.3f"
                    ),
                },
                hide_index=True,
                height=260,
            )

            if scan_job.get("install_output") or scan_job.get("automation_output"):
                col_install, col_auto = st.columns(2, gap="large")
                with col_install:
                    render_section_intro(
                        "Install Output", "Sandbox extension installation logs."
                    )
                    with st.container(height=220):
                        st.code(
                            scan_job.get("install_output") or "(no output)",
                            language="text",
                        )
                with col_auto:
                    render_section_intro(
                        "Automation Output",
                        "Playwright automation logs from the executor.",
                    )
                    with st.container(height=220):
                        st.code(
                            scan_job.get("automation_output") or "(no output)",
                            language="text",
                        )
    with tabs[2]:
        render_provenance_tab(context, key_prefix="simulation")
    with tabs[3]:
        render_rule_workbench_tab(context, key_prefix="simulation")

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
