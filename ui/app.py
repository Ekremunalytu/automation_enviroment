"""
ExTrace Intelligence Suite
==========================

Advanced Analytics Dashboard for VS Code Extension Security.
"""

import os
import time
from datetime import datetime
from typing import cast

import altair as alt
import pandas as pd
import requests  # type: ignore[import-untyped]
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
API_ACTIVATIONS_URL = f"{API_BASE_URL}/api/activations"
API_MARKETPLACE_SEARCH_URL = f"{API_BASE_URL}/api/marketplace/search"
API_MARKETPLACE_DOWNLOAD_URL = f"{API_BASE_URL}/api/marketplace/download"
API_MARKETPLACE_ANALYZE_URL = f"{API_BASE_URL}/api/marketplace/analyze"
API_MARKETPLACE_ANALYZE_START_URL = f"{API_MARKETPLACE_ANALYZE_URL}/start"
_FRAGMENT_DECORATOR = getattr(
    st, "fragment", getattr(st, "experimental_fragment", None)
)


def _auto_refresh_fragment(run_every: int | float | str | None):
    """Return a fragment decorator when supported, otherwise a no-op decorator."""
    if _FRAGMENT_DECORATOR is None:
        return lambda func: func
    return _FRAGMENT_DECORATOR(run_every=run_every)


