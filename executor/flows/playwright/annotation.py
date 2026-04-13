"""Helpers for target attribution summaries."""

from __future__ import annotations

from typing import Any


def strong_target_file_events(report: Any) -> list[Any]:
    return [
        event
        for event in getattr(report, "target_file_events", [])
        if getattr(event, "attribution_status", "") == "target_attributed"
    ]


def strong_target_network_events(report: Any) -> list[Any]:
    return [
        event
        for event in getattr(report, "target_network_events", [])
        if getattr(event, "attribution_status", "") == "target_attributed"
    ]


def has_strong_target_attribution(report: Any) -> bool:
    return bool(
        strong_target_file_events(report) or strong_target_network_events(report)
    )


def target_stream_entries(report: Any) -> list[Any]:
    streams = getattr(report, "log_streams", {})
    if not isinstance(streams, dict):
        return []
    entries = streams.get("target_extension_host", [])
    return entries if isinstance(entries, list) else []


def build_attribution_summary(
    report: Any,
    *,
    count_target_activations: Any,
    is_background_activation: Any,
) -> dict[str, Any]:
    correlated_only = [
        event
        for event in [
            *getattr(report, "file_events", []),
            *getattr(report, "network_events", []),
        ]
        if getattr(event, "attribution_status", "")
        in {"near_target_activation", "competing_candidate"}
    ]
    background_activations = [
        event
        for event in getattr(report, "activated", [])
        if getattr(event, "extension_id", "")
        == getattr(report, "target_extension_id", "")
        and is_background_activation(getattr(event, "activation_event", ""))
    ]
    competing_candidates = [
        event
        for event in [
            *getattr(report, "file_events", []),
            *getattr(report, "network_events", []),
        ]
        if getattr(event, "attribution_status", "") == "competing_candidate"
    ]
    return {
        "target_activation_count": count_target_activations(
            getattr(report, "activated", []),
            getattr(report, "target_extension_id", ""),
        ),
        "strong_target_file_event_count": len(strong_target_file_events(report)),
        "strong_target_network_event_count": len(strong_target_network_events(report)),
        "correlated_only_event_count": len(correlated_only),
        "background_activation_count": len(background_activations),
        "competing_candidate_count": len(competing_candidates),
        "ui_blocker_count": len(getattr(report, "ui_blocker_entries", [])),
    }
