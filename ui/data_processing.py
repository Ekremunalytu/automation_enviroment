"""Report transformation helpers used by the Streamlit dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import streamlit as st


@dataclass
class ReportContext:
    activations: pd.DataFrame
    network: pd.DataFrame
    files: pd.DataFrame
    summary: dict[str, Any]
    network_summary: dict[str, Any]
    file_summary: dict[str, Any]
    running_extensions: list[dict[str, Any]]


def process_activation_data(data: dict[str, Any]) -> pd.DataFrame:
    activated = data.get("activated", [])
    if not activated:
        return pd.DataFrame()

    df = pd.DataFrame(activated)
    if "activation_event" not in df.columns:
        df["activation_event"] = "(unknown trigger)"
    df["activation_event"] = (
        df["activation_event"].fillna("").replace("", "(unknown trigger)")
    )

    if "duration_ms" not in df.columns:
        df["duration_ms"] = 50
    df["duration_ms"] = pd.to_numeric(df["duration_ms"], errors="coerce").fillna(50)

    has_valid_timestamps = False
    if "timestamp" in df.columns:
        df["dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
        mask_nat = df["dt"].isna() & df["timestamp"].notna() & (df["timestamp"] != "")
        if mask_nat.any():
            numeric_ts = pd.to_numeric(df.loc[mask_nat, "timestamp"], errors="coerce")
            df.loc[mask_nat, "dt"] = pd.to_datetime(numeric_ts, unit="s")
        has_valid_timestamps = df["dt"].notna().any()

    monitoring_start = pd.to_datetime(
        data.get("summary", {}).get("monitoring_started_at"),
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
        labels=["⚡ Instant", "✅ Fast", "⚠️ Slow", "🔥 Critical"],
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
        return pd.DataFrame()

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

    df["dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
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
        return pd.DataFrame()

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

    df["dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["rel_time_s"] = pd.to_numeric(df["rel_time_s"], errors="coerce")
    df["source"] = df["source"].fillna("").replace("", "unknown")
    df["observer"] = df["observer"].fillna("").replace("", "unknown")
    df["operation"] = df["operation"].fillna("").replace("", "io")
    df["sensitive"] = df["sensitive"].fillna(False).astype(bool)
    df["path_short"] = (
        df["path"]
        .fillna("")
        .map(lambda value: value if len(value) <= 72 else f"...{value[-69:]}")
    )
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


@st.cache_data(show_spinner=False)
def prepare_report_context(data: dict[str, Any]) -> ReportContext:
    return ReportContext(
        activations=process_activation_data(data),
        network=process_network_data(data),
        files=process_file_data(data),
        summary=data.get("summary", {}),
        network_summary=data.get("network_summary", {}),
        file_summary=data.get("file_summary", {}),
        running_extensions=data.get("running_extensions", []),
    )


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