st.set_page_config(
    page_title="ExTrace Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Advanced Theme & CSS (Cyber-Minimalist Aesthetic)
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
    /* -----------------------------------------------------------------------
       FONTS & VARIABLES
    ----------------------------------------------------------------------- */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&family=Outfit:wght@400;600;800&display=swap');

    :root {
        --bg-color: #050505;
        --card-bg: rgba(255, 255, 255, 0.03);
        --card-border: rgba(255, 255, 255, 0.06);
        --accent-primary: #8b5cf6; /* Violet */
        --accent-secondary: #06b6d4; /* Cyan */
        --accent-glow: rgba(139, 92, 246, 0.5);
        --text-primary: #f4f4f5;
        --text-secondary: #a1a1aa;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
    }

    /* -----------------------------------------------------------------------
       GLOBAL RESETS
    ----------------------------------------------------------------------- */
    .stApp {
        background-color: var(--bg-color);
        background-image:
            radial-gradient(
                circle at 10% 20%,
                rgba(139, 92, 246, 0.08),
                transparent 40%
            ),
            radial-gradient(
                circle at 90% 80%,
                rgba(6, 182, 212, 0.06),
                transparent 40%
            );
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif;
        color: var(--text-primary) !important;
        letter-spacing: -0.02em;
    }

    code {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* -----------------------------------------------------------------------
       SIDEBAR
    ----------------------------------------------------------------------- */
    section[data-testid="stSidebar"] {
        background-color: rgba(10, 10, 10, 0.8);
        border-right: 1px solid var(--card-border);
        backdrop-filter: blur(20px);
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    /* -----------------------------------------------------------------------
       GLASS CARDS
    ----------------------------------------------------------------------- */
    .glass-card {
        background: linear-gradient(
            145deg,
            rgba(255, 255, 255, 0.03) 0%,
            rgba(255, 255, 255, 0.01) 100%
        );
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--card-border);
        border-radius: 16px;
        padding: 24px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }

    .glass-card:hover {
        border-color: rgba(255, 255, 255, 0.12);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transform: translateY(-2px);
    }

    .glass-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    }

    .kpi-value {
        font-family: 'Outfit', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(180deg, #fff, #9ca3af);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 10px 0;
    }

    .kpi-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-secondary);
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .kpi-icon {
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: rgba(255,255,255,0.05);
        color: var(--text-primary);
        font-size: 1.1rem;
        border: 1px solid rgba(255,255,255,0.05);
    }

    /* -----------------------------------------------------------------------
       TABS & COMPONENTS
    ----------------------------------------------------------------------- */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        gap: 20px;
        border-bottom: 1px solid var(--card-border);
        padding-bottom: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background-color: transparent;
        border: none;
        color: var(--text-secondary);
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 1rem;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: white;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--accent-primary);
        background-color: transparent;
        position: relative;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"]::after {
        content: "";
        position: absolute;
        bottom: -11px;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--accent-primary);
        box-shadow: 0 -2px 10px var(--accent-glow);
    }

    /* Button Styling */
    .stButton > button {
        background: rgba(255,255,255,0.05);
        border: 1px solid var(--card-border);
        color: var(--text-primary);
        border-radius: 8px;
        transition: all 0.2s;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
    }

    .stButton > button:hover {
        background: rgba(255,255,255,0.1);
        border-color: var(--text-primary);
    }

    /* DataFrame Table Styling */
    div[data-testid="stDataFrame"] {
        background: transparent;
        border: 1px solid var(--card-border);
        border-radius: 12px;
    }

    /* Header Gradient Text */
    .gradient-text {
        background: linear-gradient(135deg, #a78bfa 0%, #22d3ee 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.3));
    }

    /* System Status Pulse */
    .status-dot {
        height: 8px;
        width: 8px;
        background-color: var(--success);
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse-green 2s infinite;
    }

    @keyframes pulse-green {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Helpers & Data
# ---------------------------------------------------------------------------


@st.cache_data(ttl=2)
def _fetch_report_list_cached() -> list[dict]:
    resp = requests.get(API_ACTIVATIONS_URL, timeout=2)
    resp.raise_for_status()
    return resp.json()


def fetch_report_list() -> tuple[list[dict], str | None]:
    try:
        return _fetch_report_list_cached(), None
    except requests.RequestException as exc:
        return [], f"Report list unavailable: {exc}"


@st.cache_data(ttl=2)
def _fetch_report_cached(filename: str) -> dict:
    url = (
        f"{API_ACTIVATIONS_URL}/latest"
        if filename == "latest"
        else f"{API_ACTIVATIONS_URL}/{filename}"
    )
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    return resp.json()


def is_valid_activation_report(data: dict) -> bool:
    return (
        isinstance(data, dict)
        and isinstance(data.get("summary"), dict)
        and isinstance(data.get("activated"), list)
    )


def fetch_report(filename: str) -> tuple[dict, str | None]:
    try:
        payload = _fetch_report_cached(filename)
    except requests.RequestException as exc:
        return {}, f"Error loading report: {exc}"

    if not is_valid_activation_report(payload):
        return {}, "Selected file is not a valid activation report."

    return payload, None


def start_analysis_job(publisher: str, name: str, version: str) -> dict | None:
    try:
        resp = requests.post(
            API_MARKETPLACE_ANALYZE_START_URL,
            json={"publisher": publisher, "name": name, "version": version},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        st.error(f"Analysis start error: {exc}")
        return None


def fetch_analysis_job(job_id: str) -> dict | None:
    try:
        resp = requests.get(f"{API_MARKETPLACE_ANALYZE_URL}/{job_id}", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        st.error(f"Analysis status error: {exc}")
        return None


def sync_active_scan_job() -> tuple[dict | None, bool]:
    """Refresh the active sandbox job snapshot from the API."""
    current_scan_job = st.session_state.get("last_scan_status")
    active_scan_job_id = st.session_state.get("active_scan_job_id")
    if not active_scan_job_id:
        return current_scan_job, False

    live_job = fetch_analysis_job(active_scan_job_id)
    if live_job is None:
        return current_scan_job, False

    current_scan_job = live_job
    st.session_state["last_scan_status"] = live_job

    if live_job.get("status") in {"completed", "failed"}:
        st.session_state.pop("active_scan_job_id", None)
        if live_job.get("status") == "completed" and live_job.get("report_path"):
            st.cache_data.clear()
            st.session_state["pending_report"] = live_job["report_path"]
        return current_scan_job, True

    return current_scan_job, False


def load_scan_report(scan_job: dict | None) -> tuple[dict | None, str | None]:
    """Load the activation report associated with the current scan job."""
    if not scan_job or not scan_job.get("report_path"):
        return None, None

    report, report_error = fetch_report(scan_job["report_path"])
    return (report or None), report_error


def process_data(data: dict) -> pd.DataFrame:
    activated = data.get("activated", [])
    if not activated:
        return pd.DataFrame()

    df = pd.DataFrame(activated)
    if "activation_event" not in df.columns:
        df["activation_event"] = "(unknown trigger)"
    df["activation_event"] = (
        df["activation_event"].fillna("").replace("", "(unknown trigger)")
    )

    # Ensure duration_ms exists and fill missing values
    if "duration_ms" not in df.columns:
        df["duration_ms"] = 50
    df["duration_ms"] = pd.to_numeric(df["duration_ms"], errors="coerce").fillna(50)

    # Convert timestamps
    has_valid_timestamps = False
    if "timestamp" in df.columns:
        df["dt"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # Retry NaT values as UNIX seconds (for non-empty strings that failed ISO parse)
        mask_nat = df["dt"].isna() & df["timestamp"].notna() & (df["timestamp"] != "")
        if mask_nat.any():
            numeric_ts = pd.to_numeric(df.loc[mask_nat, "timestamp"], errors="coerce")
            df.loc[mask_nat, "dt"] = pd.to_datetime(numeric_ts, unit="s")

        has_valid_timestamps = df["dt"].notna().any()

    monitoring_start = pd.to_datetime(
        data.get("summary", {}).get("monitoring_started_at"),
        unit="s",
        errors="coerce",
    )
    if pd.isna(monitoring_start):
        monitoring_start = pd.Timestamp.now()

    if has_valid_timestamps:
        start_time = df["dt"].dropna().min()
        missing_mask = df["dt"].isna()
        if missing_mask.any():
            synthetic = (
                df.loc[missing_mask, "duration_ms"].cumsum().shift(fill_value=0)
                / 1000.0
            )
            df.loc[missing_mask, "dt"] = start_time + pd.to_timedelta(
                synthetic, unit="s"
            )
        df["rel_start"] = (df["dt"] - start_time).dt.total_seconds()
    else:
        cumulative = df["duration_ms"].cumsum().shift(fill_value=0)
        df["dt"] = monitoring_start + pd.to_timedelta(cumulative, unit="ms")
        df["rel_start"] = cumulative / 1000.0

    df["rel_end"] = df["rel_start"] + (df["duration_ms"] / 1000)

    # Categorize durations
    df["performance"] = pd.cut(
        df["duration_ms"],
        bins=[-1, 50, 200, 1000, 999999],
        labels=["⚡ Instant", "✅ Fast", "⚠️ Slow", "🔥 Critical"],
    )

    # Ensure 'source' column exists for the data grid
    if "source" not in df.columns:
        df["source"] = ""

    df["lane_base"] = (
        df["extension_id"].fillna("unknown.extension") + " · " + df["activation_event"]
    )
    lane_index = df.groupby("lane_base").cumcount()
    df["lane"] = df["lane_base"] + lane_index.map(
        lambda idx: "" if idx == 0 else f" · #{idx + 1}"
    )

    return df


def process_network_data(data: dict) -> pd.DataFrame:
    events = data.get("network_events", [])
    if not events:
        return pd.DataFrame()

    df = pd.DataFrame(events)
    for column in [
        "timestamp",
        "rel_time_s",
        "protocol",
        "event_type",
        "source_ip",
        "destination_ip",
        "destination_port",
        "host",
        "path",
        "summary",
    ]:
        if column not in df.columns:
            df[column] = ""

    df["dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["rel_time_s"] = pd.to_numeric(df["rel_time_s"], errors="coerce")
    if df["rel_time_s"].isna().all() and df["dt"].notna().any():
        start_time = df["dt"].dropna().min()
        df["rel_time_s"] = (df["dt"] - start_time).dt.total_seconds()

    df["destination_port"] = pd.to_numeric(
        df["destination_port"], errors="coerce"
    ).astype("Int64")
    df["protocol"] = df["protocol"].fillna("").replace("", "unknown")
    df["event_type"] = df["event_type"].fillna("").replace("", "network_event")
    df["host_display"] = (
        df["host"]
        .fillna("")
        .replace("", pd.NA)
        .fillna(df["destination_ip"].fillna("").replace("", pd.NA))
        .fillna("(unknown host)")
    )
    df["event_label"] = df["event_type"].str.replace("_", " ").str.title()
    df["protocol_label"] = df["protocol"].str.upper()
    df["lane"] = df["host_display"] + " · " + df["event_label"]
    return df.sort_values(
        by=["rel_time_s", "host_display"],
        ascending=[True, True],
        na_position="last",
    )


def build_network_log(network_df: pd.DataFrame, limit: int = 400) -> str:
    if network_df.empty:
        return ""

    lines: list[str] = []
    recent = network_df.tail(limit)
    for row in recent.itertuples(index=False):
        rel = f"{row.rel_time_s:8.3f}s" if pd.notna(row.rel_time_s) else "   --.--s"
        host = row.host_display if row.host_display else "(unknown host)"
        port = f":{int(row.destination_port)}" if pd.notna(row.destination_port) else ""
        path = f" {row.path}" if row.path else ""
        src = f"{row.source_ip} -> " if row.source_ip else ""
        lines.append(
            f"[{rel}] {row.protocol_label:<6} {row.event_label:<18} "
            f"{src}{host}{port}{path}"
        )
    return "\n".join(lines)


def process_file_data(data: dict) -> pd.DataFrame:
    events = data.get("file_events", [])
    if not events:
        return pd.DataFrame()

    df = pd.DataFrame(events)
    for column in [
        "timestamp",
        "rel_time_s",
        "operation",
        "path",
        "secondary_path",
        "source",
        "observer",
        "scenario_name",
        "related_extension_id",
        "related_activation_event",
        "flags",
        "sensitive",
        "summary",
    ]:
        if column not in df.columns:
            df[column] = ""

    df["dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["rel_time_s"] = pd.to_numeric(df["rel_time_s"], errors="coerce")
    df["source"] = df["source"].fillna("").replace("", "unknown")
    df["observer"] = df["observer"].fillna("").replace("", "unknown")
    df["operation"] = df["operation"].fillna("").replace("", "io")
    df["sensitive"] = df["sensitive"].fillna(False).astype(bool)
    df["path_short"] = (
        df["path"]
        .fillna("")
        .map(lambda value: value if len(value) <= 72 else f"...{value[-69:]}")
    )
    df["activation_label"] = (
        df["related_extension_id"].fillna("").replace("", "(unlinked)")
        + " · "
        + df["related_activation_event"].fillna("").replace("", "no activation link")
    )
    df["scenario_label"] = df["scenario_name"].fillna("").replace("", "(no scenario)")
    df["operation_label"] = df["operation"].str.title()
    df["source_label"] = df["source"].str.replace("_", " ").str.title()
    df["lane"] = df["path_short"] + " · " + df["operation_label"]
    return df.sort_values(
        by=["rel_time_s", "path"],
        ascending=[True, True],
        na_position="last",
    )


def build_file_log(file_df: pd.DataFrame, limit: int = 400) -> str:
    if file_df.empty:
        return ""

    lines: list[str] = []
    recent = file_df.tail(limit)
    for row in recent.itertuples(index=False):
        rel = f"{row.rel_time_s:8.3f}s" if pd.notna(row.rel_time_s) else "   --.--s"
        sensitive = " SENSITIVE" if row.sensitive else ""
        activation = (
            f" [{row.related_extension_id}:{row.related_activation_event}]"
            if row.related_extension_id or row.related_activation_event
            else ""
        )
        scenario = f" [{row.scenario_name}]" if row.scenario_name else ""
        lines.append(
            f"[{rel}] {row.source_label:<10} {row.operation_label:<8} "
            f"{row.path}{sensitive}{scenario}{activation}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Marketplace Helpers
# ---------------------------------------------------------------------------


def search_marketplace(query: str) -> list[dict]:
    try:
        resp = requests.get(
            API_MARKETPLACE_SEARCH_URL, params={"query": query}, timeout=15
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Search error: {e}")
        return []


def download_extension(publisher: str, name: str, version: str) -> dict | None:
    try:
        resp = requests.post(
            API_MARKETPLACE_DOWNLOAD_URL,
            json={"publisher": publisher, "name": name, "version": version},
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 409:
            # Extension already registered — treat as successful download
            st.info("Extension already downloaded and registered.")
            return {"status": "already_exists"}
        st.error(f"Download error: {e}")
        return None
    except Exception as e:
        st.error(f"Download error: {e}")
        return None


def analyze_extension(publisher: str, name: str, version: str) -> dict | None:
    try:
        resp = requests.post(
            API_MARKETPLACE_ANALYZE_URL,
            json={"publisher": publisher, "name": name, "version": version},
            timeout=600,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Analysis error: {e}")
        return None


# ---------------------------------------------------------------------------
# Marketplace Page Renderer
# ---------------------------------------------------------------------------


def render_marketplace_page() -> None:
    st.markdown(
        """
        <h1 style="font-size: 2.5rem; margin-bottom: 0;">
            VS Code <span class="gradient-text">Marketplace</span>
        </h1>
        <p style="color: #a1a1aa; margin-top: 4px;">
            Search, download, and statically analyze extensions from the Marketplace.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

    # Search form — prevents re-run on every keystroke
    with st.form("marketplace_search_form"):
        col_q, col_btn = st.columns([4, 1])
        with col_q:
            query = st.text_input(
                "Search",
                placeholder="e.g. python, prettier, eslint",
                label_visibility="collapsed",
            )
        with col_btn:
            submitted = st.form_submit_button("Search", use_container_width=True)

    if submitted and query.strip():
        with st.spinner("Searching Marketplace..."):
            marketplace_results = search_marketplace(query.strip())
        st.session_state["marketplace_results"] = marketplace_results

    results: list[dict] = st.session_state.get("marketplace_results", [])

    if not results:
        if submitted:
            st.info("No results found.")
        return

    st.markdown(f"### Results ({len(results)})")

    for ext in results:
        pub = ext.get("publisher", "")
        ext_name = ext.get("name", "")
        ver = ext.get("version", "")
        display = ext.get("displayName", ext_name)
        desc = ext.get("description", "")
        installs = ext.get("installs", 0)
        rating = ext.get("rating", 0.0)

        c_info, c_btn = st.columns([5, 1.2], vertical_alignment="center")
        with c_info:
            action_state = (
                "Ready to analyze"
                if st.session_state.get(f"downloaded_{pub}_{ext_name}_{ver}", False)
                else "Marketplace"
            )
            st.markdown(
                f"""
                <div class="glass-card" style="margin-bottom: 12px; min-height: 152px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; gap: 12px; align-items: flex-start;">
                            <div style="font-size: 1.1rem; font-weight: 700; color: #f4f4f5;">
                                {display}
                            </div>
                            <div style="padding: 4px 10px; border-radius: 999px; border: 1px solid rgba(34, 211, 238, 0.25); color: #22d3ee; background: rgba(34, 211, 238, 0.08); font-size: 0.72rem; letter-spacing: 0.05em; text-transform: uppercase;">
                                {action_state}
                            </div>
                        </div>
                        <div style="font-size: 0.78rem; color: #a1a1aa; margin: 8px 0 10px 0;">
                            <code style="color: #8b5cf6;">{pub}.{ext_name}</code>
                        </div>
                        <div style="font-size: 0.9rem; color: #d4d4d8; line-height: 1.5;">{desc}</div>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px;">
                        <div style="padding: 5px 10px; border-radius: 999px; background: rgba(139, 92, 246, 0.12); border: 1px solid rgba(139, 92, 246, 0.25); color: #c4b5fd; font-size: 0.76rem;">
                            v{ver}
                        </div>
                        <div style="padding: 5px 10px; border-radius: 999px; background: rgba(6, 182, 212, 0.12); border: 1px solid rgba(6, 182, 212, 0.25); color: #67e8f9; font-size: 0.76rem;">
                            ⬇ {installs:,}
                        </div>
                        <div style="padding: 5px 10px; border-radius: 999px; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.25); color: #fcd34d; font-size: 0.76rem;">
                            ★ {rating:.1f}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_btn:
            ext_key = f"{pub}_{ext_name}_{ver}"
            downloaded = st.session_state.get(f"downloaded_{ext_key}", False)

            if not downloaded:
                btn_key = f"dl_{ext_key}"
                if st.button("Download", key=btn_key, use_container_width=True):
                    with st.spinner(f"Downloading {ext_name}..."):
                        result = download_extension(pub, ext_name, ver)
                    if result:
                        st.session_state[f"downloaded_{ext_key}"] = True
                        if result.get("status") == "already_exists":
                            st.success("Ready to analyze!")
                        else:
                            st.success(f"Downloaded! DB ID: {result.get('db_id')}")
                        st.rerun()
            else:
                analyze_key = f"az_{ext_key}"

                def _start_scan(p=pub, n=ext_name, v=ver):
                    st.session_state["scan_request"] = {
                        "publisher": p,
                        "name": n,
                        "version": v,
                    }
                    st.session_state["pending_nav_page"] = "Simulation"

                st.button(
                    "Analyze",
                    key=analyze_key,
                    use_container_width=True,
                    on_click=_start_scan,
                )


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
    ext_id = (
        f"{scan_job.get('publisher', 'unknown')}.{scan_job.get('name', 'unknown')}"
        f"@{scan_job.get('version', 'unknown')}"
    )

    with st.status(
        f"Sandbox analysis — {ext_id}",
        state=state_map.get(scan_job.get("status", "queued"), "running"),
        expanded=True,
    ):
        st.caption(scan_job.get("message", "Waiting for sandbox analysis status."))
        total_steps = max(len(scan_job.get("steps", [])), 1)
        for idx, step in enumerate(scan_job.get("steps", []), start=1):
            title = step_titles.get(step.get("name", ""), step.get("name", "Step"))
            status = step.get("status", "pending")
            prefix = {
                "completed": "✓",
                "failed": "✕",
                "running": "•",
                "pending": "…",
                "skipped": "○",
            }.get(status, "…")
            st.write(f"**{idx}/{total_steps}** — {prefix} {title}")
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
                        scan_job.get("install_output") or "(no output)",
                        language="text",
                    )
                with col_auto:
                    st.caption("Automation Output")
                    st.code(
                        scan_job.get("automation_output") or "(no output)",
                        language="text",
                    )


def metric_card(icon: str, label: str, value: str, color: str) -> str:
    return f"""
    <div class="glass-card">
        <div class="kpi-label">
            <div class="kpi-icon" style="color: {color}; border-color: {color}20; background: {color}10;">{icon}</div>
            {label}
        </div>
        <div class="kpi-value">{value}</div>
    </div>
    """


def get_active_scenario_name(report: dict) -> str | None:
    traces = report.get("scenario_traces", [])
    if not isinstance(traces, list):
        return None

    for trace in reversed(traces):
        if trace.get("status") == "running":
            return trace.get("name")
    return None


def render_simulation_page(scan_job: dict | None, live_report: dict | None) -> None:
    st.markdown(
        """
        <h1 style="font-size: 2.5rem; margin-bottom: 0;">
            Live <span class="gradient-text">Simulation</span>
        </h1>
        <p style="color: #a1a1aa; margin-top: 4px;">
            Monitor sandbox execution, active automations, and incoming telemetry in real time.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

    if not scan_job:
        st.info("No active simulation. Start an analysis from Marketplace.")
        return

    ext_id = (
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
                <div style="font-size: 1.5rem; font-weight: 700; color: #f4f4f5; margin: 12px 0 18px 0;">{ext_id}</div>
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

    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)
    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        st.markdown(
            metric_card(
                "⚡",
                "Activations",
                str(summary.get("total_activated", 0)),
                "#8b5cf6",
            ),
            unsafe_allow_html=True,
        )
    with stat2:
        st.markdown(
            metric_card(
                "🌐",
                "Network",
                str(network_summary.get("total_events", 0)),
                "#10b981",
            ),
            unsafe_allow_html=True,
        )
    with stat3:
        st.markdown(
            metric_card(
                "🗂️",
                "File I/O",
                str(file_summary.get("total_events", 0)),
                "#22d3ee",
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

    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)
    render_scan_status(scan_job)

    sim_tabs = st.tabs(
        [
            "🔴 Live Pulse",
            "🌐 Network Stream",
            "🗂️ File Stream",
        ]
    )

    with sim_tabs[0]:
        if live_report:
            traces = pd.DataFrame(live_report.get("scenario_traces", []))
            if not traces.empty:
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
                st.info("Scenario timeline has not started streaming yet.")
        else:
            st.info("Waiting for live report telemetry...")

    with sim_tabs[1]:
        network_df = process_network_data(live_report or {})
        if not network_df.empty:
            with st.container(height=320):
                st.code(build_network_log(network_df), language="log")
        else:
            st.info("No network telemetry yet.")

    with sim_tabs[2]:
        file_df = process_file_data(live_report or {})
        if not file_df.empty:
            with st.container(height=320):
                st.code(build_file_log(file_df), language="log")
        else:
            st.info("No file telemetry yet.")

    if st.button("Clear simulation state", key="clear_scan_state"):
        st.session_state.pop("last_scan_status", None)
        st.session_state.pop("active_scan_job_id", None)
        st.session_state.pop("pending_report", None)
        st.session_state["pending_nav_page"] = "Dashboard"
        st.rerun()


@_auto_refresh_fragment(run_every=2)
def render_live_simulation_fragment() -> None:
    """Render the live Simulation page with isolated periodic refresh."""
    current_scan_job, scan_finished = sync_active_scan_job()
    live_report, report_error = load_scan_report(current_scan_job)

    if (
        report_error
        and current_scan_job
        and current_scan_job.get("status") in {"running", "completed"}
    ):
        st.info("Preparing live simulation report...")

    if (
        _FRAGMENT_DECORATOR is None
        and current_scan_job
        and current_scan_job.get("status") == "running"
    ):
        st.caption(
            "Automatic live refresh requires Streamlit fragment support. "
            "Use System Refresh while the analysis is running."
        )

    render_simulation_page(current_scan_job, live_report)

    if scan_finished:
        st.rerun()


# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------

# Defaults (overridden inside sidebar when page == "Dashboard")
target = None
chart_theme = "plasma"

pending_nav_page = st.session_state.pop("pending_nav_page", None)
if pending_nav_page:
    st.session_state["nav_page"] = pending_nav_page

with st.sidebar:
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h2 style="margin:0; font-size: 1.4rem;">⚡ ExTrace</h2>
            <div style="font-size: 0.8rem; color: #a1a1aa; letter-spacing: 0.05em;">INTELLIGENCE SUITE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        ["Dashboard", "Simulation", "Marketplace", "Theme"],
        key="nav_page",
        label_visibility="collapsed",
    )

    st.markdown("---")

    if page == "Dashboard":
        reports, report_list_error = fetch_report_list()

        if report_list_error:
            st.error(report_list_error)

        if reports:
            report_map = {r["filename"]: r for r in reports}
            pending = st.session_state.get("pending_report")
            report_names = list(report_map.keys())
            if pending and pending not in report_map:
                report_names = [pending, *report_names]

            opts = ["(Latest Report)", *report_names]

            if pending and pending in report_map:
                st.session_state["selected_report"] = pending
                st.session_state.pop("pending_report", None)
            elif st.session_state.get("selected_report") not in opts:
                st.session_state["selected_report"] = "(Latest Report)"

            selection = st.selectbox(
                "Select Analysis Session",
                opts,
                key="selected_report",
            )

            if selection == "(Latest Report)":
                target = "latest"
                meta = reports[0]
            else:
                target = selection
                meta = report_map.get(
                    selection,
                    {
                        "modified": time.time(),
                        "size_bytes": 0,
                    },
                )

            # Metadata Card
            st.markdown(
                f"""
                <div style="
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,0.06);
                    border-radius: 12px;
                    padding: 16px;
                    margin-top: 16px;
                ">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #a1a1aa; font-size: 0.8rem;">Date</span>
                        <span style="color: #fff; font-weight: 600; font-size: 0.8rem;">
                            {datetime.fromtimestamp(meta.get("modified", 0)).strftime("%Y-%m-%d %H:%M")}
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

        else:
            st.warning("No reports found.")

    if page == "Simulation":
        current_job = st.session_state.get("last_scan_status")
        if current_job:
            st.markdown(
                f"""
                <div style="
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,0.06);
                    border-radius: 12px;
                    padding: 16px;
                    margin-top: 16px;
                ">
                    <div style="color: #a1a1aa; font-size: 0.78rem; margin-bottom: 8px;">Live Sandbox</div>
                    <div style="color: #fff; font-weight: 700; font-size: 0.95rem; line-height: 1.5;">
                        {current_job.get("publisher", "unknown")}.{current_job.get("name", "unknown")}@{current_job.get("version", "unknown")}
                    </div>
                    <div style="margin-top: 10px; color: #67e8f9; font-size: 0.8rem;">
                        Status: {current_job.get("status", "queued").title()}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("No active simulation.")

    st.markdown("---")
    if st.button("🔄 System Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        """
        <div style="position: fixed; bottom: 20px; font-size: 0.7rem; color: #52525b;">
            v2.1.0 • SYSTEM ONLINE
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Live Scan Execution (triggered from Marketplace → Analyze)
# ---------------------------------------------------------------------------

scan_req = st.session_state.pop("scan_request", None)
if scan_req:
    job = start_analysis_job(
        scan_req["publisher"],
        scan_req["name"],
        scan_req["version"],
    )
    if job:
        st.session_state["active_scan_job_id"] = job["job_id"]
        st.session_state["last_scan_status"] = job
        st.cache_data.clear()
        st.rerun()

current_scan_job = st.session_state.get("last_scan_status")

if page == "Simulation":
    render_live_simulation_fragment()
    st.stop()

# ---------------------------------------------------------------------------
# Main Logic
# ---------------------------------------------------------------------------

if page == "Marketplace":
    render_marketplace_page()
    st.stop()

if page == "Theme":
    st.markdown(
        """
        <h1 style="font-size: 2.5rem; margin-bottom: 0;">
            Visual <span class="gradient-text">Theme</span>
        </h1>
        <p style="color: #a1a1aa; margin-top: 4px;">
            Customize the look and feel of your analysis dashboard.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

    selected_theme = st.select_slider(
        "Chart Color Palette",
        options=["turbo", "plasma", "inferno", "magma"],
        value=st.session_state.get("chart_theme", "plasma"),
    )
    if selected_theme != st.session_state.get("chart_theme"):
        st.session_state["chart_theme"] = selected_theme
        st.rerun()

    st.info("Additional theme settings will go here in the future.")
    st.stop()

if not target:
    st.markdown(
        "<div style='text-align: center; margin-top: 20vh; color: #52525b;'>"
        "Select a completed analysis report from the sidebar.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

resolved_target = cast(str, target)
raw_data, report_error = fetch_report(resolved_target)
if report_error:
    if st.session_state.get("pending_report") == resolved_target:
        st.info("Finalizing completed report...")
        time.sleep(2)
        st.rerun()
    st.error(report_error)
    st.stop()

if not raw_data:
    st.error("Failed to load report data.")
    st.stop()

df = process_data(raw_data)
network_df = process_network_data(raw_data)
file_df = process_file_data(raw_data)
summary = raw_data.get("summary", {})
network_summary = raw_data.get("network_summary", {})
file_summary = raw_data.get("file_summary", {})
running = raw_data.get("running_extensions", [])

chart_theme = st.session_state.get("chart_theme", "plasma")

# ---------------------------------------------------------------------------
# Dashboard Header
# ---------------------------------------------------------------------------

col_header, col_status = st.columns([3, 1])

with col_header:
    target_ext = raw_data.get("_metadata", {}).get("filename", "Unknown")
    scenarios = summary.get("scenarios_run", [])
    scenarios_badges = (
        " ".join(
            [
                f'<span style="background: rgba(139, 92, 246, 0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; margin-right: 4px; border: 1px solid rgba(139, 92, 246, 0.4);">{s}</span>'
                for s in scenarios
            ]
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
            <strong style="color: #22d3ee; font-size: 1.1rem; letter-spacing: 0.02em;">{target_ext}</strong>
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

# ---------------------------------------------------------------------------
# KPI Cards Grid
# ---------------------------------------------------------------------------

k1, k2, k3, k4, k5 = st.columns(5)


with k1:
    st.markdown(
        metric_card("⚡", "Total Events", f"{len(df):,}", "#8b5cf6"),
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        metric_card(
            "📦", "Extensions", str(summary.get("unique_extensions", 0)), "#06b6d4"
        ),
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        metric_card(
            "🌐",
            "Network Events",
            str(network_summary.get("total_events", len(network_df))),
            "#10b981",
        ),
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        metric_card(
            "🛰️",
            "Network Hosts",
            str(
                network_summary.get(
                    "unique_hosts",
                    network_df["host_display"].nunique() if not network_df.empty else 0,
                )
            ),
            "#f97316",
        ),
        unsafe_allow_html=True,
    )
with k5:
    dur = summary.get("monitoring_duration_s", 0)
    st.markdown(
        metric_card("⏱️", "Duration", f"{dur:.1f}s", "#f59e0b"), unsafe_allow_html=True
    )

st.markdown("<div style='height: 48px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Deep Dive Analysis
# ---------------------------------------------------------------------------

tab_viz, tab_network, tab_file, tab_perf, tab_grid, tab_raw, tab_host_logs = st.tabs(
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

# --- Tab 1: Visual Intelligence ---
with tab_viz:
    if not df.empty:
        c1, c2 = st.columns([2, 1])

        with c1:
            st.markdown("### Activity Pulse")

            # Interactive Brush
            brush = alt.selection_interval(encodings=["x"])

            # Dynamically calculate height based on number of unique extensions
            lane_count = df["lane"].nunique() if not df.empty else 10
            chart_height = max(400, lane_count * 24)

            # Main Scatter Plot
            chart = (
                alt.Chart(df)
                .mark_circle(size=80, opacity=0.8)
                .encode(
                    x=alt.X(
                        "rel_start",
                        title="Timeline (seconds)",
                        axis=alt.Axis(gridColor="#333"),
                    ),
                    y=alt.Y(
                        "lane",
                        title=None,
                        axis=alt.Axis(labelLimit=200, gridColor="#333"),
                    ),
                    color=alt.Color(
                        "activation_event",
                        scale=alt.Scale(scheme=chart_theme),
                        legend=None,
                    ),
                    size=alt.Size(
                        "duration_ms", scale=alt.Scale(range=[50, 500]), legend=None
                    ),
                    tooltip=[
                        "extension_id",
                        "activation_event",
                        "duration_ms",
                        "rel_start",
                        "source",
                    ],
                )
                .properties(height=chart_height, width="container")
                .add_params(brush)
            )

            # Density Area Chart
            hist = (
                alt.Chart(df)
                .mark_area(
                    interpolate="monotone",
                    fillOpacity=0.5,
                    line={"color": "#06b6d4"},
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(color="#06b6d4", offset=0),
                            alt.GradientStop(color="rgba(6, 182, 212, 0.1)", offset=1),
                        ],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0,
                    ),
                )
                .encode(
                    x=alt.X(
                        "rel_start", bin=alt.Bin(maxbins=50), title=None, axis=None
                    ),
                    y=alt.Y("count()", title=None, axis=None),
                )
                .properties(height=60, width="container")
                .transform_filter(brush)
            )

            st.altair_chart(chart & hist, theme="streamlit")

        with c2:
            st.markdown("### Distribution")

            pie = (
                alt.Chart(df)
                .mark_arc(
                    innerRadius=80, cornerRadius=6, stroke="#050505", strokeWidth=2
                )
                .encode(
                    theta=alt.Theta("count()"),
                    color=alt.Color(
                        "activation_event",
                        scale=alt.Scale(scheme=chart_theme),
                        legend=alt.Legend(
                            orient="bottom", columns=1, labelColor="#a1a1aa"
                        ),
                    ),
                    order=alt.Order("count()", sort="descending"),
                    tooltip=["activation_event", "count()"],
                )
                .properties(height=480)
            )

            st.altair_chart(pie, theme="streamlit")
    else:
        st.info("No activation data to visualize.")

# --- Tab 2: Network Telemetry ---
with tab_network:
    if not network_df.empty:
        n1, n2 = st.columns([2, 1])

        with n1:
            st.markdown("### Live Network Timeline")
            lane_count = network_df["lane"].nunique()
            chart_height = max(360, lane_count * 22)

            timeline = (
                alt.Chart(network_df)
                .mark_circle(size=90, opacity=0.85)
                .encode(
                    x=alt.X(
                        "rel_time_s",
                        title="Timeline (seconds)",
                        axis=alt.Axis(gridColor="#333"),
                    ),
                    y=alt.Y(
                        "lane",
                        title=None,
                        axis=alt.Axis(labelLimit=220, gridColor="#333"),
                    ),
                    color=alt.Color(
                        "event_label",
                        scale=alt.Scale(scheme=chart_theme),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("dt:T", title="Timestamp"),
                        alt.Tooltip("protocol_label:N", title="Protocol"),
                        alt.Tooltip("event_label:N", title="Event"),
                        alt.Tooltip("host_display:N", title="Host"),
                        alt.Tooltip("destination_port:Q", title="Port"),
                        alt.Tooltip("summary:N", title="Summary"),
                    ],
                )
                .properties(height=chart_height, width="container")
            )

            density = (
                alt.Chart(network_df)
                .mark_area(
                    interpolate="monotone",
                    fillOpacity=0.45,
                    line={"color": "#22d3ee"},
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(color="#22d3ee", offset=0),
                            alt.GradientStop(
                                color="rgba(34, 211, 238, 0.08)", offset=1
                            ),
                        ],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0,
                    ),
                )
                .encode(
                    x=alt.X(
                        "rel_time_s", bin=alt.Bin(maxbins=40), title=None, axis=None
                    ),
                    y=alt.Y("count()", title=None, axis=None),
                )
                .properties(height=60, width="container")
            )

            st.altair_chart(timeline & density, theme="streamlit")

        with n2:
            st.markdown("### Traffic Breakdown")
            distribution = (
                alt.Chart(network_df)
                .mark_arc(
                    innerRadius=80, cornerRadius=6, stroke="#050505", strokeWidth=2
                )
                .encode(
                    theta=alt.Theta("count()"),
                    color=alt.Color(
                        "event_label",
                        scale=alt.Scale(scheme=chart_theme),
                        legend=alt.Legend(
                            orient="bottom", columns=1, labelColor="#a1a1aa"
                        ),
                    ),
                    tooltip=["event_label", "count()"],
                )
                .properties(height=420)
            )
            st.altair_chart(distribution, theme="streamlit")

            top_hosts = (
                network_df.groupby("host_display", dropna=False)
                .size()
                .reset_index(name="events")
                .sort_values("events", ascending=False)
                .head(8)
            )
            host_bar = (
                alt.Chart(top_hosts)
                .mark_bar(cornerRadiusEnd=4, color="#06b6d4")
                .encode(
                    x=alt.X(
                        "events:Q", title="Events", axis=alt.Axis(gridColor="#333")
                    ),
                    y=alt.Y(
                        "host_display:N",
                        sort="-x",
                        title=None,
                        axis=alt.Axis(labelLimit=180),
                    ),
                    tooltip=["host_display", "events"],
                )
                .properties(height=240)
            )
            st.altair_chart(host_bar, theme="streamlit")

        st.markdown("### Network Event Log")
        network_log = build_network_log(network_df)
        with st.container(height=260):
            st.code(network_log or "(no live events yet)", language="log")

        st.markdown("### Network Grid")
        network_search = st.text_input(
            "Network search",
            placeholder="Filter by host, protocol, summary, or IP...",
            label_visibility="collapsed",
        )
        network_view = network_df.copy()
        if network_search:
            mask = (
                network_view["host_display"].str.contains(
                    network_search, case=False, na=False
                )
                | network_view["protocol_label"].str.contains(
                    network_search, case=False, na=False
                )
                | network_view["summary"].str.contains(
                    network_search, case=False, na=False
                )
                | network_view["source_ip"].str.contains(
                    network_search, case=False, na=False
                )
                | network_view["destination_ip"].str.contains(
                    network_search, case=False, na=False
                )
            )
            network_view = network_view[mask]

        st.dataframe(
            network_view[
                [
                    "dt",
                    "protocol_label",
                    "event_label",
                    "host_display",
                    "source_ip",
                    "destination_ip",
                    "destination_port",
                    "summary",
                ]
            ],
            column_config={
                "dt": st.column_config.DatetimeColumn(
                    "Timestamp", format="HH:mm:ss.SS"
                ),
                "protocol_label": st.column_config.TextColumn("Protocol"),
                "event_label": st.column_config.TextColumn("Event"),
                "host_display": st.column_config.TextColumn("Host", width="medium"),
                "source_ip": st.column_config.TextColumn("Source IP", width="medium"),
                "destination_ip": st.column_config.TextColumn(
                    "Destination IP", width="medium"
                ),
                "destination_port": st.column_config.NumberColumn("Port", format="%d"),
                "summary": st.column_config.TextColumn("Summary", width="large"),
            },
            height=440,
            hide_index=True,
        )

        if network_summary.get("capture_error"):
            st.warning(network_summary["capture_error"])
    else:
        capture_error = network_summary.get("capture_error")
        if capture_error:
            st.warning(capture_error)
        else:
            st.info("No network telemetry captured in this report yet.")

# --- Tab 3: File I/O Intelligence ---
with tab_file:
    if not file_df.empty:
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            st.markdown(
                metric_card(
                    "🗂️",
                    "File Events",
                    str(file_summary.get("total_events", len(file_df))),
                    "#22d3ee",
                ),
                unsafe_allow_html=True,
            )
        with f2:
            st.markdown(
                metric_card(
                    "🛡️",
                    "Sensitive Hits",
                    str(
                        file_summary.get(
                            "sensitive_events",
                            int(file_df["sensitive"].sum()),
                        )
                    ),
                    "#f43f5e",
                ),
                unsafe_allow_html=True,
            )
        with f3:
            st.markdown(
                metric_card(
                    "🧭",
                    "Automation I/O",
                    str((file_df["source"] == "automation").sum()),
                    "#8b5cf6",
                ),
                unsafe_allow_html=True,
            )
        with f4:
            st.markdown(
                metric_card(
                    "🧩",
                    "Extension I/O",
                    str((file_df["source"] == "extension").sum()),
                    "#f59e0b",
                ),
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([2, 1])

        with c1:
            st.markdown("### File Access Timeline")
            lane_count = file_df["lane"].nunique()
            chart_height = max(360, lane_count * 22)
            file_timeline = (
                alt.Chart(file_df)
                .mark_circle(size=95, opacity=0.85)
                .encode(
                    x=alt.X(
                        "rel_time_s",
                        title="Timeline (seconds)",
                        axis=alt.Axis(gridColor="#333"),
                    ),
                    y=alt.Y(
                        "lane",
                        title=None,
                        axis=alt.Axis(labelLimit=220, gridColor="#333"),
                    ),
                    color=alt.Color(
                        "source_label",
                        scale=alt.Scale(
                            domain=["Automation", "Extension", "System", "Unknown"],
                            range=["#8b5cf6", "#f59e0b", "#64748b", "#22d3ee"],
                        ),
                        legend=alt.Legend(orient="bottom", labelColor="#a1a1aa"),
                    ),
                    shape=alt.Shape(
                        "operation_label",
                        legend=alt.Legend(orient="bottom", labelColor="#a1a1aa"),
                    ),
                    tooltip=[
                        alt.Tooltip("dt:T", title="Timestamp"),
                        alt.Tooltip("source_label:N", title="Source"),
                        alt.Tooltip("operation_label:N", title="Operation"),
                        alt.Tooltip("path:N", title="Path"),
                        alt.Tooltip("scenario_label:N", title="Scenario"),
                        alt.Tooltip("activation_label:N", title="Activation Link"),
                    ],
                )
                .properties(height=chart_height, width="container")
            )
            st.altair_chart(file_timeline, theme="streamlit")

        with c2:
            st.markdown("### Attribution Mix")
            source_mix = (
                alt.Chart(file_df)
                .mark_arc(
                    innerRadius=80, cornerRadius=6, stroke="#050505", strokeWidth=2
                )
                .encode(
                    theta=alt.Theta("count()"),
                    color=alt.Color(
                        "source_label",
                        scale=alt.Scale(
                            domain=["Automation", "Extension", "System", "Unknown"],
                            range=["#8b5cf6", "#f59e0b", "#64748b", "#22d3ee"],
                        ),
                        legend=alt.Legend(orient="bottom", labelColor="#a1a1aa"),
                    ),
                    tooltip=["source_label", "count()"],
                )
                .properties(height=260)
            )
            st.altair_chart(source_mix, theme="streamlit")

            op_counts = (
                file_df.groupby(["operation_label", "source_label"], dropna=False)
                .size()
                .reset_index(name="events")
            )
            matrix = (
                alt.Chart(op_counts)
                .mark_bar(cornerRadiusEnd=4)
                .encode(
                    x=alt.X(
                        "events:Q",
                        title="Events",
                        axis=alt.Axis(gridColor="#333"),
                    ),
                    y=alt.Y(
                        "operation_label:N",
                        sort="-x",
                        title=None,
                        axis=alt.Axis(labelLimit=160),
                    ),
                    color=alt.Color(
                        "source_label:N",
                        scale=alt.Scale(
                            domain=["Automation", "Extension", "System", "Unknown"],
                            range=["#8b5cf6", "#f59e0b", "#64748b", "#22d3ee"],
                        ),
                        legend=None,
                    ),
                    tooltip=["operation_label", "source_label", "events"],
                )
                .properties(height=260)
            )
            st.altair_chart(matrix, theme="streamlit")

        d1, d2 = st.columns(2)
        with d1:
            st.markdown("### Sensitive Access Map")
            sensitive_df = file_df[file_df["sensitive"]].copy()
            if not sensitive_df.empty:
                sensitive_chart = (
                    alt.Chart(
                        sensitive_df.groupby(
                            ["path_short", "source_label"], dropna=False
                        )
                        .size()
                        .reset_index(name="events")
                        .head(12)
                    )
                    .mark_bar(cornerRadiusEnd=4)
                    .encode(
                        x=alt.X(
                            "events:Q", title="Events", axis=alt.Axis(gridColor="#333")
                        ),
                        y=alt.Y(
                            "path_short:N",
                            sort="-x",
                            title=None,
                            axis=alt.Axis(labelLimit=220),
                        ),
                        color=alt.Color(
                            "source_label:N",
                            scale=alt.Scale(
                                domain=["Automation", "Extension", "System", "Unknown"],
                                range=["#8b5cf6", "#f59e0b", "#64748b", "#22d3ee"],
                            ),
                            legend=None,
                        ),
                        tooltip=["path_short", "source_label", "events"],
                    )
                    .properties(height=300)
                )
                st.altair_chart(sensitive_chart, theme="streamlit")
            else:
                st.info("No sensitive file access observed in this report.")

        with d2:
            st.markdown("### Activation Correlation")
            linked_df = file_df[
                file_df["related_extension_id"].fillna("").ne("")
                | file_df["related_activation_event"].fillna("").ne("")
            ].copy()
            if not linked_df.empty:
                correlation = (
                    alt.Chart(
                        linked_df.groupby(
                            ["activation_label", "source_label"],
                            dropna=False,
                        )
                        .size()
                        .reset_index(name="events")
                        .sort_values("events", ascending=False)
                        .head(12)
                    )
                    .mark_bar(cornerRadiusEnd=4)
                    .encode(
                        x=alt.X(
                            "events:Q", title="Events", axis=alt.Axis(gridColor="#333")
                        ),
                        y=alt.Y(
                            "activation_label:N",
                            sort="-x",
                            title=None,
                            axis=alt.Axis(labelLimit=240),
                        ),
                        color=alt.Color(
                            "source_label:N",
                            scale=alt.Scale(
                                domain=["Automation", "Extension", "System", "Unknown"],
                                range=["#8b5cf6", "#f59e0b", "#64748b", "#22d3ee"],
                            ),
                            legend=None,
                        ),
                        tooltip=["activation_label", "source_label", "events"],
                    )
                    .properties(height=300)
                )
                st.altair_chart(correlation, theme="streamlit")
            else:
                st.info("No file events could be linked to activation records yet.")

        st.markdown("### File Event Log")
        file_log = build_file_log(file_df)
        with st.container(height=260):
            st.code(file_log or "(no file events yet)", language="log")

        st.markdown("### File I/O Grid")
        file_search = st.text_input(
            "File search",
            placeholder="Filter by path, source, scenario, activation, or summary...",
            label_visibility="collapsed",
        )
        file_view = file_df.copy()
        if file_search:
            mask = (
                file_view["path"].str.contains(file_search, case=False, na=False)
                | file_view["source_label"].str.contains(
                    file_search, case=False, na=False
                )
                | file_view["scenario_label"].str.contains(
                    file_search, case=False, na=False
                )
                | file_view["activation_label"].str.contains(
                    file_search, case=False, na=False
                )
                | file_view["summary"].str.contains(file_search, case=False, na=False)
            )
            file_view = file_view[mask]

        st.dataframe(
            file_view[
                [
                    "dt",
                    "source_label",
                    "operation_label",
                    "path",
                    "scenario_label",
                    "activation_label",
                    "observer",
                    "sensitive",
                    "summary",
                ]
            ],
            column_config={
                "dt": st.column_config.DatetimeColumn(
                    "Timestamp", format="HH:mm:ss.SS"
                ),
                "source_label": st.column_config.TextColumn("Source"),
                "operation_label": st.column_config.TextColumn("Operation"),
                "path": st.column_config.TextColumn("Path", width="large"),
                "scenario_label": st.column_config.TextColumn("Scenario"),
                "activation_label": st.column_config.TextColumn(
                    "Activation Link", width="large"
                ),
                "observer": st.column_config.TextColumn("Observer"),
                "sensitive": st.column_config.CheckboxColumn("Sensitive"),
                "summary": st.column_config.TextColumn("Summary", width="large"),
            },
            height=460,
            hide_index=True,
        )

        if file_summary.get("capture_error"):
            st.warning(file_summary["capture_error"])
    else:
        capture_error = file_summary.get("capture_error")
        if capture_error:
            st.warning(capture_error)
        else:
            st.info("No file telemetry captured in this report yet.")

# --- Tab 4: Performance Matrix ---
with tab_perf:
    p1, p2 = st.columns(2)

    with p1:
        st.markdown("### Latency Distribution")
        if not df.empty:
            lane_count = df["lane"].nunique()
            box_height = max(400, lane_count * 24)

            box = (
                alt.Chart(df)
                .mark_boxplot(extent="min-max", color="#8b5cf6", ticks=True)
                .encode(
                    x=alt.X(
                        "duration_ms",
                        scale=alt.Scale(type="log"),
                        title="Duration (ms, log scale)",
                        axis=alt.Axis(gridColor="#333"),
                    ),
                    y=alt.Y("lane", title=None, axis=alt.Axis(labelLimit=200)),
                    color=alt.Color(
                        "performance", scale=alt.Scale(scheme="spectral"), legend=None
                    ),
                    tooltip=["activation_event", "duration_ms"],
                )
                .properties(height=box_height)
            )
            st.altair_chart(box, theme="streamlit")

    with p2:
        st.markdown("### Startup Overheads")
        if running:
            df_run = pd.DataFrame(running)
            if "activation_time_ms" in df_run.columns:
                df_run = df_run.sort_values("activation_time_ms", ascending=False).head(
                    15
                )

                bar = (
                    alt.Chart(df_run)
                    .mark_bar(cornerRadiusEnd=4, color="#f43f5e")
                    .encode(
                        x=alt.X(
                            "activation_time_ms",
                            title="Load Time (ms)",
                            axis=alt.Axis(gridColor="#333"),
                        ),
                        y=alt.Y(
                            "extension_id",
                            sort="-x",
                            title=None,
                            axis=alt.Axis(labelLimit=200),
                        ),
                        color=alt.Color(
                            "activation_time_ms",
                            scale=alt.Scale(scheme="magma"),
                            legend=None,
                        ),
                        tooltip=["extension_id", "activation_time_ms"],
                    )
                    .properties(height=400)
                )
                st.altair_chart(bar, theme="streamlit")
        else:
            st.warning("No running extension metrics found.")

# --- Tab 4: Data Grid ---
with tab_grid:
    if not df.empty:
        c_filter, c_export = st.columns([4, 1])

        with c_filter:
            search_txt = st.text_input(
                "Search",
                placeholder="Filter by ID, Event, or Source...",
                label_visibility="collapsed",
            )

        df_view = df.copy()
        if search_txt:
            mask = (
                df_view["extension_id"].str.contains(search_txt, case=False, na=False)
                | df_view["activation_event"].str.contains(
                    search_txt, case=False, na=False
                )
                | df_view["source"].str.contains(search_txt, case=False, na=False)
            )
            df_view = df_view[mask]

        with c_export:
            st.download_button(
                "📥 Export CSV",
                df_view.to_csv(index=False).encode("utf-8"),
                "extrace_analysis.csv",
                "text/csv",
                key="download-csv",
            )

        st.dataframe(
            df_view[
                [
                    "dt",
                    "extension_id",
                    "activation_event",
                    "duration_ms",
                    "performance",
                    "source",
                    "lane",
                ]
            ],
            column_config={
                "dt": st.column_config.DatetimeColumn(
                    "Timestamp", format="HH:mm:ss.SS"
                ),
                "extension_id": st.column_config.TextColumn("Extension", width="large"),
                "activation_event": st.column_config.TextColumn("Trigger Flow (Event)"),
                "duration_ms": st.column_config.ProgressColumn(
                    "Duration", format="%d ms", min_value=0, max_value=1000
                ),
                "performance": st.column_config.TextColumn("Status"),
                "source": st.column_config.TextColumn("Source"),
                "lane": st.column_config.TextColumn("Lane", width="large"),
            },
            height=600,
            hide_index=True,
        )
    else:
        st.info("No table data available.")

# --- Tab 5: Raw Inspector ---
with tab_raw:
    st.markdown("### JSON Structure")
    st.json(raw_data, expanded=False)

# --- Tab 6: Extension Host Logs ---
with tab_host_logs:
    st.markdown("### Extension Host Output")
    eh_output = raw_data.get("extension_host_output", "")
    eh_lines = raw_data.get("extension_host_output_lines", 0)
    if eh_output:
        st.caption(f"{eh_lines} total lines (showing up to last 500)")
        with st.container(height=600):
            st.code(eh_output, language="log")
    else:
        st.info(
            "No Extension Host logs available in this report. "
            "Re-run the analysis to capture logs."
        )
