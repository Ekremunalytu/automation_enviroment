"""Shared fact extraction helpers for risk signal policy."""

from __future__ import annotations

from typing import Any


def indexed_target_activations(report: Any) -> list[tuple[str, Any]]:
    target_id = getattr(report, "target_extension_id", "")
    if not target_id:
        return []
    return [
        (f"activation-{index:04d}", entry)
        for index, entry in enumerate(getattr(report, "activated", []), start=1)
        if getattr(entry, "extension_id", "") == target_id
    ]


def indexed_target_file_events(report: Any) -> list[tuple[str, Any]]:
    return [
        (f"file-{index:04d}", entry)
        for index, entry in enumerate(getattr(report, "file_events", []), start=1)
        if getattr(entry, "is_target_extension_event", False)
    ]


def indexed_target_network_events(report: Any) -> list[tuple[str, Any]]:
    return [
        (f"network-{index:04d}", entry)
        for index, entry in enumerate(getattr(report, "network_events", []), start=1)
        if getattr(entry, "is_target_extension_event", False)
    ]


def indexed_ui_blockers(report: Any) -> list[tuple[str, Any]]:
    return [
        (f"ui-blocker-{index:04d}", entry)
        for index, entry in enumerate(
            getattr(report, "ui_blocker_entries", []),
            start=1,
        )
    ]
