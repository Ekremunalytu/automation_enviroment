"""Extension Host log discovery and activation parsing (W12-5 split from extension_host.py)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ._shared import _log, _parse_iso_timestamp
from .events import ActivationEntry

# Patterns found in VS Code Extension Host logs (--log trace)
# These cover multiple VS Code versions.
_ACTIVATION_PATTERNS = [
    # "ExtensionService#_doActivateExtension <id>, ..."
    re.compile(
        r"ExtensionService#_doActivateExtension\s+(?P<id>[\w.\-]+)"
        r"(?:.*?activationEvent:\s*'(?P<event>[^']*)')?"
    ),
    # "extension activated <id> in <N>ms"
    re.compile(
        r"extension activated\s+(?P<id>[\w.\-]+)" r"(?:.*?in\s+(?P<ms>\d+)\s*ms)?"
    ),
    # "activating extension '<id>' because of '<event>'"
    re.compile(
        r"activating extension\s+'(?P<id>[^']+)'"
        r"(?:.*?because of\s+'(?P<event>[^']*)')?"
    ),
    # "eager activation <id>"
    re.compile(r"eager\s+activation\s+(?P<id>[\w.\-]+)"),
    # "[info] <id>: extension activated successfully"
    # S5 ReDoS-sweep: this is the only pattern that leads with an *unanchored*
    # greedy prefix (every other pattern starts with a required literal that
    # ``.search`` anchors to). An unbounded ``[\w.\-]+`` before the required
    # ``:`` backtracks O(n^2) on a colon-less mega-line; bounding it to a length
    # no real extension id approaches (publisher.name is <128 chars) makes the
    # prefix linear without changing any legitimate match.
    re.compile(
        r"(?P<id>[\w.\-]{1,256}):\s+extension activated" r"(?:.*?(?P<ms>\d+)\s*ms)?"
    ),
    # "ExtHostExtensionService#_doActivateExtension ..."
    re.compile(
        r"ExtHostExtensionService#.*activat\w*\s+(?P<id>[\w.\-]+)"
        r"(?:.*?'(?P<event>[^']*)')?"
    ),
]

# Lifecycle marker patterns enrich event_attempts correlation in
# health_reconciliation (PR345 PR3). Each entry is (compiled_pattern,
# marker_type) where marker_type ends up on ActivationEntry.marker_type.
# Kept sibling to _ACTIVATION_PATTERNS so the existing dedup contract
# (entry per (id, event, timestamp, duration_ms)) stays intact for the
# default activation path; lifecycle entries dedup on the same tuple
# extended with marker_type.
_LIFECYCLE_MARKER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # "activate(<id>) entered"
    (
        re.compile(r"activate(?:Function)?\s*\((?P<id>[\w.\-]+)\)\s*entered"),
        "activate_fn_entry",
    ),
    # "activateFunction entered for <id>" / "activate entered <id>"
    # W15-5 I4: require an explicit \s+ anchor and the VS Code extension-id
    # shape ``<publisher>.<name>`` to keep the previously loose ``.*?`` from
    # capturing peer ids or timestamps as the activation target.
    (
        re.compile(
            r"activate(?:Function)?\s+entered(?:\s+for)?\s+(?P<id>[\w-]+\.[\w.\-]+)"
        ),
        "activate_fn_entry",
    ),
    # "activate(<id>) returned in 42ms" / "activate(<id>) completed"
    (
        re.compile(
            r"activate(?:Function)?\s*\((?P<id>[\w.\-]+)\)\s*"
            r"(?:returned|completed)"
            r"(?:.*?in\s+(?P<ms>\d+)\s*ms)?"
        ),
        "activate_fn_exit",
    ),
    # "activate returned for <id> in <N>ms" / "activate completed <id>"
    # W15-5 I4: same tightening — explicit \s+ anchor + publisher.name id shape.
    (
        re.compile(
            r"activate(?:Function)?\s+"
            r"(?:returned|completed)(?:\s+for)?\s+(?P<id>[\w-]+\.[\w.\-]+)"
            r"(?:\s+in\s+(?P<ms>\d+)\s*ms)?"
        ),
        "activate_fn_exit",
    ),
    # "registered command 'extrace.example.run' for <id>"
    (
        re.compile(
            r"register(?:ed|ing)?\s+command\s+'(?P<event>[^']+)'"
            r"(?:.*?(?:for|by|from)\s+(?P<id>[\w.\-]+))?"
        ),
        "command_register",
    ),
    # "registered FooProvider for <id>"
    (
        re.compile(
            r"register(?:ed|ing)?\s+(?P<event>\w+Provider)"
            r"(?:.*?(?:for|by|from)\s+(?P<id>[\w.\-]+))?"
        ),
        "provider_register",
    ),
]

# Timestamp pattern at start of VS Code log lines
_TIMESTAMP_RE = re.compile(r"^\[?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\]?")

# S5 ReDoS-sweep (W23) hygiene bound. Every activation/lifecycle pattern above
# is matched per-line, and the audit confirmed none has the nested-quantifier
# shape that drives exponential backtracking. The one residual edge is the set
# of unanchored greedy-prefix id patterns (``[\w.\-]+`` before a required
# literal), which backtrack O(n^2) on a single adversarial mega-line. Real VS
# Code activation markers sit at the head of the line (id/event well under a
# few hundred chars), so truncating an absurdly long line to a generous bound
# removes the only super-linear edge without dropping any real activation.
_MAX_PARSE_LINE_LEN = 16_384


def _parse_activation_lines(lines: list[str], *, source: str) -> list[ActivationEntry]:
    entries: list[ActivationEntry] = []
    seen: set[tuple[str, str, str, int | None, str]] = set()

    for line in lines:
        # S5 hygiene: bound the input to the per-line patterns so the
        # unanchored greedy-prefix ids cannot be driven into O(n^2)
        # backtracking by a single pathological mega-line (see
        # _MAX_PARSE_LINE_LEN). The marker/id/event live at the head of the
        # line, so this never drops a real activation.
        if len(line) > _MAX_PARSE_LINE_LEN:
            line = line[:_MAX_PARSE_LINE_LEN]
        lowered = line.lower()
        if "activ" not in lowered and "register" not in lowered:
            continue

        ts_match = _TIMESTAMP_RE.match(line)
        timestamp = ts_match.group(1) if ts_match else ""

        matched = False
        for pattern in _ACTIVATION_PATTERNS:
            match = pattern.search(line)
            if match is None:
                continue

            ext_id = match.group("id")
            event = match.groupdict().get("event", "") or ""
            ms_str = match.groupdict().get("ms")
            duration_ms = int(ms_str) if ms_str else None
            dedup_key = (ext_id, event, timestamp, duration_ms, "")

            if dedup_key in seen:
                matched = True
                break

            seen.add(dedup_key)
            entries.append(
                ActivationEntry(
                    extension_id=ext_id,
                    activation_event=event,
                    duration_ms=duration_ms,
                    timestamp=timestamp,
                    source=source,
                )
            )
            matched = True
            break

        if matched:
            continue

        for pattern, marker_type in _LIFECYCLE_MARKER_PATTERNS:
            match = pattern.search(line)
            if match is None:
                continue

            ext_id = match.groupdict().get("id") or ""
            if not ext_id:
                continue

            event = match.groupdict().get("event", "") or ""
            ms_str = match.groupdict().get("ms")
            duration_ms = int(ms_str) if ms_str else None
            dedup_key = (ext_id, event, timestamp, duration_ms, marker_type)

            if dedup_key in seen:
                break

            seen.add(dedup_key)
            entries.append(
                ActivationEntry(
                    extension_id=ext_id,
                    activation_event=event,
                    duration_ms=duration_ms,
                    timestamp=timestamp,
                    source=source,
                    marker_type=marker_type,
                )
            )
            break

    return entries


def _activation_within_monitoring_window(
    entry: ActivationEntry,
    monitoring_start: float,
) -> bool:
    if monitoring_start <= 0:
        return True

    event_epoch = _parse_iso_timestamp(entry.timestamp)
    if event_epoch is None:
        return True

    return event_epoch >= monitoring_start


_LAST_EXTHOST_LOG_COUNT: int = -1


def _resolve_vscode_logs_dir() -> Path:
    # W12-5: resolve via the facade so tests that monkey-patch
    # ``extension_host.VSCODE_LOGS_DIR`` continue to take effect after the
    # ahtapot split. Lazy import — the facade module is fully loaded by the
    # time any function below is invoked.
    from . import extension_host as _facade

    return _facade.VSCODE_LOGS_DIR


def find_exthost_logs() -> list[Path]:
    """Find all Extension Host log files under the VS Code logs directory.

    Returns paths sorted newest-first.
    """
    global _LAST_EXTHOST_LOG_COUNT
    logs_dir = _resolve_vscode_logs_dir()
    if not logs_dir.exists():
        if _LAST_EXTHOST_LOG_COUNT != -2:
            _log(f"Log directory not found: {logs_dir}")
            _LAST_EXTHOST_LOG_COUNT = -2
        return []

    patterns = ["**/exthost*/exthost.log", "**/exthost*.log"]
    found: list[Path] = []
    for pattern in patterns:
        found.extend(logs_dir.glob(pattern))

    seen: set[str] = set()
    unique: list[Path] = []
    for p in sorted(found, key=lambda x: x.stat().st_mtime, reverse=True):
        canon = str(p.resolve())
        if canon not in seen:
            seen.add(canon)
            unique.append(p)

    if len(unique) != _LAST_EXTHOST_LOG_COUNT:
        _log(f"Found {len(unique)} Extension Host log file(s)")
        _LAST_EXTHOST_LOG_COUNT = len(unique)
    return unique


def parse_activations_from_log(
    log_path: Path,
    start_offset: int = 0,
) -> list[ActivationEntry]:
    """Parse a single Extension Host log file for activation events."""
    if not log_path.exists():
        return []

    raw = log_path.read_bytes()
    if start_offset < 0:
        start_offset = 0
    if start_offset > len(raw):
        start_offset = len(raw)

    content = raw[start_offset:].decode("utf-8", errors="replace")
    entries = _parse_activation_lines(content.splitlines(), source="log")

    _log(f"Parsed {len(entries)} activation(s) from {log_path.name}")
    return entries


def parse_all_exthost_logs(
    start_offsets: Mapping[str, int] | None = None,
) -> list[ActivationEntry]:
    """Find and parse all Extension Host log files.

    Args:
        start_offsets: Optional map of ``resolved_log_path -> byte_offset``.
            If provided, only content appended after the given offset is parsed.
    """
    all_entries: list[ActivationEntry] = []
    seen_entries: set[tuple[str, str, str, int | None, str, str]] = set()
    offsets = start_offsets or {}

    for log_path in find_exthost_logs():
        start_offset = offsets.get(str(log_path.resolve()), 0)
        # W22 rotation guard: ``_snapshot_log_offsets`` records each log's SIZE
        # at monitor start, and Extension Host logs only grow (append) — UNLESS
        # a window reload (a contributed ``*reload*`` command, or
        # ``--reload-before-run``) rotates ``exthost.log`` -> ``exthost.1.log``
        # and starts a fresh, smaller ``exthost.log``. When the recorded offset
        # exceeds the file's current size the tail offset is stale, so parse
        # the whole (rotated) file instead of skipping it — otherwise the
        # post-reload activations are dropped and the target extension is
        # reported as "never activated" even though it clearly activated.
        try:
            if start_offset > log_path.stat().st_size:
                start_offset = 0
        except OSError:
            start_offset = 0
        for entry in parse_activations_from_log(log_path, start_offset=start_offset):
            dedup_key = (
                entry.extension_id,
                entry.activation_event,
                entry.timestamp,
                entry.duration_ms,
                entry.source,
                entry.marker_type,
            )
            if dedup_key in seen_entries:
                continue
            seen_entries.add(dedup_key)
            all_entries.append(entry)

    return all_entries


def find_harness_channel_logs() -> list[Path]:
    """Find ``ExTrace Harness`` output channel log files.

    Harness markers (``[extrace-harness]`` JSON-line) land here, not in
    exthost.log, because launch_vscode.sh redirects VS Code stdout to
    /dev/null — Extension Host ``console.log`` output is therefore
    discarded. The harness extension routes markers through
    ``outputChannel.appendLine`` instead, which VS Code persists to a
    per-channel log file under ``output_logging_*/``.
    """
    logs_dir = _resolve_vscode_logs_dir()
    if not logs_dir.exists():
        return []
    found = list(logs_dir.glob("**/output_logging_*/*ExTrace Harness.log"))
    return sorted(found, key=lambda x: x.stat().st_mtime, reverse=True)


def read_extension_host_output(page: Any = None) -> str:
    """Read Extension Host output from the log file directly.

    This is more reliable than trying to scrape the Output panel via
    Playwright, since the Output channel picker can behave unpredictably.

    Falls back to reading the exthost.log file which contains the same data.
    """
    _ = page
    _log("Reading Extension Host output from log file...")

    parts: list[str] = []

    # Read directly from the Extension Host log file (most reliable for
    # activation entries + provider trace).
    logs = find_exthost_logs()
    if logs:
        try:
            parts.append(logs[0].read_text(errors="replace"))
            _log(f"Read {len(parts[-1])} chars from {logs[0].name}")
        except OSError as exc:
            _log(f"Failed to read log file: {exc}")

    # Harness channel log files carry the stimulus markers (see
    # find_harness_channel_logs docstring for why they live separately).
    for harness_log in find_harness_channel_logs():
        try:
            parts.append(harness_log.read_text(errors="replace"))
            _log(f"Read {len(parts[-1])} chars from {harness_log.name}")
        except OSError as exc:
            _log(f"Failed to read harness channel log {harness_log.name}: {exc}")

    if parts:
        return "\n".join(parts)

    # Fallback: try all per-extension log files
    logs_dir = _resolve_vscode_logs_dir()
    if logs_dir.exists():
        for log_file in sorted(logs_dir.rglob("*.log")):
            if "exthost" in str(log_file):
                try:
                    parts.append(
                        f"--- {log_file.name} ---\n{log_file.read_text(errors='replace')}"
                    )
                except OSError:
                    continue
        if parts:
            content = "\n".join(parts)
            _log(f"Read {len(content)} chars from {len(parts)} exthost log file(s)")
            return content

    _log("No Extension Host log files found")
    return ""


def parse_activations_from_output(
    output: str,
    *,
    monitoring_start: float = 0.0,
) -> list[ActivationEntry]:
    """Parse activation entries from final Extension Host output."""
    entries = _parse_activation_lines(output.splitlines(), source="output")
    return [
        entry
        for entry in entries
        if _activation_within_monitoring_window(entry, monitoring_start)
    ]
