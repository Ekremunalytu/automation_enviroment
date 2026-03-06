"""
ExTrace Intelligence Suite
==========================

Advanced Analytics Dashboard for VS Code Extension Security.
"""

import os
from datetime import datetime

import altair as alt
import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
API_ACTIVATIONS_URL = f"{API_BASE_URL}/api/activations"
API_MARKETPLACE_SEARCH_URL = f"{API_BASE_URL}/api/marketplace/search"
API_MARKETPLACE_DOWNLOAD_URL = f"{API_BASE_URL}/api/marketplace/download"
API_MARKETPLACE_ANALYZE_URL = f"{API_BASE_URL}/api/marketplace/analyze"

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


@st.cache_data(ttl=5)
def fetch_report_list() -> list[dict]:
    try:
        resp = requests.get(API_ACTIVATIONS_URL, timeout=2)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


@st.cache_data(ttl=15)
def fetch_report(filename: str) -> dict:
    url = (
        f"{API_ACTIVATIONS_URL}/latest"
        if filename == "latest"
        else f"{API_ACTIVATIONS_URL}/{filename}"
    )
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Error loading report: {e}")
        return {}


def process_data(data: dict) -> pd.DataFrame:
    activated = data.get("activated", [])
    if not activated:
        return pd.DataFrame()

    df = pd.DataFrame(activated)

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

    # Calculate relative timing
    if has_valid_timestamps:
        start_time = df["dt"].min()
        df["rel_start"] = (df["dt"] - start_time).dt.total_seconds()
    else:
        # No valid timestamps: build a synthetic timeline from cumulative durations
        df["dt"] = pd.Timestamp.now()
        cumulative = df["duration_ms"].cumsum().shift(fill_value=0)
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

    return df


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
            results = search_marketplace(query.strip())
        st.session_state["marketplace_results"] = results

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

        c_info, c_btn = st.columns([5, 1])
        with c_info:
            st.markdown(
                f"""
                <div class="glass-card" style="margin-bottom: 8px;">
                    <div style="font-size: 1.05rem; font-weight: 700; color: #f4f4f5;">
                        {display}
                    </div>
                    <div style="font-size: 0.78rem; color: #a1a1aa; margin: 4px 0;">
                        <code style="color: #8b5cf6;">{pub}.{ext_name}</code>
                        &nbsp;·&nbsp; v{ver}
                        &nbsp;·&nbsp; ⬇ {installs:,}
                        &nbsp;·&nbsp; ★ {rating:.1f}
                    </div>
                    <div style="font-size: 0.85rem; color: #71717a;">{desc}</div>
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
                    st.session_state["nav_page"] = "Dashboard"

                st.button(
                    "Analyze",
                    key=analyze_key,
                    use_container_width=True,
                    on_click=_start_scan,
                )


# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------

# Defaults (overridden inside sidebar when page == "Dashboard")
target = None
chart_theme = "plasma"

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
        ["Dashboard", "Marketplace", "Theme"],
        key="nav_page",
        label_visibility="collapsed",
    )

    st.markdown("---")

    if page == "Dashboard":
        reports = fetch_report_list()

        if reports:
            report_map = {r["filename"]: r for r in reports}
            opts = ["(Latest Report)", *list(report_map.keys())]

            # If we just finished an analysis, auto-select that report
            pending = st.session_state.pop("pending_report", None)
            default_idx = 0
            if pending and pending in report_map:
                default_idx = opts.index(pending)

            selection = st.selectbox("Select Analysis Session", opts, index=default_idx)

            if selection == "(Latest Report)":
                target = "latest"
                meta = reports[0]
            else:
                target = selection
                meta = report_map[selection]

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

# ---------------------------------------------------------------------------
# Live Scan Execution (triggered from Marketplace → Analyze)
# ---------------------------------------------------------------------------

scan_req = st.session_state.pop("scan_request", None)
if scan_req:
    _pub = scan_req["publisher"]
    _name = scan_req["name"]
    _ver = scan_req["version"]
    _ext_id = f"{_pub}.{_name}@{_ver}"

    with st.status(f"Scanning {_ext_id}...", expanded=True) as scan_status:
        scan_status.update(label=f"Scanning {_ext_id}...", state="running")

        st.write("**1/3** — Installing extension in sandbox...")
        st.caption("Running `code --install-extension` inside executor container")

        st.write("**2/3** — Running Playwright automation...")
        st.caption("Executing scenarios, monitoring activations & network traffic")

        az_result = analyze_extension(_pub, _name, _ver)

        if az_result:
            st.write("**3/3** — Collecting results...")
            report_file = az_result.get("report_path", "")
            scan_status.update(label=f"Scan complete — {_ext_id}", state="complete")
            st.session_state["last_scan_logs"] = {
                "install_output": az_result.get("install_output", ""),
                "automation_output": az_result.get("automation_output", ""),
                "extension": f"{_pub}.{_name}",
            }
            st.cache_data.clear()
            # Force the sidebar to pick up the new report on next rerun
            st.session_state["pending_report"] = report_file
            st.rerun()
        else:
            scan_status.update(label=f"Scan failed — {_ext_id}", state="error")
            st.stop()

# Show last scan logs on Dashboard if available
_scan_logs = st.session_state.get("last_scan_logs")
if _scan_logs:
    with st.expander(f"Last Scan Logs — `{_scan_logs['extension']}`", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.caption("Install Output")
            st.code(
                _scan_logs.get("install_output") or "(no output)",
                language="text",
            )
        with col_b:
            st.caption("Automation Output")
            st.code(
                _scan_logs.get("automation_output") or "(no output)",
                language="text",
            )
    if st.button("Clear logs", key="clear_scan_logs"):
        st.session_state.pop("last_scan_logs", None)
        st.rerun()
    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

if not target:
    st.markdown(
        "<div style='text-align: center; margin-top: 20vh; color: #52525b;'>"
        "Waiting for analysis data...</div>",
        unsafe_allow_html=True,
    )
    st.stop()

raw_data = fetch_report(target)
if not raw_data:
    st.error("Failed to load report data.")
    st.stop()

df = process_data(raw_data)
summary = raw_data.get("summary", {})
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

k1, k2, k3, k4 = st.columns(4)


def metric_card(icon, label, value, color):
    return f"""
    <div class="glass-card">
        <div class="kpi-label">
            <div class="kpi-icon" style="color: {color}; border-color: {color}20; background: {color}10;">{icon}</div>
            {label}
        </div>
        <div class="kpi-value">{value}</div>
    </div>
    """


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
        metric_card("🚀", "Active Processes", str(len(running)), "#10b981"),
        unsafe_allow_html=True,
    )
with k4:
    dur = summary.get("monitoring_duration_s", 0)
    st.markdown(
        metric_card("⏱️", "Duration", f"{dur:.1f}s", "#f59e0b"), unsafe_allow_html=True
    )

st.markdown("<div style='height: 48px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Deep Dive Analysis
# ---------------------------------------------------------------------------

tab_viz, tab_perf, tab_grid, tab_raw, tab_host_logs = st.tabs(
    [
        "📊 Visual Intelligence",
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
            unique_ext_count = df["extension_id"].nunique() if not df.empty else 10
            chart_height = max(400, unique_ext_count * 25)

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
                        "extension_id",
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

# --- Tab 2: Performance Matrix ---
with tab_perf:
    p1, p2 = st.columns(2)

    with p1:
        st.markdown("### Latency Distribution")
        if not df.empty:
            unique_ext_count = df["extension_id"].nunique()
            box_height = max(400, unique_ext_count * 25)

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
                    y=alt.Y(
                        "activation_event", title=None, axis=alt.Axis(labelLimit=200)
                    ),
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

# --- Tab 3: Data Grid ---
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
            mask = df_view["extension_id"].str.contains(
                search_txt, case=False, na=False
            ) | df_view["activation_event"].str.contains(
                search_txt, case=False, na=False
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
            },
            height=600,
            hide_index=True,
        )
    else:
        st.info("No table data available.")

# --- Tab 4: Raw Inspector ---
with tab_raw:
    st.markdown("### JSON Structure")
    st.json(raw_data, expanded=False)

# --- Tab 5: Extension Host Logs ---
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
