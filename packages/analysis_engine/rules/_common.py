"""Shared helpers for package-local detection rules."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from packages.analysis_contracts import ActivationReport, EvidenceEvent
from packages.analysis_contracts.detection import EvidenceRef

_BENIGN_DOMAIN_PATH = (
    Path(__file__).resolve().parents[1] / "allowlists" / "benign_domains.txt"
)


@lru_cache(maxsize=1)
def benign_domains() -> frozenset[str]:
    lines = _BENIGN_DOMAIN_PATH.read_text(encoding="utf-8").splitlines()
    values = {line.strip().lower() for line in lines if line.strip()}
    return frozenset(values)


def is_benign_domain(host: str) -> bool:
    normalized = host.strip().lower().rstrip(".")
    if not normalized:
        return False
    for allowed in benign_domains():
        if normalized == allowed or normalized.endswith(f".{allowed}"):
            return True
    return False


def event_type(event: EvidenceEvent) -> str:
    raw_context = event.raw_context if isinstance(event.raw_context, dict) else {}
    value = raw_context.get("event_type", "")
    return str(value).strip().lower()


def event_method(event: EvidenceEvent) -> str:
    raw_context = event.raw_context if isinstance(event.raw_context, dict) else {}
    return str(raw_context.get("method", "")).strip().upper()


def event_message(event: EvidenceEvent) -> str:
    raw_context = event.raw_context if isinstance(event.raw_context, dict) else {}
    message = raw_context.get("message", "")
    return " ".join(
        part for part in [event.summary.strip(), str(message).strip()] if part
    ).strip()


def rel_time(event: EvidenceEvent) -> float:
    return event.rel_time_s if event.rel_time_s is not None else float("inf")


def activation_time(report: ActivationReport) -> float | None:
    candidates: list[float] = []
    for event in report.evidence_events:
        kind = event.kind.strip().lower()
        if kind not in {"activation", "extension_host"}:
            continue
        type_name = event_type(event)
        summary = event.summary.strip().lower()
        if type_name == "activated" or "activated" in summary:
            candidates.append(rel_time(event))
    return min(candidates) if candidates else None


def network_events(report: ActivationReport) -> list[EvidenceEvent]:
    return [event for event in report.evidence_events if event.kind == "network"]


def file_events(report: ActivationReport) -> list[EvidenceEvent]:
    return [event for event in report.evidence_events if event.kind == "file"]


def outbound_network_events(report: ActivationReport) -> list[EvidenceEvent]:
    return [event for event in network_events(report) if event.host]


def unknown_outbound_network_events(report: ActivationReport) -> list[EvidenceEvent]:
    return [
        event
        for event in outbound_network_events(report)
        if not is_benign_domain(event.host)
    ]


def make_evidence_ref(event: EvidenceEvent, **extra: Any) -> EvidenceRef:
    type_name = "event"
    if event.kind == "file":
        type_name = (
            "filesystem_read"
            if event.operation.strip().lower() == "read"
            else "filesystem_event"
        )
    elif event.kind == "network":
        type_name = (
            "network_request"
            if event_type(event) == "http_request"
            else "network_event"
        )
    elif event.kind == "extension_host":
        type_name = "extension_host_log"
    elif event.kind == "activation":
        type_name = "activation"

    payload: dict[str, Any] = {
        "type": type_name,
        "event_id": event.event_id,
        "summary": event.summary or None,
    }
    if event.path:
        payload["path"] = event.path
    if event.host:
        payload["host"] = event.host
    if event.operation:
        payload["operation"] = event.operation
    if event_method(event):
        payload["method"] = event_method(event)
    payload.update(extra)
    return EvidenceRef(**payload)


__all__ = [
    "activation_time",
    "event_message",
    "event_method",
    "event_type",
    "file_events",
    "is_benign_domain",
    "make_evidence_ref",
    "network_events",
    "outbound_network_events",
    "rel_time",
    "unknown_outbound_network_events",
]
