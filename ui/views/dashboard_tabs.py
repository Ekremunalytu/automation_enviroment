"""Dashboard tab renderers."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
from components import metric_card
from data_processing import (
    build_file_log,
    build_network_log,
    filter_dataframe,
    to_csv_bytes,
)

FILE_SOURCE_DOMAIN = ["Automation", "Extension", "System", "Unknown"]
FILE_SOURCE_RANGE = ["#8b5cf6", "#f59e0b", "#64748b", "#22d3ee"]


def render_visual_tab(df: pd.DataFrame, chart_theme: str) -> None:
    if df.empty:
        st.info("No activation data to visualize.")
        return

    col_chart, col_distribution = st.columns([2, 1])
    with col_chart:
        st.markdown("### Activity Pulse")
        brush = alt.selection_interval(encodings=["x"])
        lane_count = df["lane"].nunique()
        chart_height = max(400, lane_count * 24)
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
                    "lane", title=None, axis=alt.Axis(labelLimit=200, gridColor="#333")
                ),
                color=alt.Color(
                    "activation_event", scale=alt.Scale(scheme=chart_theme), legend=None
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
                x=alt.X("rel_start", bin=alt.Bin(maxbins=50), title=None, axis=None),
                y=alt.Y("count()", title=None, axis=None),
            )
            .properties(height=60, width="container")
            .transform_filter(brush)
        )
        st.altair_chart(chart & hist, theme="streamlit")

    with col_distribution:
        st.markdown("### Distribution")
        pie = (
            alt.Chart(df)
            .mark_arc(innerRadius=80, cornerRadius=6, stroke="#050505", strokeWidth=2)
            .encode(
                theta=alt.Theta("count()"),
                color=alt.Color(
                    "activation_event",
                    scale=alt.Scale(scheme=chart_theme),
                    legend=alt.Legend(orient="bottom", columns=1, labelColor="#a1a1aa"),
                ),
                order=alt.Order("count()", sort="descending"),
                tooltip=["activation_event", "count()"],
            )
            .properties(height=480)
        )
        st.altair_chart(pie, theme="streamlit")


def render_network_tab(
    network_df: pd.DataFrame,
    network_summary: dict,
    chart_theme: str,
) -> None:
    if network_df.empty:
        capture_error = network_summary.get("capture_error")
        if capture_error:
            st.warning(capture_error)
        else:
            st.info("No network telemetry captured in this report yet.")
        return

    col_timeline, col_breakdown = st.columns([2, 1])
    with col_timeline:
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
                    "lane", title=None, axis=alt.Axis(labelLimit=220, gridColor="#333")
                ),
                color=alt.Color(
                    "event_label", scale=alt.Scale(scheme=chart_theme), legend=None
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
                        alt.GradientStop(color="rgba(34, 211, 238, 0.08)", offset=1),
                    ],
                    x1=1,
                    x2=1,
                    y1=1,
                    y2=0,
                ),
            )
            .encode(
                x=alt.X("rel_time_s", bin=alt.Bin(maxbins=40), title=None, axis=None),
                y=alt.Y("count()", title=None, axis=None),
            )
            .properties(height=60, width="container")
        )
        st.altair_chart(timeline & density, theme="streamlit")

    with col_breakdown:
        st.markdown("### Traffic Breakdown")
        distribution = (
            alt.Chart(network_df)
            .mark_arc(innerRadius=80, cornerRadius=6, stroke="#050505", strokeWidth=2)
            .encode(
                theta=alt.Theta("count()"),
                color=alt.Color(
                    "event_label",
                    scale=alt.Scale(scheme=chart_theme),
                    legend=alt.Legend(orient="bottom", columns=1, labelColor="#a1a1aa"),
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
                x=alt.X("events:Q", title="Events", axis=alt.Axis(gridColor="#333")),
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
    with st.container(height=260):
        st.code(build_network_log(network_df) or "(no live events yet)", language="log")

    st.markdown("### Network Grid")
    search_text = st.text_input(
        "Network search",
        placeholder="Filter by host, protocol, summary, or IP...",
        label_visibility="collapsed",
    )
    network_view = filter_dataframe(
        network_df,
        search_text,
        ["host_display", "protocol_label", "summary", "source_ip", "destination_ip"],
    )
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
            "dt": st.column_config.DatetimeColumn("Timestamp", format="HH:mm:ss.SS"),
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


def render_file_tab(file_df: pd.DataFrame, file_summary: dict) -> None:
    if file_df.empty:
        capture_error = file_summary.get("capture_error")
        if capture_error:
            st.warning(capture_error)
        else:
            st.info("No file telemetry captured in this report yet.")
        return

    stats = st.columns(4)
    with stats[0]:
        st.markdown(
            metric_card(
                "🗂️",
                "File Events",
                str(file_summary.get("total_events", len(file_df))),
                "#22d3ee",
            ),
            unsafe_allow_html=True,
        )
    with stats[1]:
        st.markdown(
            metric_card(
                "🛡️",
                "Sensitive Hits",
                str(
                    file_summary.get(
                        "sensitive_events", int(file_df["sensitive"].sum())
                    )
                ),
                "#f43f5e",
            ),
            unsafe_allow_html=True,
        )
    with stats[2]:
        st.markdown(
            metric_card(
                "🧭",
                "Automation I/O",
                str((file_df["source"] == "automation").sum()),
                "#8b5cf6",
            ),
            unsafe_allow_html=True,
        )
    with stats[3]:
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
    col_timeline, col_mix = st.columns([2, 1])
    with col_timeline:
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
                    "lane", title=None, axis=alt.Axis(labelLimit=220, gridColor="#333")
                ),
                color=alt.Color(
                    "source_label",
                    scale=alt.Scale(domain=FILE_SOURCE_DOMAIN, range=FILE_SOURCE_RANGE),
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

    with col_mix:
        st.markdown("### Attribution Mix")
        source_mix = (
            alt.Chart(file_df)
            .mark_arc(innerRadius=80, cornerRadius=6, stroke="#050505", strokeWidth=2)
            .encode(
                theta=alt.Theta("count()"),
                color=alt.Color(
                    "source_label",
                    scale=alt.Scale(domain=FILE_SOURCE_DOMAIN, range=FILE_SOURCE_RANGE),
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
                x=alt.X("events:Q", title="Events", axis=alt.Axis(gridColor="#333")),
                y=alt.Y(
                    "operation_label:N",
                    sort="-x",
                    title=None,
                    axis=alt.Axis(labelLimit=160),
                ),
                color=alt.Color(
                    "source_label:N",
                    scale=alt.Scale(domain=FILE_SOURCE_DOMAIN, range=FILE_SOURCE_RANGE),
                    legend=None,
                ),
                tooltip=["operation_label", "source_label", "events"],
            )
            .properties(height=260)
        )
        st.altair_chart(matrix, theme="streamlit")

    col_sensitive, col_correlation = st.columns(2)
    with col_sensitive:
        st.markdown("### Sensitive Access Map")
        sensitive_df = file_df[file_df["sensitive"]].copy()
        if sensitive_df.empty:
            st.info("No sensitive file access observed in this report.")
        else:
            sensitive_chart = (
                alt.Chart(
                    sensitive_df.groupby(["path_short", "source_label"], dropna=False)
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
                            domain=FILE_SOURCE_DOMAIN, range=FILE_SOURCE_RANGE
                        ),
                        legend=None,
                    ),
                    tooltip=["path_short", "source_label", "events"],
                )
                .properties(height=300)
            )
            st.altair_chart(sensitive_chart, theme="streamlit")

    with col_correlation:
        st.markdown("### Activation Correlation")
        linked_df = file_df[
            file_df["related_extension_id"].fillna("").ne("")
            | file_df["related_activation_event"].fillna("").ne("")
        ].copy()
        if linked_df.empty:
            st.info("No file events could be linked to activation records yet.")
        else:
            correlation = (
                alt.Chart(
                    linked_df.groupby(
                        ["activation_label", "source_label"], dropna=False
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
                            domain=FILE_SOURCE_DOMAIN, range=FILE_SOURCE_RANGE
                        ),
                        legend=None,
                    ),
                    tooltip=["activation_label", "source_label", "events"],
                )
                .properties(height=300)
            )
            st.altair_chart(correlation, theme="streamlit")

    st.markdown("### File Event Log")
    with st.container(height=260):
        st.code(build_file_log(file_df) or "(no file events yet)", language="log")

    st.markdown("### File I/O Grid")
    search_text = st.text_input(
        "File search",
        placeholder="Filter by path, source, scenario, activation, or summary...",
        label_visibility="collapsed",
    )
    file_view = filter_dataframe(
        file_df,
        search_text,
        ["path", "source_label", "scenario_label", "activation_label", "summary"],
    )
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
            "dt": st.column_config.DatetimeColumn("Timestamp", format="HH:mm:ss.SS"),
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


def render_performance_tab(df: pd.DataFrame, running: list[dict]) -> None:
    col_latency, col_overhead = st.columns(2)
    with col_latency:
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

    with col_overhead:
        st.markdown("### Startup Overheads")
        if not running:
            st.warning("No running extension metrics found.")
            return

        running_df = pd.DataFrame(running)
        if "activation_time_ms" not in running_df.columns:
            st.warning("No running extension metrics found.")
            return

        running_df = running_df.sort_values("activation_time_ms", ascending=False).head(
            15
        )
        bar = (
            alt.Chart(running_df)
            .mark_bar(cornerRadiusEnd=4, color="#f43f5e")
            .encode(
                x=alt.X(
                    "activation_time_ms",
                    title="Load Time (ms)",
                    axis=alt.Axis(gridColor="#333"),
                ),
                y=alt.Y(
                    "extension_id", sort="-x", title=None, axis=alt.Axis(labelLimit=200)
                ),
                color=alt.Color(
                    "activation_time_ms", scale=alt.Scale(scheme="magma"), legend=None
                ),
                tooltip=["extension_id", "activation_time_ms"],
            )
            .properties(height=400)
        )
        st.altair_chart(bar, theme="streamlit")


def render_grid_tab(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No table data available.")
        return

    col_filter, col_export = st.columns([4, 1])
    with col_filter:
        search_text = st.text_input(
            "Search",
            placeholder="Filter by ID, Event, or Source...",
            label_visibility="collapsed",
        )
    df_view = filter_dataframe(
        df, search_text, ["extension_id", "activation_event", "source"]
    )

    with col_export:
        st.download_button(
            "📥 Export CSV",
            to_csv_bytes(df_view),
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
            "dt": st.column_config.DatetimeColumn("Timestamp", format="HH:mm:ss.SS"),
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


def render_raw_tab(raw_data: dict) -> None:
    st.markdown("### JSON Structure")
    st.json(raw_data, expanded=False)


def render_host_logs_tab(raw_data: dict) -> None:
    st.markdown("### Extension Host Output")
    host_output = raw_data.get("extension_host_output", "")
    host_output_lines = raw_data.get("extension_host_output_lines", 0)
    if not host_output:
        st.info(
            "No Extension Host logs available in this report. "
            "Re-run the analysis to capture logs."
        )
        return

    st.caption(f"{host_output_lines} total lines (showing up to last 500)")
    with st.container(height=600):
        st.code(host_output, language="log")
