"""Reusable UI components."""

from __future__ import annotations

import streamlit as st


def render_page_hero(title: str, highlight: str, description: str) -> None:
    st.markdown(
        f"""
        <h1 style="font-size: 2.5rem; margin-bottom: 0;">
            {title} <span class="gradient-text">{highlight}</span>
        </h1>
        <p style="color: #a1a1aa; margin-top: 4px;">
            {description}
        </p>
        """,
        unsafe_allow_html=True,
    )


def render_spacer(height: int = 24) -> None:
    st.markdown(f"<div style='height: {height}px'></div>", unsafe_allow_html=True)


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
