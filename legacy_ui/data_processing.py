"""Report transformation helpers used by the Streamlit analyst console."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

CANONICAL_EVENT_COLUMNS = [
    "event_id",
    "kind",
    "timestamp",
    "rel_time_s",
    "collector",
    "actor",
    "scenario_name",
    "extension_id",
    "activation_event",
    "operation",
    "protocol",
    "host",
    "path",
    "destination_ip",
    "destination_port",
    "sensitive",
    "summary",
    "raw_context",
]

CANONICAL_LINK_COLUMNS = [
    "from_event_id",
    "to_event_id",
    "link_type",
    "confidence",
    "reason",
]


@dataclass
class EvidenceEventView:
    event_id: str
    kind: str
    timestamp: str = ""
    rel_time_s: float | None = None
    collector: str = ""
    actor: str = "unknown"
    scenario_name: str = ""
    extension_id: str = ""
    activation_event: str = ""
    operation: str = ""
    protocol: str = ""
    host: str = ""
    path: str = ""
    destination_ip: str = ""
    destination_port: int | None = None
    sensitive: bool = False
    summary: str = ""
    raw_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceLinkView:
    from_event_id: str
    to_event_id: str
    link_type: str
    confidence: float
    reason: str


@dataclass
class RuleDraftView:
    title: str
    scope: dict[str, Any]
    conditions: list[dict[str, Any]]
    confidence: float
    severity: str
    rationale: str
    labels: list[str]


@dataclass
class ReportContext:
    evidence: pd.DataFrame
    evidence_links: pd.DataFrame
    activations: pd.DataFrame
    network: pd.DataFrame
    files: pd.DataFrame
    scenarios: pd.DataFrame
    summary: dict[str, Any]
    network_summary: dict[str, Any]
    file_summary: dict[str, Any]
    running_extensions: list[dict[str, Any]]


def _empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _ensure_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column not in frame.columns:
            frame[column] = None
    return frame


def _format_epoch(epoch: float | int | str | None) -> str:
    if epoch is None or epoch == "" or epoch == 0:
        return ""
    try:
        return datetime.fromtimestamp(float(epoch)).isoformat(timespec="milliseconds")
    except (TypeError, ValueError, OSError):
        return ""


def _parse_timestamp(value: Any) -> pd.Timestamp:
    if value in (None, ""):
        return pd.NaT
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.notna(parsed):
        return parsed
    numeric_value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric_value):
        return pd.NaT
    return pd.to_datetime(numeric_value, unit="s", errors="coerce")


def _humanize(value: str | None, fallback: str = "Unknown") -> str:
    if not value:
        return fallback
    return str(value).replace("_", " ").strip().title()


def _truncate(value: str, width: int = 72) -> str:
    if len(value) <= width:
        return value
    return f"...{value[-(width - 3) :]}"


def process_activation_data(data: dict[str, Any]) -> pd.DataFrame:
    activated = data.get("activated", [])
    if not activated:
        return _empty_frame(
            [
                "extension_id",
                "activation_event",
                "duration_ms",
                "timestamp",
                "source",
                "dt",
                "rel_start",
                "rel_end",
                "performance",
                "lane_base",
                "lane",
            ]
        )

    df = pd.DataFrame(activated)
    if "activation_event" not in df.columns:
        df["activation_event"] = "(unknown trigger)"
    df["activation_event"] = (
        df["activation_event"].fillna("").replace("", "(unknown trigger)")
    )

    if "duration_ms" not in df.columns:
        df["duration_ms"] = 50
    df["duration_ms"] = pd.to_numeric(df["duration_ms"], errors="coerce").fillna(50)

    if "timestamp" not in df.columns:
        df["timestamp"] = ""
    df["dt"] = df["timestamp"].map(_parse_timestamp)
    has_valid_timestamps = df["dt"].notna().any()

    monitoring_start = pd.to_datetime(
        (data.get("summary") or {}).get("monitoring_started_at"),
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
                synthetic,
                unit="s",
            )
        df["rel_start"] = (df["dt"] - start_time).dt.total_seconds()
    else:
        cumulative = df["duration_ms"].cumsum().shift(fill_value=0)
        df["dt"] = monitoring_start + pd.to_timedelta(cumulative, unit="ms")
        df["rel_start"] = cumulative / 1000.0

    df["rel_end"] = df["rel_start"] + (df["duration_ms"] / 1000)
    df["performance"] = pd.cut(
        df["duration_ms"],
        bins=[-1, 50, 200, 1000, 999999],
        labels=["Instant", "Fast", "Slow", "Critical"],
    )
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


def process_network_data(data: dict[str, Any]) -> pd.DataFrame:
    events = data.get("network_events", [])
    if not events:
        return _empty_frame(
            [
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
                "dt",
                "host_display",
                "event_label",
                "protocol_label",
                "lane",
            ]
        )

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

    df["dt"] = df["timestamp"].map(_parse_timestamp)
    df["rel_time_s"] = pd.to_numeric(df["rel_time_s"], errors="coerce")
    if df["rel_time_s"].isna().all() and df["dt"].notna().any():
        start_time = df["dt"].dropna().min()
        df["rel_time_s"] = (df["dt"] - start_time).dt.total_seconds()

    df["destination_port"] = pd.to_numeric(
        df["destination_port"],
        errors="coerce",
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


def process_file_data(data: dict[str, Any]) -> pd.DataFrame:
    events = data.get("file_events", [])
    if not events:
        return _empty_frame(
            [
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
                "dt",
                "path_short",
                "activation_label",
                "scenario_label",
                "operation_label",
                "source_label",
                "lane",
            ]
        )

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

    df["dt"] = df["timestamp"].map(_parse_timestamp)
    df["rel_time_s"] = pd.to_numeric(df["rel_time_s"], errors="coerce")
    df["source"] = df["source"].fillna("").replace("", "unknown")
    df["observer"] = df["observer"].fillna("").replace("", "unknown")
    df["operation"] = df["operation"].fillna("").replace("", "io")
    df["sensitive"] = df["sensitive"].fillna(False).astype(bool)
    df["path_short"] = df["path"].fillna("").map(_truncate)
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


def process_scenario_data(data: dict[str, Any]) -> pd.DataFrame:
    traces = data.get("scenario_traces", [])
    if not traces:
        return _empty_frame(["name", "started_at", "ended_at", "status", "duration_s"])

    df = pd.DataFrame(traces)
    _ensure_columns(df, ["name", "started_at", "ended_at", "status"])
    df["started_at"] = pd.to_numeric(df["started_at"], errors="coerce")
    df["ended_at"] = pd.to_numeric(df["ended_at"], errors="coerce")
    df["duration_s"] = (df["ended_at"] - df["started_at"]).clip(lower=0)
    return df.sort_values(by="started_at", na_position="last")


def _legacy_evidence_events(data: dict[str, Any]) -> list[EvidenceEventView]:
    events: list[EvidenceEventView] = []

    for index, entry in enumerate(data.get("activated", []), start=1):
        events.append(
            EvidenceEventView(
                event_id=f"activation-{index:04d}",
                kind="activation",
                timestamp=str(entry.get("timestamp", "") or ""),
                collector=str(entry.get("source", "") or "log"),
                actor="extension",
                extension_id=str(entry.get("extension_id", "") or ""),
                activation_event=str(entry.get("activation_event", "") or ""),
                summary=(
                    f"Activation {entry.get('extension_id', 'unknown')}"
                    + (
                        f" via {entry.get('activation_event')}"
                        if entry.get("activation_event")
                        else ""
                    )
                ),
                raw_context={
                    "duration_ms": entry.get("duration_ms"),
                    "success": entry.get("success", True),
                },
            )
        )

    for index, entry in enumerate(data.get("network_events", []), start=1):
        events.append(
            EvidenceEventView(
                event_id=f"network-{index:04d}",
                kind="network",
                timestamp=str(entry.get("timestamp", "") or ""),
                rel_time_s=entry.get("rel_time_s"),
                collector="tshark",
                actor="unknown",
                protocol=str(entry.get("protocol", "") or ""),
                host=str(entry.get("host", "") or ""),
                path=str(entry.get("path", "") or ""),
                destination_ip=str(entry.get("destination_ip", "") or ""),
                destination_port=entry.get("destination_port"),
                summary=str(entry.get("summary", "") or ""),
                raw_context={
                    "event_type": entry.get("event_type", ""),
                    "source_ip": entry.get("source_ip", ""),
                },
            )
        )

    for index, entry in enumerate(data.get("file_events", []), start=1):
        actor = str(entry.get("source", "") or "unknown")
        if actor not in {"extension", "automation", "system"}:
            actor = "unknown"
        events.append(
            EvidenceEventView(
                event_id=f"file-{index:04d}",
                kind="file",
                timestamp=str(entry.get("timestamp", "") or ""),
                rel_time_s=entry.get("rel_time_s"),
                collector=str(entry.get("observer", "") or "unknown"),
                actor=actor,
                scenario_name=str(entry.get("scenario_name", "") or ""),
                extension_id=str(entry.get("related_extension_id", "") or ""),
                activation_event=str(entry.get("related_activation_event", "") or ""),
                operation=str(entry.get("operation", "") or ""),
                path=str(entry.get("path", "") or ""),
                sensitive=bool(entry.get("sensitive", False)),
                summary=str(entry.get("summary", "") or ""),
                raw_context={
                    "secondary_path": entry.get("secondary_path", ""),
                    "flags": entry.get("flags", ""),
                    "source": entry.get("source", ""),
                },
            )
        )

    for index, entry in enumerate(data.get("scenario_traces", []), start=1):
        started_at = entry.get("started_at")
        events.append(
            EvidenceEventView(
                event_id=f"scenario-{index:04d}",
                kind="scenario",
                timestamp=_format_epoch(started_at),
                rel_time_s=entry.get("rel_time_s"),
                collector="automation",
                actor="automation",
                scenario_name=str(entry.get("name", "") or ""),
                summary=(
                    f"Scenario {entry.get('name', 'unknown')} "
                    f"{entry.get('status', 'running')}"
                ),
                raw_context={
                    "status": entry.get("status", "running"),
                    "started_at": started_at,
                    "ended_at": entry.get("ended_at"),
                },
            )
        )

    return events


def process_evidence_data(data: dict[str, Any]) -> pd.DataFrame:
    records = data.get("evidence_events") or [
        asdict(event) for event in _legacy_evidence_events(data)
    ]
    if not records:
        return _empty_frame([*CANONICAL_EVENT_COLUMNS, "dt", "kind_label"])

    df = pd.DataFrame(records)
    _ensure_columns(df, CANONICAL_EVENT_COLUMNS)

    df["rel_time_s"] = pd.to_numeric(df["rel_time_s"], errors="coerce")
    df["destination_port"] = pd.to_numeric(
        df["destination_port"],
        errors="coerce",
    ).astype("Int64")
    df["sensitive"] = df["sensitive"].fillna(False).astype(bool)
    df["raw_context"] = df["raw_context"].apply(
        lambda value: value if isinstance(value, dict) else {}
    )
    df["dt"] = df["timestamp"].map(_parse_timestamp)
    monitoring_start = (data.get("summary") or {}).get("monitoring_started_at")
    if df["rel_time_s"].isna().any() and monitoring_start:
        numeric_rel = (
            df["dt"] - pd.to_datetime(monitoring_start, unit="s", errors="coerce")
        ).dt.total_seconds()
        df["rel_time_s"] = df["rel_time_s"].fillna(numeric_rel.round(3))

    df["kind_label"] = df["kind"].map(lambda value: _humanize(value, "Event"))
    df["collector_label"] = df["collector"].map(
        lambda value: _humanize(value, "Unknown")
    )
    df["actor_label"] = df["actor"].map(lambda value: _humanize(value, "Unknown"))
    df["scenario_label"] = df["scenario_name"].fillna("").replace("", "(no scenario)")
    df["artifact"] = (
        df["path"]
        .fillna("")
        .replace("", pd.NA)
        .fillna(df["host"].fillna("").replace("", pd.NA))
        .fillna(df["extension_id"].fillna("").replace("", pd.NA))
        .fillna(df["summary"].fillna("").replace("", pd.NA))
        .fillna("(no artifact)")
    )
    df["artifact_short"] = df["artifact"].astype(str).map(_truncate)
    df["detail"] = (
        df["activation_event"]
        .fillna("")
        .replace("", pd.NA)
        .fillna(df["operation"].fillna("").replace("", pd.NA))
        .fillna(df["protocol"].fillna("").replace("", pd.NA))
        .fillna(df["collector"].fillna("").replace("", pd.NA))
        .fillna("(n/a)")
    )
    df["timeline_lane"] = df["kind_label"] + " · " + df["artifact_short"]
    df["selection_label"] = (
        df["event_id"].astype(str)
        + " · "
        + df["kind_label"]
        + " · "
        + df["artifact_short"]
    )
    df["timestamp_display"] = df["dt"].dt.strftime("%H:%M:%S.%f").str[:-3].fillna("--")
    df["summary_display"] = df["summary"].fillna("").replace("", "(no summary)")
    return df.sort_values(
        by=["rel_time_s", "dt", "event_id"],
        ascending=[True, True, True],
        na_position="last",
    )


def _legacy_evidence_links(
    data: dict[str, Any], evidence_df: pd.DataFrame
) -> list[EvidenceLinkView]:
    links: list[EvidenceLinkView] = []
    if evidence_df.empty:
        return links

    scenario_map = {
        row.scenario_name: row.event_id
        for row in evidence_df.itertuples(index=False)
        if row.kind == "scenario" and row.scenario_name
    }
    activation_map = {
        row.extension_id: row.event_id
        for row in evidence_df.itertuples(index=False)
        if row.kind == "activation" and row.extension_id
    }

    for row in evidence_df.itertuples(index=False):
        if row.kind != "scenario" and row.scenario_name in scenario_map:
            links.append(
                EvidenceLinkView(
                    from_event_id=row.event_id,
                    to_event_id=scenario_map[row.scenario_name],
                    link_type="occurred_in_scenario",
                    confidence=1.0,
                    reason=(
                        f"Legacy report tagged event with scenario {row.scenario_name}."
                    ),
                )
            )
        if (
            row.kind == "file"
            and row.extension_id
            and row.extension_id in activation_map
        ):
            links.append(
                EvidenceLinkView(
                    from_event_id=row.event_id,
                    to_event_id=activation_map[row.extension_id],
                    link_type="candidate_owner",
                    confidence=0.6,
                    reason=(
                        "Legacy report linked file activity to an activation record."
                    ),
                )
            )
    return links


def process_evidence_links(
    data: dict[str, Any], evidence_df: pd.DataFrame
) -> pd.DataFrame:
    records = data.get("evidence_links") or [
        asdict(link) for link in _legacy_evidence_links(data, evidence_df)
    ]
    if not records:
        return _empty_frame(
            [
                *CANONICAL_LINK_COLUMNS,
                "link_label",
                "confidence_pct",
                "confidence_label",
                "from_kind",
                "to_kind",
                "to_summary",
            ]
        )

    df = pd.DataFrame(records)
    _ensure_columns(df, CANONICAL_LINK_COLUMNS)
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0.0)
    df["link_label"] = df["link_type"].map(lambda value: _humanize(value, "Link"))
    df["confidence_pct"] = (df["confidence"] * 100).round(0).astype(int)
    df["confidence_label"] = df["confidence"].map(
        lambda value: "High" if value >= 0.8 else "Medium" if value >= 0.5 else "Low"
    )

    if not evidence_df.empty:
        event_index = evidence_df.set_index("event_id")
        df["from_kind"] = df["from_event_id"].map(
            lambda event_id: (
                event_index.at[event_id, "kind"]
                if event_id in event_index.index
                else ""
            )
        )
        df["to_kind"] = df["to_event_id"].map(
            lambda event_id: (
                event_index.at[event_id, "kind"]
                if event_id in event_index.index
                else ""
            )
        )
        df["to_summary"] = df["to_event_id"].map(
            lambda event_id: (
                event_index.at[event_id, "summary_display"]
                if event_id in event_index.index
                else ""
            )
        )
    else:
        df["from_kind"] = ""
        df["to_kind"] = ""
        df["to_summary"] = ""
    return df


def _build_summary(data: dict[str, Any], evidence_df: pd.DataFrame) -> dict[str, Any]:
    summary = dict(data.get("summary") or {})
    if summary:
        return summary
    return {
        "total_activated": int((evidence_df["kind"] == "activation").sum())
        if not evidence_df.empty
        else 0,
        "unique_extensions": int(
            evidence_df["extension_id"].replace("", pd.NA).dropna().nunique()
        )
        if not evidence_df.empty
        else 0,
        "scenarios_run": evidence_df["scenario_name"]
        .replace("", pd.NA)
        .dropna()
        .drop_duplicates()
        .tolist()
        if not evidence_df.empty
        else [],
    }


def _build_network_summary(
    data: dict[str, Any], network_df: pd.DataFrame
) -> dict[str, Any]:
    summary = dict(data.get("network_summary") or {})
    if summary:
        return summary
    return {
        "total_events": len(network_df),
        "unique_hosts": int(network_df["host_display"].nunique())
        if not network_df.empty
        else 0,
        "protocols": sorted(network_df["protocol"].dropna().unique().tolist())
        if not network_df.empty
        else [],
        "capture_error": "",
    }


def _build_file_summary(data: dict[str, Any], file_df: pd.DataFrame) -> dict[str, Any]:
    summary = dict(data.get("file_summary") or {})
    if summary:
        return summary
    return {
        "total_events": len(file_df),
        "sensitive_events": int(file_df["sensitive"].sum()) if not file_df.empty else 0,
        "sources": file_df["source"].value_counts(dropna=False).to_dict()
        if not file_df.empty
        else {},
        "operations": file_df["operation"].value_counts(dropna=False).to_dict()
        if not file_df.empty
        else {},
        "capture_error": "",
    }


@st.cache_data(show_spinner=False)
def prepare_report_context(data: dict[str, Any]) -> ReportContext:
    evidence = process_evidence_data(data)
    evidence_links = process_evidence_links(data, evidence)
    activations = process_activation_data(data)
    network = process_network_data(data)
    files = process_file_data(data)
    scenarios = process_scenario_data(data)
    return ReportContext(
        evidence=evidence,
        evidence_links=evidence_links,
        activations=activations,
        network=network,
        files=files,
        scenarios=scenarios,
        summary=_build_summary(data, evidence),
        network_summary=_build_network_summary(data, network),
        file_summary=_build_file_summary(data, files),
        running_extensions=data.get("running_extensions", []),
    )


def get_event_options(evidence_df: pd.DataFrame) -> list[str]:
    if evidence_df.empty:
        return []
    return evidence_df["selection_label"].tolist()


def resolve_event_id(evidence_df: pd.DataFrame, selection_label: str) -> str | None:
    if evidence_df.empty or not selection_label:
        return None
    matches = evidence_df.loc[
        evidence_df["selection_label"] == selection_label, "event_id"
    ]
    if matches.empty:
        return None
    return str(matches.iloc[0])


def get_event_record(
    evidence_df: pd.DataFrame, event_id: str | None
) -> pd.Series | None:
    if evidence_df.empty or not event_id:
        return None
    matches = evidence_df[evidence_df["event_id"] == event_id]
    if matches.empty:
        return None
    return matches.iloc[0]


def get_provenance_records(
    evidence_df: pd.DataFrame,
    links_df: pd.DataFrame,
    event_id: str | None,
) -> tuple[pd.Series | None, pd.DataFrame]:
    event_record = get_event_record(evidence_df, event_id)
    if event_record is None or links_df.empty:
        return event_record, _empty_frame(
            [*links_df.columns, "peer_event_id", "peer_kind", "peer_summary"]
        )

    event_index = evidence_df.set_index("event_id")
    outgoing = links_df[links_df["from_event_id"] == event_id].copy()
    incoming = links_df[links_df["to_event_id"] == event_id].copy()

    outgoing["direction"] = "outgoing"
    outgoing["peer_event_id"] = outgoing["to_event_id"]
    incoming["direction"] = "incoming"
    incoming["peer_event_id"] = incoming["from_event_id"]

    related = pd.concat([outgoing, incoming], ignore_index=True)
    if related.empty:
        return event_record, related

    related["peer_kind"] = related["peer_event_id"].map(
        lambda linked_id: (
            event_index.at[linked_id, "kind_label"]
            if linked_id in event_index.index
            else "Unknown"
        )
    )
    related["peer_summary"] = related["peer_event_id"].map(
        lambda linked_id: (
            event_index.at[linked_id, "summary_display"]
            if linked_id in event_index.index
            else ""
        )
    )
    return event_record, related.sort_values(
        by=["confidence", "link_type"],
        ascending=[False, True],
    )


def build_rule_draft(
    event_record: pd.Series | None,
    related_links: pd.DataFrame,
) -> RuleDraftView | None:
    if event_record is None:
        return None

    conditions: list[dict[str, Any]] = []
    labels = [str(event_record["kind"])]
    scope = {
        "kind": event_record["kind"],
        "actor": event_record["actor"],
        "collector": event_record["collector"],
    }

    conditions.append(
        {"field": "kind", "operator": "eq", "value": event_record["kind"]}
    )
    if event_record["actor"]:
        conditions.append(
            {"field": "actor", "operator": "eq", "value": event_record["actor"]}
        )
    if event_record["collector"]:
        conditions.append(
            {
                "field": "collector",
                "operator": "eq",
                "value": event_record["collector"],
            }
        )

    if event_record["extension_id"]:
        scope["extension_id"] = event_record["extension_id"]
        conditions.append(
            {
                "field": "extension_id",
                "operator": "eq",
                "value": event_record["extension_id"],
            }
        )
        labels.append("extension-attributed")
    if event_record["scenario_name"]:
        scope["scenario_name"] = event_record["scenario_name"]
        conditions.append(
            {
                "field": "scenario_name",
                "operator": "eq",
                "value": event_record["scenario_name"],
            }
        )
    if event_record["kind"] == "file":
        if event_record["operation"]:
            conditions.append(
                {
                    "field": "operation",
                    "operator": "eq",
                    "value": event_record["operation"],
                }
            )
        if event_record["path"]:
            conditions.append(
                {"field": "path", "operator": "contains", "value": event_record["path"]}
            )
        if event_record["sensitive"]:
            labels.append("sensitive-path")
            conditions.append({"field": "sensitive", "operator": "eq", "value": True})
    elif event_record["kind"] == "network":
        if event_record["host"]:
            conditions.append(
                {"field": "host", "operator": "eq", "value": event_record["host"]}
            )
        if event_record["protocol"]:
            conditions.append(
                {
                    "field": "protocol",
                    "operator": "eq",
                    "value": event_record["protocol"],
                }
            )
        if pd.notna(event_record["destination_port"]):
            conditions.append(
                {
                    "field": "destination_port",
                    "operator": "eq",
                    "value": int(event_record["destination_port"]),
                }
            )
        if event_record["destination_ip"]:
            conditions.append(
                {
                    "field": "destination_ip",
                    "operator": "eq",
                    "value": event_record["destination_ip"],
                }
            )
        labels.append("network-activity")
    elif event_record["kind"] == "activation":
        if event_record["activation_event"]:
            conditions.append(
                {
                    "field": "activation_event",
                    "operator": "eq",
                    "value": event_record["activation_event"],
                }
            )
        labels.append("activation-flow")

    confidence = 0.4
    if not related_links.empty:
        confidence = float(related_links["confidence"].max())
        top_link_types = sorted(set(related_links["link_type"].dropna().tolist()))
        if top_link_types:
            scope["evidence_links"] = top_link_types
            labels.extend(top_link_types)

    severity = "medium"
    if bool(event_record["sensitive"]) or confidence >= 0.8:
        severity = "high"
    elif event_record["kind"] == "scenario":
        severity = "low"
    elif confidence < 0.5:
        severity = "medium"

    rationale_parts = [str(event_record["summary_display"])]
    if not related_links.empty:
        top_reasons = related_links["reason"].dropna().head(3).tolist()
        rationale_parts.extend(top_reasons)

    title_artifact = event_record["artifact_short"] or event_record["kind_label"]
    return RuleDraftView(
        title=f"{event_record['kind_label']} Watch: {title_artifact}",
        scope=scope,
        conditions=conditions,
        confidence=round(confidence, 2),
        severity=severity,
        rationale=" ".join(part for part in rationale_parts if part),
        labels=sorted(set(labels)),
    )


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, int | float):
        return str(value)
    text = str(value).replace('"', '\\"')
    return f'"{text}"'


def _to_yaml(value: Any, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, dict | list):
                lines.append(f"{prefix}{key}:")
                lines.append(_to_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(item)}")
        return "\n".join(lines)
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict | list):
                lines.append(f"{prefix}-")
                lines.append(_to_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{prefix}{_yaml_scalar(value)}"


def rule_draft_to_json(rule_draft: RuleDraftView) -> str:
    return json.dumps(asdict(rule_draft), indent=2, ensure_ascii=False)


def rule_draft_to_yaml(rule_draft: RuleDraftView) -> str:
    return _to_yaml(asdict(rule_draft))


def build_network_log(network_df: pd.DataFrame, limit: int = 400) -> str:
    if network_df.empty:
        return ""

    lines: list[str] = []
    for row in network_df.tail(limit).itertuples(index=False):
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


def build_file_log(file_df: pd.DataFrame, limit: int = 400) -> str:
    if file_df.empty:
        return ""

    lines: list[str] = []
    for row in file_df.tail(limit).itertuples(index=False):
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


def build_evidence_log(evidence_df: pd.DataFrame, limit: int = 400) -> str:
    if evidence_df.empty:
        return ""

    lines: list[str] = []
    for row in evidence_df.tail(limit).itertuples(index=False):
        rel = f"{row.rel_time_s:8.3f}s" if pd.notna(row.rel_time_s) else "   --.--s"
        artifact = row.artifact_short or "(no artifact)"
        detail = row.detail or "(n/a)"
        scenario = f" [{row.scenario_name}]" if row.scenario_name else ""
        lines.append(
            f"[{rel}] {row.kind_label:<10} {row.actor_label:<10} "
            f"{artifact} :: {detail}{scenario}"
        )
    return "\n".join(lines)


def filter_dataframe(
    frame: pd.DataFrame,
    search_text: str,
    columns: list[str],
) -> pd.DataFrame:
    if frame.empty or not search_text:
        return frame

    mask = pd.Series(False, index=frame.index)
    for column in columns:
        mask = mask | frame[column].astype(str).str.contains(
            search_text,
            case=False,
            na=False,
        )
    return frame[mask]


def to_csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")
