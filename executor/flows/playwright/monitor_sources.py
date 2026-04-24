"""Source collection and parsing helpers for activation monitoring."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

import re
from pathlib import Path

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import Page

    from . import commands, keyboard
    from .monitor_records import RunningExtension
    from .monitor_support import resolve_monitor_api
    from .runtime_capture._shared import _log
    from .runtime_capture.events import ActivationEntry
    from .runtime_capture.extension_host import (
        _activation_within_monitoring_window,
        _parse_activation_lines,
    )
except ImportError:  # pragma: no cover - top-level executor import mode
    import commands
    import keyboard
    from monitor_records import RunningExtension
    from monitor_support import resolve_monitor_api
    from runtime_capture._shared import _log
    from runtime_capture.events import ActivationEntry
    from runtime_capture.extension_host import (
        _activation_within_monitoring_window,
        _parse_activation_lines,
    )

    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import Page


_LAST_EXTHOST_LOG_COUNT: int = -1


def find_exthost_logs() -> list[Path]:
    """Find Extension Host log files (wrapper preserving monkeypatch points)."""
    global _LAST_EXTHOST_LOG_COUNT
    api = resolve_monitor_api()
    logs_dir = api.VSCODE_LOGS_DIR
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
    start_offsets: dict[str, int] | None = None,
) -> list[ActivationEntry]:
    """Find and parse all Extension Host log files."""
    api = resolve_monitor_api()
    all_entries: list[ActivationEntry] = []
    seen_entries: set[tuple[str, str, str, int | None, str]] = set()
    offsets = start_offsets or {}

    for log_path in api.find_exthost_logs():
        start_offset = offsets.get(str(log_path.resolve()), 0)
        for entry in api.parse_activations_from_log(
            log_path, start_offset=start_offset
        ):
            dedup_key = (
                entry.extension_id,
                entry.activation_event,
                entry.timestamp,
                entry.duration_ms,
                entry.source,
            )
            if dedup_key in seen_entries:
                continue
            seen_entries.add(dedup_key)
            all_entries.append(entry)

    return all_entries


def get_running_extensions(page: Page) -> list[RunningExtension]:
    """Open 'Developer: Show Running Extensions' and scrape extension list."""
    extensions: list[RunningExtension] = []
    try:
        _log("Opening Running Extensions view...")
        commands.run_command(page, "Developer: Show Running Extensions")
        page.wait_for_timeout(3000)

        rows = page.query_selector_all(".runtime-extensions-editor .monaco-list-row")

        if rows:
            for row in rows:
                text = row.inner_text()
                aria = row.get_attribute("aria-label") or ""
                ext = _parse_running_extension_row(text, aria)
                if ext:
                    extensions.append(ext)
            _log(f"Found {len(extensions)} running extension(s) via UI")
        else:
            _log("List rows not found in Running Extensions view")

    except PlaywrightError as exc:
        _log(f"Running Extensions scraping failed: {exc}")
    finally:
        try:
            page.keyboard.press(keyboard.CLOSE_EDITOR)
            page.wait_for_timeout(300)
        except PlaywrightError as exc:
            _log(f"Failed to close Running Extensions tab: {exc}")

    return extensions


def _parse_running_extension_row(
    text: str,
    aria_label: str = "",
) -> RunningExtension | None:
    """Parse a single row from the Running Extensions list."""
    if not text or not text.strip():
        return None

    lines = [
        line_text.strip()
        for line_text in text.strip().splitlines()
        if line_text.strip()
    ]
    if not lines:
        return None

    name = lines[0]
    timing = None

    for line in lines:
        time_match = re.search(r"(\d+)\s*ms", line)
        if time_match:
            timing = int(time_match.group(1))
            break

    ext_id = aria_label
    if ext_id and "." not in ext_id:
        ext_id = f"vscode.{ext_id}"

    if not ext_id:
        ext_id = name

    return RunningExtension(
        extension_id=ext_id,
        name=name,
        activation_time_ms=timing,
    )


def read_extension_host_output(page: Page | None = None) -> str:
    """Read Extension Host output from the log file directly."""
    _ = page
    api = resolve_monitor_api()
    _log("Reading Extension Host output from log file...")

    logs = api.find_exthost_logs()
    if logs:
        try:
            content = logs[0].read_text(errors="replace")
            _log(f"Read {len(content)} chars from {logs[0].name}")
            return content
        except OSError as exc:
            _log(f"Failed to read log file: {exc}")

    logs_dir = api.VSCODE_LOGS_DIR
    if logs_dir.exists():
        parts: list[str] = []
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


__all__ = [
    "_parse_running_extension_row",
    "find_exthost_logs",
    "get_running_extensions",
    "parse_activations_from_log",
    "parse_activations_from_output",
    "parse_all_exthost_logs",
    "read_extension_host_output",
]
