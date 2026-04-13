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


def render_section_intro(title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="section-intro">
            <h3>{title}</h3>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_card(title: str, value: str, tone: str = "default") -> str:
    return f"""
    <div class="info-card tone-{tone}">
        <div class="info-card-title">{title}</div>
        <div class="info-card-value">{value}</div>
    </div>
    """


def pill_row(items: list[str], tone: str = "default") -> str:
    if not items:
        items = ["(none)"]
    pills = "".join(f'<span class="pill tone-{tone}">{item}</span>' for item in items)
    return f'<div class="pill-row">{pills}</div>'


def metric_card(label: str, value: str, color: str, icon: str | None = None) -> str:
    icon_markup = (
        f'<div class="kpi-icon" style="color: {color}; border-color: {color}20; background: {color}10;">{icon}</div>'
        if icon
        else f'<div class="kpi-accent" style="background: linear-gradient(180deg, {color}, transparent);"></div>'
    )
    return f"""
    <div class="glass-card">
        <div class="kpi-label">
            {icon_markup}
            {label}
        </div>
        <div class="kpi-value">{value}</div>
    </div>
    """
