"""
ExTrace UI — Extension Activation Dashboard
=============================================

Streamlit dashboard for visualizing VS Code extension activation events
captured during dynamic analysis in the executor container.

Data source: FastAPI activation reports API (/api/activations)
"""

import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
API_ACTIVATIONS_URL = f"{API_BASE_URL}/api/activations"

# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="ExTrace — Activation Dashboard",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
    /* Global */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #21262d 0%, #161b22 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetric"] label {
        color: #8b949e !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #e6edf3 !important;
        font-weight: 700 !important;
    }

    /* Dataframe styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #0d1117;
        border-right: 1px solid #21262d;
    }

    /* Headers */
    h1, h2, h3 {
        color: #e6edf3 !important;
    }

    /* Status badges */
    .status-active {
        background: #238636;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-inactive {
        background: #6e7681;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
    }

    /* Info boxes */
    .ext-card {
        background: #21262d;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 8px;
    }

    /* Purple accent */
    .stSelectbox label, .stRadio label {
        color: #c9d1d9 !important;
    }

    div[data-testid="stMetricDelta"] svg {
        display: none;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# API Client
# ---------------------------------------------------------------------------


@st.cache_data(ttl=10)
def fetch_report_list() -> list[dict]:
    """Fetch available activation reports from the API."""
    try:
        resp = requests.get(API_ACTIVATIONS_URL, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"API connection error: {e}")
        return []


@st.cache_data(ttl=10)
def fetch_report(filename: str) -> dict | None:
    """Fetch a specific activation report by filename."""
    try:
        resp = requests.get(f"{API_ACTIVATIONS_URL}/{filename}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"Failed to load report ({filename}): {e}")
        return None


@st.cache_data(ttl=10)
def fetch_latest_report() -> dict | None:
    """Fetch the latest activation report."""
    try:
        resp = requests.get(f"{API_ACTIVATIONS_URL}/latest", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"Failed to load latest report: {e}")
        return None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🔮 ExTrace")
    st.markdown("**Extension Activation Dashboard**")
    st.divider()

    # Report selector
    reports = fetch_report_list()

    if reports:
        report_names = [r["filename"] for r in reports]

        selected_report = st.selectbox(
            "📄 Select Report",
            options=["(Latest Report)", *report_names],
            index=0,
        )

        st.divider()
        st.markdown("### 📂 Available Reports")
        for r in reports:
            size_kb = r["size_bytes"] / 1024
            mod_time = datetime.fromtimestamp(r["modified"]).strftime("%Y-%m-%d %H:%M")
            st.markdown(
                f"- **{r['filename']}**  \n" f"  `{size_kb:.1f} KB` · `{mod_time}`"
            )
    else:
        selected_report = None
        st.warning("No reports found yet.")
        st.markdown(
            "Run automation in the executor container to generate reports:\n"
            "```bash\n"
            "make exec-run\n"
            "```"
        )

    st.divider()
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ---------------------------------------------------------------------------
# Main Content
# ---------------------------------------------------------------------------

st.markdown("# 🔮 ExTrace — Activation Dashboard")
st.markdown("Visualize Extension Host process activation events")

if not reports:
    st.info(
        "📭 No activation reports found. "
        "Run automation with `--monitor` flag in the executor container "
        "to generate reports."
    )
    st.code(
        "docker exec -e PYTHONUNBUFFERED=1 automation_executor "
        "python3 /home/executor/playwright/entrypoint.py --monitor",
        language="bash",
    )
    st.stop()

# Load report data
if selected_report == "(Latest Report)":
    report = fetch_latest_report()
else:
    report = fetch_report(selected_report) if selected_report else None

if not report:
    st.error("Failed to load report.")
    st.stop()

summary = report.get("summary", {})
activated = report.get("activated", [])
running = report.get("running_extensions", [])
metadata = report.get("_metadata", {})

# ---------------------------------------------------------------------------
# Summary Metrics
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("### 📊 Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Activations",
        value=summary.get("total_activated", len(activated)),
    )

with col2:
    st.metric(
        label="Unique Extensions",
        value=summary.get("unique_extensions", 0),
    )

with col3:
    st.metric(
        label="Running Extensions",
        value=summary.get("running_extensions", len(running)),
    )

with col4:
    duration = summary.get("monitoring_duration_s", 0)
    if duration:
        mins = int(duration // 60)
        secs = int(duration % 60)
        st.metric(
            label="Monitoring Duration",
            value=f"{mins}m {secs}s",
        )
    else:
        st.metric(label="Monitoring Duration", value="—")

# Report file info
if metadata.get("filename"):
    st.caption(f"📄 Report: `{metadata['filename']}`")

# ---------------------------------------------------------------------------
# Activated Extensions
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("### ⚡ Activated Extensions")

if activated:
    df_activated = pd.DataFrame(activated)

    # Column renaming for display
    column_map = {
        "extension_id": "Extension ID",
        "activation_event": "Activation Event",
        "timestamp": "Timestamp",
        "duration_ms": "Duration (ms)",
        "source": "Source",
    }
    display_cols = [c for c in column_map if c in df_activated.columns]
    df_display = df_activated[display_cols].rename(columns=column_map)

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Extension ID": st.column_config.TextColumn("Extension ID", width="large"),
            "Activation Event": st.column_config.TextColumn(
                "Activation Event", width="medium"
            ),
            "Duration (ms)": st.column_config.NumberColumn(
                "Duration (ms)", format="%d"
            ),
            "Source": st.column_config.TextColumn("Source", width="small"),
        },
    )

    # Activation event distribution
    st.markdown("#### 🎯 Activation Event Distribution")
    if "activation_event" in df_activated.columns:
        event_counts = df_activated["activation_event"].value_counts().reset_index()
        event_counts.columns = ["Activation Event", "Count"]
        st.bar_chart(
            event_counts.set_index("Activation Event"),
            color="#a855f7",
        )

    # Source distribution
    if "source" in df_activated.columns:
        col_src1, col_src2 = st.columns(2)
        with col_src1:
            st.markdown("#### 📡 Source Distribution")
            source_counts = df_activated["source"].value_counts().reset_index()
            source_counts.columns = ["Source", "Count"]
            st.dataframe(source_counts, use_container_width=True, hide_index=True)

        with col_src2:
            st.markdown("#### 🆔 Extension ID List")
            ext_ids = sorted(df_activated["extension_id"].unique().tolist())
            for ext_id in ext_ids:
                st.markdown(f"- `{ext_id}`")
else:
    st.info("No activated extensions found in this report.")

# ---------------------------------------------------------------------------
# Running Extensions
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("### 🏃 Running Extensions")

if running:
    df_running = pd.DataFrame(running)

    column_map_running = {
        "extension_id": "Extension ID",
        "name": "Name",
        "activation_time_ms": "Activation Time (ms)",
        "status": "Status",
    }
    display_cols_running = [c for c in column_map_running if c in df_running.columns]
    df_running_display = df_running[display_cols_running].rename(
        columns=column_map_running
    )

    st.dataframe(
        df_running_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Extension ID": st.column_config.TextColumn("Extension ID", width="large"),
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Activation Time (ms)": st.column_config.NumberColumn(
                "Activation Time (ms)", format="%d ms"
            ),
        },
    )

    # Performance chart
    if "activation_time_ms" in df_running.columns:
        st.markdown("#### ⏱️ Activation Times")
        perf_data = df_running[["extension_id", "activation_time_ms"]].copy()
        perf_data = perf_data.dropna(subset=["activation_time_ms"])
        perf_data = perf_data.sort_values("activation_time_ms", ascending=False)
        if not perf_data.empty:
            st.bar_chart(
                perf_data.set_index("extension_id"),
                color="#22c55e",
            )
else:
    st.info("No running extension data found in this report.")

# ---------------------------------------------------------------------------
# Extension IDs (from summary)
# ---------------------------------------------------------------------------

extension_ids = summary.get("extension_ids", [])
if extension_ids:
    st.markdown("---")
    with st.expander(f"📦 All Extension IDs ({len(extension_ids)})", expanded=False):
        for ext_id in sorted(extension_ids):
            st.code(ext_id, language=None)

# ---------------------------------------------------------------------------
# Raw JSON
# ---------------------------------------------------------------------------

st.markdown("---")
with st.expander("🔍 Raw JSON Data", expanded=False):
    st.json(report)
