"""Parse and attribute target-extension Output channel events.

PR345 PR5 + ADR 0006: the harness extension wraps
``vscode.window.createOutputChannel`` and emits each ``append``/``appendLine``
call as a JSON-line ``[extrace-harness]`` marker with
``kind="output_channel_appendline"``. This module:

- ``parse_output_signal_events(extension_host_output)`` extracts those
  markers from the captured exthost output and returns
  ``OutputSignalEvent`` instances. Used as a fallback / transitional
  source for older VS Code builds that piped extension ``console.log``
  into ``exthost.log``.
- ``read_output_channel_logs(logs_dir)`` walks the per-window
  ``output_logging_<ts>/<idx>-<channel>.log`` files VS Code 1.105+
  writes to disk and emits one ``OutputSignalEvent`` per appendLine.
  This is the primary source post-W8-0 because ``console.log`` from
  extensions no longer reaches ``exthost.log`` on VS Code 1.105+.
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
from pathlib import Path

from packages.analysis_contracts import redact_secrets

from ..runtime_capture._shared import VSCODE_LOGS_DIR, _parse_iso_timestamp
from ..runtime_capture.events import ActivationEntry, OutputSignalEvent

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
        # W10-7 (closes [FOLLOWUP w8-6-output-signals-redaction]) +
        # W12-0 (closes [FOLLOWUP w8-6-output-signals-file-backed-redaction]):
        # OutputSignalEvent.text carries extension-controlled output channel
        # content. Both this harness-marker source and the file-backed
        # source (read_output_channel_logs below) pipe through
        # redact_secrets at construction so the persisted ActivationReport
        # never holds raw API keys / DB URLs / OAuth tokens emitted by the
        # target extension. VS Code 1.105+ made the file-backed path the
        # primary source on production builds.
        text = redact_secrets(_truncate(str(payload.get("text", "") or "")))
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


# VS Code 1.105+ persists Output channel content under
# ``<user-data>/logs/<session>/window<N>/exthost/output_logging_<ts>/<idx>-<channel>.log``.
# Filename pattern: ``<numeric idx>-<channel name>.log``.
_OUTPUT_CHANNEL_FILE_RE = re.compile(r"^\d+-(?P<channel>.+)\.log$")


def read_output_channel_logs(
    logs_dir: Path | None = None,
    *,
    monitoring_start: float = 0.0,
) -> list[OutputSignalEvent]:
    """Return OutputSignalEvent records by reading VS Code's persisted
    Output channel files directly.

    VS Code 1.105+ no longer pipes extension ``console.log`` into
    ``exthost.log``; instead each Output channel's appendLine writes
    are persisted to ``output_logging_<ts>/<idx>-<channel>.log`` files.
    Reading those files directly is the reliable signal source —
    independent of the harness ``[extrace-harness]`` console.log shim,
    which silently drops in 1.105+.

    Lines that parse as JSON with a numeric ``ts`` field carry the
    extension-side emit timestamp; otherwise we fall back to the
    file's mtime as the per-line timestamp.
    """
    base_dir = logs_dir if logs_dir is not None else VSCODE_LOGS_DIR
    if base_dir is None or not base_dir.exists():
        return []

    events: list[OutputSignalEvent] = []
    for log_path in base_dir.glob("**/output_logging_*/*-*.log"):
        match = _OUTPUT_CHANNEL_FILE_RE.match(log_path.name)
        if match is None:
            continue
        channel = match.group("channel")
        try:
            content = log_path.read_text(errors="replace")
        except OSError:
            continue
        try:
            mtime_ms = log_path.stat().st_mtime * 1000.0
        except OSError:
            mtime_ms = 0.0

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            ts_ms = mtime_ms
            try:
                payload = json.loads(line)
            except (ValueError, TypeError):
                payload = None
            if isinstance(payload, dict):
                value = payload.get("ts")
                try:
                    if value is not None:
                        ts_ms = float(value)
                except (TypeError, ValueError):
                    pass

            timestamp, rel_time_s = _format_epoch_ms(ts_ms, monitoring_start)
            text = redact_secrets(_truncate(line))
            events.append(
                OutputSignalEvent(
                    timestamp=timestamp,
                    rel_time_s=rel_time_s,
                    channel=channel,
                    text=text,
                    summary=f"OutputChannel({channel}) appendLine",
                )
            )

    events.sort(key=lambda e: e.timestamp)
    return events


def merge_output_signal_events(
    *event_lists: list[OutputSignalEvent],
) -> list[OutputSignalEvent]:
    """Merge multiple OutputSignalEvent sources, deduplicating identical entries.

    Duplicates can arise when both ``parse_output_signal_events`` (legacy
    exthost-output marker source) and ``read_output_channel_logs``
    (VS Code 1.105+ file source) observe the same appendLine. Dedup key
    is ``(channel, text, timestamp)``.
    """
    seen: set[tuple[str, str, str]] = set()
    merged: list[OutputSignalEvent] = []
    for events in event_lists:
        for event in events:
            key = (event.channel, event.text, event.timestamp)
            if key in seen:
                continue
            seen.add(key)
            merged.append(event)
    merged.sort(key=lambda e: e.timestamp)
    return merged


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
