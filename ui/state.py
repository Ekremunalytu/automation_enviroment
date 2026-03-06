"""Session state helpers for the Streamlit UI."""

from __future__ import annotations

import streamlit as st
from api import fetch_analysis_job, fetch_report, start_analysis_job


def apply_pending_navigation() -> None:
    pending_nav_page = st.session_state.pop("pending_nav_page", None)
    if pending_nav_page:
        st.session_state["nav_page"] = pending_nav_page


def sync_active_scan_job() -> tuple[dict | None, bool, str | None]:
    current_scan_job = st.session_state.get("last_scan_status")
    active_scan_job_id = st.session_state.get("active_scan_job_id")
    if not active_scan_job_id:
        return current_scan_job, False, None

    live_job, error = fetch_analysis_job(active_scan_job_id)
    if error or live_job is None:
        return current_scan_job, False, error

    current_scan_job = live_job
    st.session_state["last_scan_status"] = live_job

    if live_job.get("status") in {"completed", "failed"}:
        st.session_state.pop("active_scan_job_id", None)
        if live_job.get("status") == "completed" and live_job.get("report_path"):
            st.cache_data.clear()
            st.session_state["pending_report"] = live_job["report_path"]
        return current_scan_job, True, None

    return current_scan_job, False, None


def load_scan_report(scan_job: dict | None) -> tuple[dict | None, str | None]:
    if not scan_job or not scan_job.get("report_path"):
        return None, None

    report, error = fetch_report(scan_job["report_path"])
    return (report or None), error


def process_pending_scan_request() -> None:
    scan_request = st.session_state.pop("scan_request", None)
    if not scan_request:
        return

    job, error = start_analysis_job(
        scan_request["publisher"],
        scan_request["name"],
        scan_request["version"],
    )
    if error:
        st.error(error)
        return

    if not job:
        st.error("Analysis start failed without a job payload.")
        return

    st.session_state["active_scan_job_id"] = job["job_id"]
    st.session_state["last_scan_status"] = job
    st.cache_data.clear()
    st.rerun()
