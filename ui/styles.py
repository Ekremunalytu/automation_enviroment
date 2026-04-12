"""Global page configuration and styling."""

from __future__ import annotations

import streamlit as st

GLOBAL_STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&family=Outfit:wght@400;600;800&display=swap');

    :root {
        --bg-color: #050505;
        --card-bg: rgba(255, 255, 255, 0.03);
        --card-border: rgba(255, 255, 255, 0.06);
        --accent-primary: #8b5cf6;
        --accent-secondary: #06b6d4;
        --accent-glow: rgba(139, 92, 246, 0.5);
        --text-primary: #f4f4f5;
        --text-secondary: #a1a1aa;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
    }

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

    section[data-testid="stSidebar"] {
        background-color: rgba(10, 10, 10, 0.8);
        border-right: 1px solid var(--card-border);
        backdrop-filter: blur(20px);
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    .stAppDeployButton,
    [data-testid="stDecoration"] {
        display: none !important;
    }

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
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.1),
            transparent
        );
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
        background: rgba(255, 255, 255, 0.05);
        color: var(--text-primary);
        font-size: 1.1rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

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

    .stButton > button {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--card-border);
        color: var(--text-primary);
        border-radius: 8px;
        transition: all 0.2s;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
    }

    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: var(--text-primary);
    }

    div[data-testid="stDataFrame"] {
        background: transparent;
        border: 1px solid var(--card-border);
        border-radius: 12px;
    }

    .gradient-text {
        background: linear-gradient(135deg, #a78bfa 0%, #22d3ee 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.3));
    }

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
"""


def configure_page() -> None:
    st.set_page_config(
        page_title="ExTrace Intelligence",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def apply_global_styles() -> None:
    st.markdown(GLOBAL_STYLES, unsafe_allow_html=True)
