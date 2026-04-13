"""Analyst-focused dashboard tab renderers."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
from components import info_card, metric_card, pill_row, render_section_intro
from data_processing import (
    ReportContext,
    build_evidence_log,
    build_rule_draft,
    filter_dataframe,
    get_event_options,
    get_event_record,
    get_provenance_records,
    resolve_event_id,
    rule_draft_to_json,
    rule_draft_to_yaml,
    to_csv_bytes,
)

KIND_DOMAIN = ["Activation", "Network", "File", "Scenario"]
KIND_RANGE = ["#8b5cf6", "#10b981", "#22d3ee", "#f59e0b"]


def _selection_key(key_prefix: str) -> str:
    return f"{key_prefix}_selected_event_label"


def _widget_key(key_prefix: str, suffix: str) -> str:
    return f"{key_prefix}_{suffix}"


def _ensure_selection(context: ReportContext, key_prefix: str) -> str | None:
    if context.evidence.empty:
        return None

    options = get_event_options(context.evidence)
    if not options:
        return None

    selection_key = _selection_key(key_prefix)
    current = st.session_state.get(selection_key)
    if current not in options:
        st.session_state[selection_key] = options[0]
        current = options[0]
    return resolve_event_id(context.evidence, current)


def _render_event_selector(
    evidence_df: pd.DataFrame,
    key_prefix: str,
    label: str = "Selected Evidence Event",
    widget_suffix: str = "focus_selectbox",
) -> str | None:
    if evidence_df.empty:
        st.info("No evidence events available.")
        return None

    options = get_event_options(evidence_df)
    state_key = _selection_key(key_prefix)
    current = st.session_state.get(state_key)
    if current not in options:
        st.session_state[state_key] = options[0]
        current = options[0]

    selection = st.selectbox(
        label,
        options,
        index=options.index(current),
        key=_widget_key(key_prefix, widget_suffix),
    )
    st.session_state[state_key] = selection
    return resolve_event_id(evidence_df, selection)


def _render_link_cards(related: pd.DataFrame) -> None:
    if related.empty:
        st.info("No provenance links available for this event.")
        return

    cards: list[str] = []
    for row in related.head(8).itertuples(index=False):
        cards.append(
            f"""
            <div class="chain-card">
                <div class="chain-header">
                    <div>
                        <div class="chain-title">{row.link_label} → {row.peer_kind}</div>
                        <div class="chain-subtitle">{row.peer_summary}</div>
                    </div>
                    <div class="chain-score">{row.confidence_pct}% · {row.confidence_label}</div>
                </div>
                <div class="chain-reason">{row.reason}</div>
            </div>
            """
        )
    st.markdown(
        f'<div class="provenance-chain">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def _render_event_identity(event_record: pd.Series) -> None:
    tone = "alert" if bool(event_record["sensitive"]) else "accent"
    identity_cards = st.columns(3)
    with identity_cards[0]:
        st.markdown(
            info_card("Artifact", str(event_record["artifact"]), tone=tone),
            unsafe_allow_html=True,
        )
    with identity_cards[1]:
        st.markdown(
            info_card(
                "Collector / Actor",
                f"{event_record['collector_label']} / {event_record['actor_label']}",
            ),
            unsafe_allow_html=True,
        )
    with identity_cards[2]:
        st.markdown(
            info_card(
                "Event Kind", f"{event_record['kind_label']} · {event_record['detail']}"
            ),
            unsafe_allow_html=True,
        )


def _render_event_context(event_record: pd.Series, related: pd.DataFrame) -> None:
    col_left, col_right = st.columns([1.15, 1.85], gap="large")
    with col_left:
        top_confidence = (
            f"{int(float(related['confidence'].max()) * 100)}%"
            if not related.empty
            else "0%"
        )
        context_cards = st.columns(2)
        with context_cards[0]:
            st.markdown(
                info_card(
                    "Scenario",
                    str(event_record["scenario_label"]),
                ),
                unsafe_allow_html=True,
            )
        with context_cards[1]:
            st.markdown(
                info_card(
                    "Best Link Confidence",
                    top_confidence,
                    tone="warn"
                    if not related.empty and float(related["confidence"].max()) < 0.5
                    else "default",
                ),
                unsafe_allow_html=True,
            )

        detail_rows = [
            ("Event ID", event_record["event_id"]),
            ("Extension", event_record["extension_id"] or "(unattributed)"),
            ("Host", event_record["host"] or "(n/a)"),
            ("Path", event_record["path"] or "(n/a)"),
            ("Destination IP", event_record["destination_ip"] or "(n/a)"),
            (
                "Port",
                str(event_record["destination_port"])
                if pd.notna(event_record["destination_port"])
                else "(n/a)",
            ),
            ("Timestamp", event_record["timestamp_display"]),
            ("Sensitive", "Yes" if bool(event_record["sensitive"]) else "No"),
        ]
        details = pd.DataFrame(detail_rows, columns=["Field", "Value"])
        st.dataframe(details, hide_index=True, use_container_width=True, height=318)
    with col_right:
        render_section_intro(
            "Reason Chain",
            "Explicit links that explain scenario membership, candidate ownership and duplicate observations.",
        )
        _render_link_cards(related)
        if not related.empty and float(related["confidence"].max()) < 0.5:
            st.warning(
                "Ownership evidence is low-confidence. Use this as a lead, not as a final attribution."
            )


def _render_filter_panel(context: ReportContext, key_prefix: str) -> pd.DataFrame:
    evidence_df = context.evidence
    if evidence_df.empty:
        return evidence_df

    render_section_intro(
        "Investigation Filters",
        "Narrow the timeline before selecting a specific evidence record.",
    )

    kinds = sorted(evidence_df["kind_label"].dropna().unique().tolist())
    selected_kinds = st.multiselect(
        "Kinds",
        kinds,
        default=kinds,
        key=f"{key_prefix}_filter_kinds",
    )

    actors = sorted(evidence_df["actor_label"].dropna().unique().tolist())
    selected_actors = st.multiselect(
        "Actors",
        actors,
        default=actors,
        key=f"{key_prefix}_filter_actors",
    )

    collectors = sorted(evidence_df["collector_label"].dropna().unique().tolist())
    selected_collectors = st.multiselect(
        "Collectors",
        collectors,
        default=collectors,
        key=f"{key_prefix}_filter_collectors",
    )

    scenario_options = sorted(
        scenario
        for scenario in evidence_df["scenario_label"].dropna().unique().tolist()
        if scenario != "(no scenario)"
    )
    selected_scenarios = st.multiselect(
        "Scenarios",
        scenario_options,
        default=[],
        key=f"{key_prefix}_filter_scenarios",
    )

    sensitive_only = st.checkbox(
        "Sensitive artifacts only",
        key=f"{key_prefix}_filter_sensitive",
    )
    search_text = st.text_input(
        "Search",
        placeholder="host, path, extension, summary…",
        key=f"{key_prefix}_filter_search",
    )

    filtered = evidence_df[
        evidence_df["kind_label"].isin(selected_kinds)
        & evidence_df["actor_label"].isin(selected_actors)
        & evidence_df["collector_label"].isin(selected_collectors)
    ]
    if selected_scenarios:
        filtered = filtered[filtered["scenario_name"].isin(selected_scenarios)]
    if sensitive_only:
        filtered = filtered[filtered["sensitive"]]
    filtered = filter_dataframe(
        filtered,
        search_text,
        [
            "artifact",
            "summary_display",
            "extension_id",
            "host",
            "path",
            "scenario_name",
            "collector",
            "actor",
        ],
    )
    return filtered


def render_overview_tab(context: ReportContext, chart_theme: str) -> None:
    evidence_df = context.evidence
    if evidence_df.empty:
        st.info("No evidence data to visualize.")
        return

    render_section_intro(
        "Run Summary",
        "Topline activity and the distribution of collected evidence for this run.",
    )

    summary_cards = st.columns(4)
    with summary_cards[0]:
        st.markdown(
            metric_card("Evidence Events", f"{len(evidence_df):,}", "#8b5cf6"),
            unsafe_allow_html=True,
        )
    with summary_cards[1]:
        st.markdown(
            metric_card(
                "Attributed Extensions",
                str(evidence_df["extension_id"].replace("", pd.NA).dropna().nunique()),
                "#22d3ee",
            ),
            unsafe_allow_html=True,
        )
    with summary_cards[2]:
        st.markdown(
            metric_card(
                "Sensitive Artifacts",
                str(int(evidence_df["sensitive"].sum())),
                "#f43f5e",
            ),
            unsafe_allow_html=True,
        )
    with summary_cards[3]:
        st.markdown(
            metric_card(
                "Evidence Links",
                str(len(context.evidence_links)),
                "#f59e0b",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)
    col_timeline, col_mix = st.columns([2, 1])

    with col_timeline:
        render_section_intro(
            "Evidence Timeline", "A single pulse view across all event kinds."
        )
        lane_count = evidence_df["timeline_lane"].nunique()
        chart_height = max(360, lane_count * 18)
        chart = (
            alt.Chart(evidence_df)
            .mark_circle(size=85, opacity=0.82)
            .encode(
                x=alt.X(
                    "rel_time_s:Q",
                    title="Timeline (seconds)",
                    axis=alt.Axis(gridColor="#2a2a2a"),
                ),
                y=alt.Y(
                    "timeline_lane:N",
                    title=None,
                    axis=alt.Axis(labelLimit=220, gridColor="#2a2a2a"),
                ),
                color=alt.Color(
                    "kind_label:N",
                    scale=alt.Scale(domain=KIND_DOMAIN, range=KIND_RANGE),
                    legend=alt.Legend(orient="bottom", columns=2, labelColor="#a1a1aa"),
                ),
                shape=alt.Shape("actor_label:N", legend=None),
                tooltip=[
                    "event_id",
                    "kind_label",
                    "actor_label",
                    "collector_label",
                    "artifact",
                    "summary_display",
                ],
            )
            .properties(height=chart_height, width="container")
        )
        st.altair_chart(chart, theme="streamlit")

    with col_mix:
        render_section_intro("Evidence Mix", "Kinds and actors visible at a glance.")
        kind_mix = (
            alt.Chart(evidence_df)
            .mark_arc(innerRadius=70, cornerRadius=5, stroke="#050505", strokeWidth=2)
            .encode(
                theta=alt.Theta("count()"),
                color=alt.Color(
                    "kind_label:N",
                    scale=alt.Scale(domain=KIND_DOMAIN, range=KIND_RANGE),
                    legend=alt.Legend(orient="bottom", labelColor="#a1a1aa"),
                ),
                tooltip=["kind_label", "count()"],
            )
            .properties(height=250)
        )
        st.altair_chart(kind_mix, theme="streamlit")

        actor_counts = (
            evidence_df.groupby("actor_label", dropna=False)
            .size()
            .reset_index(name="events")
            .sort_values("events", ascending=False)
        )
        actor_bar = (
            alt.Chart(actor_counts)
            .mark_bar(cornerRadiusEnd=4, color="#22d3ee")
            .encode(
                x=alt.X("events:Q", title="Events", axis=alt.Axis(gridColor="#2a2a2a")),
                y=alt.Y("actor_label:N", sort="-x", title=None),
                tooltip=["actor_label", "events"],
            )
            .properties(height=220)
        )
        st.altair_chart(actor_bar, theme="streamlit")

    top_artifacts = (
        evidence_df.groupby(["artifact_short", "kind_label"], dropna=False)
        .size()
        .reset_index(name="events")
        .sort_values("events", ascending=False)
        .head(12)
    )
    render_section_intro(
        "Hot Artifacts", "Most active hosts, paths, or extension surfaces in this run."
    )
    artifact_chart = (
        alt.Chart(top_artifacts)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("events:Q", title="Events", axis=alt.Axis(gridColor="#2a2a2a")),
            y=alt.Y(
                "artifact_short:N", sort="-x", title=None, axis=alt.Axis(labelLimit=260)
            ),
            color=alt.Color(
                "kind_label:N",
                scale=alt.Scale(domain=KIND_DOMAIN, range=KIND_RANGE),
                legend=None,
            ),
            tooltip=["artifact_short", "kind_label", "events"],
        )
        .properties(height=300)
    )
    st.altair_chart(artifact_chart, theme="streamlit")


def render_evidence_timeline_tab(
    context: ReportContext, chart_theme: str, key_prefix: str
) -> None:
    evidence_df = context.evidence
    if evidence_df.empty:
        st.info("No evidence captured in this report.")
        return

    col_filters, col_results = st.columns([1, 2.4], gap="large")
    with col_filters:
        filtered = _render_filter_panel(context, key_prefix)
    with col_results:
        render_section_intro(
            "Evidence Timeline",
            "Use the filters to isolate a behavior cluster, then select an event for provenance review.",
        )
        if filtered.empty:
            st.warning("No evidence matched the current filters.")
            return

        selected_event_id = _render_event_selector(
            filtered,
            key_prefix,
            "Focus Event",
            widget_suffix="timeline_focus_selectbox",
        )
        lane_count = filtered["timeline_lane"].nunique()
        chart_height = max(420, lane_count * 20)
        chart = (
            alt.Chart(filtered)
            .mark_circle(size=90, opacity=0.84)
            .encode(
                x=alt.X(
                    "rel_time_s:Q",
                    title="Timeline (seconds)",
                    axis=alt.Axis(gridColor="#2a2a2a"),
                ),
                y=alt.Y(
                    "timeline_lane:N",
                    title=None,
                    axis=alt.Axis(labelLimit=260, gridColor="#2a2a2a"),
                ),
                color=alt.Color(
                    "kind_label:N",
                    scale=alt.Scale(domain=KIND_DOMAIN, range=KIND_RANGE),
                    legend=alt.Legend(orient="bottom", labelColor="#a1a1aa"),
                ),
                size=alt.Size("sensitive:N", legend=None),
                tooltip=[
                    "event_id",
                    "kind_label",
                    "collector_label",
                    "actor_label",
                    "scenario_label",
                    "summary_display",
                ],
            )
            .properties(height=chart_height, width="container")
        )
        st.altair_chart(chart, theme="streamlit")

        toolbar_left, toolbar_right = st.columns([4, 1])
        with toolbar_left:
            st.caption(f"{len(filtered)} evidence records after filtering")
        with toolbar_right:
            st.download_button(
                "Export CSV",
                to_csv_bytes(filtered),
                "extrace_evidence.csv",
                "text/csv",
                key=f"{key_prefix}_download_evidence_csv",
                use_container_width=True,
            )

        st.dataframe(
            filtered[
                [
                    "timestamp_display",
                    "kind_label",
                    "actor_label",
                    "collector_label",
                    "scenario_label",
                    "artifact_short",
                    "detail",
                    "summary_display",
                ]
            ],
            column_config={
                "timestamp_display": st.column_config.TextColumn("Time"),
                "kind_label": st.column_config.TextColumn("Kind"),
                "actor_label": st.column_config.TextColumn("Actor"),
                "collector_label": st.column_config.TextColumn("Collector"),
                "scenario_label": st.column_config.TextColumn("Scenario"),
                "artifact_short": st.column_config.TextColumn(
                    "Artifact", width="medium"
                ),
                "detail": st.column_config.TextColumn("Detail", width="medium"),
                "summary_display": st.column_config.TextColumn(
                    "Summary", width="large"
                ),
            },
            hide_index=True,
            height=360,
        )

        if selected_event_id:
            st.caption(f"Focused event: `{selected_event_id}`")

        render_section_intro(
            "Evidence Stream", "A compact, grep-like view of the same filtered records."
        )
        with st.container(height=240):
            st.code(build_evidence_log(filtered), language="log")


def render_provenance_tab(context: ReportContext, key_prefix: str) -> None:
    selected_event_id = _ensure_selection(context, key_prefix)
    event_record, related = get_provenance_records(
        context.evidence,
        context.evidence_links,
        selected_event_id,
    )
    if event_record is None:
        st.info("Select an evidence event from the timeline tab first.")
        return

    render_section_intro(
        "Why This Event Exists",
        "Collector, actor, scenario, artifact and link chain for the currently focused evidence event.",
    )
    _render_event_identity(event_record)
    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)
    _render_event_context(event_record, related)

    detail_col, raw_col = st.columns([1.35, 1], gap="large")
    with detail_col:
        render_section_intro(
            "Evidence Summary", "Primary narrative and attached evidence labels."
        )
        st.code(str(event_record["summary_display"]), language="text")
        st.markdown(
            pill_row(
                [
                    event_record["kind_label"],
                    event_record["collector_label"],
                    event_record["actor_label"],
                    event_record["scenario_label"],
                ],
                tone="accent",
            ),
            unsafe_allow_html=True,
        )
    with raw_col:
        raw_context = event_record["raw_context"]
        render_section_intro(
            "Raw Context", "Collector-specific fields preserved for investigation."
        )
        if isinstance(raw_context, dict) and raw_context:
            st.json(raw_context, expanded=False)
        else:
            st.info("No collector-specific raw context on this record.")


def render_rule_workbench_tab(context: ReportContext, key_prefix: str) -> None:
    selected_event_id = _ensure_selection(context, key_prefix)
    event_record, related = get_provenance_records(
        context.evidence,
        context.evidence_links,
        selected_event_id,
    )
    if event_record is None:
        st.info("Select an evidence event to draft a rule.")
        return

    render_section_intro(
        "Rule Workbench",
        "Draft a portable detection rule from the focused evidence event. Nothing is persisted server-side.",
    )

    rule_draft = build_rule_draft(event_record, related)
    if rule_draft is None:
        st.info("Rule draft could not be generated.")
        return

    draft_json = rule_draft_to_json(rule_draft)
    draft_yaml = rule_draft_to_yaml(rule_draft)

    summary_cards = st.columns(4)
    with summary_cards[0]:
        st.markdown(
            info_card("Title", rule_draft.title, tone="accent"),
            unsafe_allow_html=True,
        )
    with summary_cards[1]:
        st.markdown(
            info_card("Severity", rule_draft.severity.title(), tone="warn"),
            unsafe_allow_html=True,
        )
    with summary_cards[2]:
        st.markdown(
            info_card("Confidence", f"{int(rule_draft.confidence * 100)}%"),
            unsafe_allow_html=True,
        )
    with summary_cards[3]:
        st.markdown(
            info_card("Conditions", str(len(rule_draft.conditions))),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)
    top_col, export_col = st.columns([1.5, 1], gap="large")
    with top_col:
        render_section_intro(
            "Rule Intent",
            "Human-readable rationale and classification labels before export.",
        )
        st.code(rule_draft.rationale, language="text")
        st.markdown(
            pill_row(rule_draft.labels, tone="accent"),
            unsafe_allow_html=True,
        )
        scope_items = [f"{key}: {value}" for key, value in rule_draft.scope.items()]
        st.markdown(
            pill_row(scope_items, tone="warn"),
            unsafe_allow_html=True,
        )
    with export_col:
        render_section_intro(
            "Export", "Download the draft in the format that fits your rule pipeline."
        )
        st.download_button(
            "Download JSON",
            draft_json.encode("utf-8"),
            "rule_draft.json",
            "application/json",
            key=f"{key_prefix}_rule_json",
            use_container_width=True,
        )
        st.download_button(
            "Download YAML",
            draft_yaml.encode("utf-8"),
            "rule_draft.yaml",
            "text/yaml",
            key=f"{key_prefix}_rule_yaml",
            use_container_width=True,
        )

    lower_left, lower_right = st.columns([1.2, 1.3], gap="large")
    with lower_left:
        render_section_intro(
            "Rule Conditions",
            "Concrete match clauses derived from the focused evidence record.",
        )
        conditions_df = pd.DataFrame(rule_draft.conditions)
        st.dataframe(
            conditions_df,
            column_config={
                "field": st.column_config.TextColumn("Field"),
                "operator": st.column_config.TextColumn("Operator"),
                "value": st.column_config.TextColumn("Value", width="large"),
            },
            hide_index=True,
            height=280,
        )
    with lower_right:
        render_section_intro(
            "Draft Output", "Review the serialized rule before exporting it."
        )
        format_tab_json, format_tab_yaml = st.tabs(["JSON", "YAML"])
        with format_tab_json:
            st.code(draft_json, language="json")
        with format_tab_yaml:
            st.code(draft_yaml, language="yaml")


def render_dashboard_focus_bar(context: ReportContext, key_prefix: str) -> None:
    if context.evidence.empty:
        return
    col_picker, col_hint = st.columns([2.2, 1], gap="large")
    with col_picker:
        _render_event_selector(
            context.evidence,
            key_prefix,
            "Focused Evidence Event",
            widget_suffix="global_focus_selectbox",
        )
    with col_hint:
        selected_event_id = _ensure_selection(context, key_prefix)
        event_record = get_event_record(context.evidence, selected_event_id)
        if event_record is not None:
            st.markdown(
                info_card(
                    "Current Focus",
                    f"{event_record['kind_label']} · {event_record['artifact_short']}",
                    tone="accent",
                ),
                unsafe_allow_html=True,
            )
