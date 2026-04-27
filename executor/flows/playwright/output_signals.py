"""Parse and attribute target-extension Output channel events.

PR345 PR5 + ADR 0006: the harness extension wraps
``vscode.window.createOutputChannel`` and emits each ``append``/``appendLine``
call as a JSON-line ``[extrace-harness]`` marker with
``kind="output_channel_appendline"``. This module:

- ``parse_output_signal_events(extension_host_output)`` extracts those
  markers from the captured exthost output and returns
  ``OutputSignalEvent`` instances.
- ``annotate_output_signal_events(report)`` fills in the per-event
  attribution fields by correlating each event's timestamp against the
  nearest target-extension activation entry.

Channel-name attribution is intentionally a heuristic; the harness
hook captures every extension's output channels, so the Python side
must decide which of those events were target-owned. The current rule:
a captured output event is target-owned iff its emit timestamp falls
within the ``rel_time_s`` neighborhood of a target activation entry
(within ``ATTRIBUTION_WINDOW_S`` seconds either side). Otherwise it
remains in the report as an unattributed observation.
"""
# mypy: disable-error-code=no-redef

from __future__ import annotations

import json
import re
from datetime import datetime

try:
    from .runtime_capture._shared import _parse_iso_timestamp
    from .runtime_capture.events import ActivationEntry, OutputSignalEvent
except ImportError:  # pragma: no cover - top-level executor import mode
    from runtime_capture._shared import _parse_iso_timestamp
    from runtime_capture.events import ActivationEntry, OutputSignalEvent

# Reuses the same prefix the existing _HARNESS_MARKER_RE in
# health_reconciliation.py consumes; keeps a single inbound IPC channel.
_HARNESS_MARKER_RE = re.compile(r"\[extrace-harness\]\s+(?P<payload>\{.*\})")

# Attribution window (seconds) — events emitted within this many seconds of
# a target activation entry (forward or backward) are treated as
# target-owned. Conservative default; tuned together with the
# evidence-builder temporal-link confidence in attribution/links.py.
ATTRIBUTION_WINDOW_S = 5.0

# Truncation guard mirrors the JS-side 500-char cap, applied defensively
# in case a future harness payload arrives without the truncation.
_MAX_TEXT_LEN = 500


def _truncate(text: str) -> str:
    if len(text) <= _MAX_TEXT_LEN:
        return text
    return text[:_MAX_TEXT_LEN]


def _format_epoch_ms(
    value_ms: float, monitoring_start: float
) -> tuple[str, float | None]:
    """Format an epoch-millisecond value into a naive local-time ISO string.

    The naive format is intentional: the rest of the runtime capture stack
    (``runtime_capture/extension_host.py`` activation parsing,
    ``_parse_iso_timestamp``) treats timestamps as local-naive. Emitting
    UTC here would create a TZ offset between event and activation
    epochs that defeats the attribution window.
    """
    epoch_s = float(value_ms) / 1000.0
    timestamp = datetime.fromtimestamp(epoch_s).isoformat(timespec="milliseconds")
    rel_time_s: float | None = None
    if monitoring_start > 0:
        rel_time_s = round(max(epoch_s - monitoring_start, 0.0), 3)
    return timestamp, rel_time_s


def parse_output_signal_events(
    extension_host_output: str,
    *,
    monitoring_start: float = 0.0,
) -> list[OutputSignalEvent]:
    """Return OutputSignalEvent records for harness output-channel markers.

    Reads the captured ``extension_host_output`` blob (the same source
    ``health_reconciliation`` consumes) and converts each
    ``[extrace-harness] {kind:"output_channel_appendline", ...}`` line
    into an OutputSignalEvent. Lines that fail to parse or carry the
    wrong ``kind`` are skipped silently — bad harness output is the
    harness's bug, not the parser's.
    """
    events: list[OutputSignalEvent] = []
    if not extension_host_output:
        return events

    for line in str(extension_host_output).splitlines():
        marker_match = _HARNESS_MARKER_RE.search(line)
        if marker_match is None:
            continue
        try:
            payload = json.loads(marker_match.group("payload"))
        except ValueError:
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("kind") != "output_channel_appendline":
            continue
        if payload.get("collector") != "harness_extension":
            continue
        channel = str(payload.get("channel", "") or "")
        text = _truncate(str(payload.get("text", "") or ""))
        ts_value = payload.get("ts")
        try:
            ts_ms = float(ts_value) if ts_value is not None else 0.0
        except (TypeError, ValueError):
            ts_ms = 0.0
        timestamp, rel_time_s = _format_epoch_ms(ts_ms, monitoring_start)
        events.append(
            OutputSignalEvent(
                timestamp=timestamp,
                rel_time_s=rel_time_s,
                channel=channel,
                text=text,
                summary=f"OutputChannel({channel}) appendLine",
            )
        )

    return events


def _activation_index(
    activations: list[ActivationEntry],
    target_extension_id: str,
    monitoring_start: float,
) -> list[tuple[float, ActivationEntry]]:
    """Pre-compute (epoch_seconds, activation) for target activations only."""
    indexed: list[tuple[float, ActivationEntry]] = []
    for activation in activations:
        if not target_extension_id:
            continue
        if activation.extension_id != target_extension_id:
            continue
        epoch = _parse_iso_timestamp(activation.timestamp)
        if epoch is None:
            continue
        # Drop activations that fired before monitoring started — they
        # belong to the previous run's tail and would create spurious links.
        if monitoring_start > 0 and epoch < monitoring_start:
            continue
        indexed.append((epoch, activation))
    indexed.sort(key=lambda item: item[0])
    return indexed


def annotate_output_signal_events(
    events: list[OutputSignalEvent],
    *,
    activations: list[ActivationEntry],
    target_extension_id: str,
    monitoring_start: float = 0.0,
    window_s: float = ATTRIBUTION_WINDOW_S,
) -> list[OutputSignalEvent]:
    """Fill attribution fields on output events whose emit time aligns with a target activation.

    Mutates events in-place and returns the same list for chaining. An
    event whose timestamp falls within ``window_s`` seconds of any target
    activation entry's timestamp is marked target-owned with
    ``attribution_status = "near_target_activation"``. Events outside
    that window stay ``attribution_status = "unattributed"``.
    """
    indexed = _activation_index(activations, target_extension_id, monitoring_start)
    if not indexed:
        return events

    for event in events:
        epoch = _parse_iso_timestamp(event.timestamp)
        if epoch is None:
            continue
        nearest_activation: ActivationEntry | None = None
        nearest_delta = window_s + 1.0
        for activation_epoch, activation in indexed:
            delta = abs(epoch - activation_epoch)
            if delta <= window_s and delta < nearest_delta:
                nearest_delta = delta
                nearest_activation = activation
        if nearest_activation is None:
            continue
        event.extension_id = nearest_activation.extension_id
        event.activation_event = nearest_activation.activation_event
        event.is_target_extension_event = True
        event.attribution_status = "near_target_activation"
        event.attribution_basis = f"within {nearest_delta:.3f}s of target activation"

    return events
