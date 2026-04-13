"""Marketplace page renderer."""

from __future__ import annotations

import streamlit as st
from api import download_extension, search_marketplace
from components import render_page_hero, render_spacer


def _queue_scan(publisher: str, name: str, version: str) -> None:
    st.session_state["scan_request"] = {
        "publisher": publisher,
        "name": name,
        "version": version,
    }
    st.session_state["pending_nav_page"] = "Simulation"


def render_marketplace_page() -> None:
    render_page_hero(
        "VS Code",
        "Marketplace",
        "Search, download, and statically analyze extensions from the Marketplace.",
    )
    render_spacer()

    with st.form("marketplace_search_form"):
        col_query, col_button = st.columns([4, 1])
        with col_query:
            query = st.text_input(
                "Search",
                placeholder="e.g. python, prettier, eslint",
                label_visibility="collapsed",
            )
        with col_button:
            submitted = st.form_submit_button("Search", use_container_width=True)

    if submitted and query.strip():
        with st.spinner("Searching Marketplace..."):
            search_results, error = search_marketplace(query.strip())
        if error:
            st.error(error)
            search_results = []
        st.session_state["marketplace_results"] = search_results

    marketplace_results: list[dict] = st.session_state.get("marketplace_results", [])
    if not marketplace_results:
        if submitted:
            st.info("No results found.")
        return

    st.markdown(f"### Results ({len(marketplace_results)})")

    for extension in marketplace_results:
        publisher = extension.get("publisher", "")
        name = extension.get("name", "")
        version = extension.get("version", "")
        display_name = extension.get("displayName", name)
        description = extension.get("description", "")
        installs = extension.get("installs", 0)
        rating = extension.get("rating", 0.0)

        col_info, col_action = st.columns([5, 1.2], vertical_alignment="center")
        with col_info:
            action_state = (
                "Ready to analyze"
                if st.session_state.get(
                    f"downloaded_{publisher}_{name}_{version}", False
                )
                else "Marketplace"
            )
            st.markdown(
                f"""
                <div class="glass-card" style="
                    margin-bottom: 12px;
                    min-height: 152px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                ">
                    <div>
                        <div style="
                            display: flex;
                            justify-content: space-between;
                            gap: 12px;
                            align-items: flex-start;
                        ">
                            <div style="
                                font-size: 1.1rem;
                                font-weight: 700;
                                color: #f4f4f5;
                            ">
                                {display_name}
                            </div>
                            <div style="
                                padding: 4px 10px;
                                border-radius: 999px;
                                border: 1px solid rgba(34, 211, 238, 0.25);
                                color: #22d3ee;
                                background: rgba(34, 211, 238, 0.08);
                                font-size: 0.72rem;
                                letter-spacing: 0.05em;
                                text-transform: uppercase;
                            ">
                                {action_state}
                            </div>
                        </div>
                        <div style="
                            font-size: 0.78rem;
                            color: #a1a1aa;
                            margin: 8px 0 10px 0;
                        ">
                            <code style="color: #8b5cf6;">{publisher}.{name}</code>
                        </div>
                        <div style="
                            font-size: 0.9rem;
                            color: #d4d4d8;
                            line-height: 1.5;
                        ">{description}</div>
                    </div>
                    <div style="
                        display: flex;
                        flex-wrap: wrap;
                        gap: 8px;
                        margin-top: 16px;
                    ">
                        <div style="
                            padding: 5px 10px;
                            border-radius: 999px;
                            background: rgba(139, 92, 246, 0.12);
                            border: 1px solid rgba(139, 92, 246, 0.25);
                            color: #c4b5fd;
                            font-size: 0.76rem;
                        ">
                            v{version}
                        </div>
                        <div style="
                            padding: 5px 10px;
                            border-radius: 999px;
                            background: rgba(6, 182, 212, 0.12);
                            border: 1px solid rgba(6, 182, 212, 0.25);
                            color: #67e8f9;
                            font-size: 0.76rem;
                        ">
                            ⬇ {installs:,}
                        </div>
                        <div style="
                            padding: 5px 10px;
                            border-radius: 999px;
                            background: rgba(245, 158, 11, 0.12);
                            border: 1px solid rgba(245, 158, 11, 0.25);
                            color: #fcd34d;
                            font-size: 0.76rem;
                        ">
                            ★ {rating:.1f}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_action:
            extension_key = f"{publisher}_{name}_{version}"
            downloaded = st.session_state.get(f"downloaded_{extension_key}", False)
            if not downloaded:
                if st.button(
                    "Download", key=f"dl_{extension_key}", use_container_width=True
                ):
                    with st.spinner(f"Downloading {name}..."):
                        result, error = download_extension(publisher, name, version)
                    if error:
                        st.error(error)
                    elif result:
                        st.session_state[f"downloaded_{extension_key}"] = True
                        if result.get("status") == "already_exists":
                            st.info("Extension already downloaded and registered.")
                            st.success("Ready to analyze!")
                        else:
                            st.success(f"Downloaded! DB ID: {result.get('db_id')}")
                        st.rerun()
            else:
                st.button(
                    "Analyze",
                    key=f"az_{extension_key}",
                    use_container_width=True,
                    on_click=_queue_scan,
                    args=(publisher, name, version),
                )
