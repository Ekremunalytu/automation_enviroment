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

    # Convert timestamps
    if "timestamp" in df.columns:
        # Handle both ISO format strings and UNIX timestamps
        df["dt"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # If all are NaT, it might be that they were UNIX timestamps treated as nanoseconds
        # But getting UNIX timestamps as "seconds" is common.
        # If we want to support UNIX seconds, we might need a check.
        # However, the current data is clearly ISO string.
        # If we want to be safe for UNIX seconds as well:
        mask_nat = df["dt"].isna() & df["timestamp"].notna() & (df["timestamp"] != "")
        if mask_nat.any():
            # Try parsing as numeric seconds for failed ones
            numeric_ts = pd.to_numeric(df.loc[mask_nat, "timestamp"], errors="coerce")
            df.loc[mask_nat, "dt"] = pd.to_datetime(numeric_ts, unit="s")

    # Calculate relative timing
    if "dt" in df.columns and not df.empty:
        start_time = df["dt"].min()
        df["rel_start"] = (df["dt"] - start_time).dt.total_seconds()
        df["duration_ms"] = df.get("duration_ms", 0).fillna(50)
        df["rel_end"] = df["rel_start"] + (df["duration_ms"] / 1000)

        # Categorize durations
        df["performance"] = pd.cut(
            df["duration_ms"],
            bins=[-1, 50, 200, 1000, 999999],
            labels=["⚡ Instant", "✅ Fast", "⚠️ Slow", "🔥 Critical"],
        )

    return df


# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------

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

    reports = fetch_report_list()

    if reports:
        report_map = {r["filename"]: r for r in reports}
        opts = ["(Latest Report)", *list(report_map.keys())]
        selection = st.selectbox("Select Analysis Session", opts)

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
        target = None

    st.markdown("### View Options")
    chart_theme = st.select_slider(
        "Color Palette", options=["turbo", "plasma", "inferno", "magma"], value="plasma"
    )

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

if not target:
    st.markdown(
        "<div style='text-align: center; margin-top: 20vh; color: #52525b;'>Waiting for analysis data...</div>",
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

# ---------------------------------------------------------------------------
# Dashboard Header
# ---------------------------------------------------------------------------

col_header, col_status = st.columns([3, 1])

with col_header:
    st.markdown(
        f"""
        <h1 style="font-size: 2.5rem; margin-bottom: 0;">
            Analysis <span class="gradient-text">Dashboard</span>
        </h1>
        <p style="color: #a1a1aa; margin-top: 4px;">
            Target: <code style="background:transparent; color: #8b5cf6;">{raw_data.get("_metadata", {}).get("filename", "Unknown")}</code>
        </p>
        """,
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

tab_viz, tab_perf, tab_grid, tab_raw = st.tabs(
    [
        "📊 Visual Intelligence",
        "⚡ Performance Matrix",
        "💾 Data Grid",
        "🔍 Raw Inspector",
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
                .properties(height=400, width="container")
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

            st.altair_chart(chart & hist, use_container_width=True, theme="streamlit")

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

            st.altair_chart(pie, use_container_width=True, theme="streamlit")
    else:
        st.info("No activation data to visualize.")

# --- Tab 2: Performance Matrix ---
with tab_perf:
    p1, p2 = st.columns(2)

    with p1:
        st.markdown("### Latency Distribution")
        if not df.empty:
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
                .properties(height=400)
            )
            st.altair_chart(box, use_container_width=True, theme="streamlit")

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
                st.altair_chart(bar, use_container_width=True, theme="streamlit")
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
                use_container_width=True,
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
                "activation_event": st.column_config.TextColumn("Event Type"),
                "duration_ms": st.column_config.ProgressColumn(
                    "Duration", format="%d ms", min_value=0, max_value=1000
                ),
                "performance": st.column_config.TextColumn("Status"),
                "source": st.column_config.TextColumn("Source"),
            },
            use_container_width=True,
            height=600,
            hide_index=True,
        )
    else:
        st.info("No table data available.")

# --- Tab 4: Raw Inspector ---
with tab_raw:
    st.markdown("### JSON Structure")
    st.json(raw_data, expanded=False)
