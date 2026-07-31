"""Shared helpers for package-local detection rules."""

from __future__ import annotations

from typing import Any

from packages.analysis_contracts import (
    ActivationReport,
    EvidenceEvent,
    is_trusted_domain,
    trusted_domains,
)
from packages.analysis_contracts.detection import EvidenceRef

TLS_EVENT_TYPES: frozenset[str] = frozenset({"tls_sni", "tls_client_hello"})
_TARGET_ATTRIBUTION_STATUSES: frozenset[str] = frozenset({"strong", "direct"})


def benign_domains() -> frozenset[str]:
    """Compatibility name for the shared trusted-domain catalog."""

    return trusted_domains()


def is_benign_domain(host: str) -> bool:
    """Compatibility name used by the dynamic unknown-outbound rules."""

    return is_trusted_domain(host)


def event_type(event: EvidenceEvent) -> str:
    # W12-3: raw_context is a typed Pydantic discriminated union; only the
    # NetworkRawContext variant carries `event_type`. Other variants return
    # "" via getattr's default.
    return str(getattr(event.raw_context, "event_type", "")).strip().lower()


def event_method(event: EvidenceEvent) -> str:
    # W12-3 incidental fix: producer (`attribution/links.py` network site)
    # writes `http_method`; this reader used to look for `method`, so the
    # value collapsed to "" in production for years — surfaced once typed
    # variants pinned the field set. NetworkRawContext is the only variant
    # carrying `http_method`; other variants return "" via getattr's default.
    return str(getattr(event.raw_context, "http_method", "")).strip().upper()


def event_message(event: EvidenceEvent) -> str:
    # W12-3: no producer writes a `message` key into raw_context today; this
    # reader has always collapsed to `event.summary` in production. Kept for
    # explicitness so a future variant adding `message` slots in cleanly.
    message = getattr(event.raw_context, "message", "")
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


def is_target_owned(event: EvidenceEvent) -> bool:
    """Event attributed to the analyzed extension with non-correlative strength."""

    if event.is_target_extension_event:
        return True
    return event.attribution_status.strip().lower() in _TARGET_ATTRIBUTION_STATUSES


def target_file_events(report: ActivationReport) -> list[EvidenceEvent]:
    return [event for event in file_events(report) if is_target_owned(event)]


def target_unknown_outbound_network_events(
    report: ActivationReport,
) -> list[EvidenceEvent]:
    return [
        event
        for event in unknown_outbound_network_events(report)
        if is_target_owned(event)
    ]


def is_tls_event(event: EvidenceEvent) -> bool:
    return event_type(event) in TLS_EVENT_TYPES


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
    "TLS_EVENT_TYPES",
    "activation_time",
    "event_message",
    "event_method",
    "event_type",
    "file_events",
    "is_benign_domain",
    "is_target_owned",
    "is_tls_event",
    "make_evidence_ref",
    "network_events",
    "outbound_network_events",
    "rel_time",
    "target_file_events",
    "target_unknown_outbound_network_events",
    "unknown_outbound_network_events",
]
