"""W19-6-followup-2 [BUG marker-channel-destination]: pin the harness
marker channel glob.

The W19-X Bug B fix (commit ``8b7b7f6``) hardened the route by which
harness markers reach the parser: ``[extrace-harness]`` JSON-lines land
in VS Code's per-channel ``output_logging_<ts>/<idx>-ExTrace Harness.log``
file because ``launch_vscode.sh`` redirects Extension Host stdout to
``/dev/null``. ``find_harness_channel_logs()`` glob-resolves these files
under the resolved logs dir.

These tests pin the glob behavior end-to-end. A future refactor that
silently widened the glob (matching unrelated channel files) or narrowed
it (missing valid marker logs) would surface here rather than only on the
next live run.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from executor.flows.playwright.runtime_capture import extension_host
from executor.flows.playwright.runtime_capture.extension_host_log_parse import (
    find_harness_channel_logs,
)

_MARKER_FILENAME = "1-ExTrace Harness.log"


def _make_output_logging_dir(parent: Path, *, suffix: str = "20260526T120000") -> Path:
    target = parent / f"output_logging_{suffix}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_find_harness_channel_logs_returns_empty_when_logs_dir_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path / "missing")
    assert find_harness_channel_logs() == []


def test_find_harness_channel_logs_returns_empty_when_no_matching_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output_dir = _make_output_logging_dir(tmp_path)
    (output_dir / "2-Other Channel.log").write_text("noise", encoding="utf-8")
    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)

    assert find_harness_channel_logs() == []


def test_find_harness_channel_logs_picks_up_marker_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output_dir = _make_output_logging_dir(tmp_path)
    marker = output_dir / _MARKER_FILENAME
    marker.write_text("[extrace-harness] {}\n", encoding="utf-8")
    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)

    found = find_harness_channel_logs()

    assert found == [marker]


def test_find_harness_channel_logs_rejects_non_marker_siblings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output_dir = _make_output_logging_dir(tmp_path)
    marker = output_dir / _MARKER_FILENAME
    marker.write_text("[extrace-harness] {}\n", encoding="utf-8")
    (output_dir / "2-Other Channel.log").write_text("noise", encoding="utf-8")
    (output_dir / "ExTrace Harness.txt").write_text("wrong-ext", encoding="utf-8")
    (output_dir / "ExTrace Harness.log.bak").write_text("backup", encoding="utf-8")
    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)

    found = find_harness_channel_logs()

    assert found == [marker], (
        f"glob must accept only the *ExTrace Harness.log suffix on a "
        f"per-channel file inside output_logging_*/, got {found}"
    )


def test_find_harness_channel_logs_rejects_marker_outside_output_logging(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # File with the right name but NOT under output_logging_*/ — must be
    # rejected. The W19-X destination claim is specifically the per-channel
    # log file under the timestamped output_logging dir.
    stray = tmp_path / _MARKER_FILENAME
    stray.write_text("[extrace-harness] {}\n", encoding="utf-8")
    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)

    assert find_harness_channel_logs() == []


def test_find_harness_channel_logs_sorts_newest_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    older_dir = _make_output_logging_dir(tmp_path, suffix="20260101T000000")
    newer_dir = _make_output_logging_dir(tmp_path, suffix="20260601T000000")

    older = older_dir / _MARKER_FILENAME
    newer = newer_dir / _MARKER_FILENAME
    older.write_text("[extrace-harness] {}\n", encoding="utf-8")
    # Force a meaningful mtime gap so the sort is unambiguous on filesystems
    # with coarse mtime resolution.
    time.sleep(0.05)
    newer.write_text("[extrace-harness] {}\n", encoding="utf-8")
    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)

    found = find_harness_channel_logs()

    assert found == [newer, older], (
        "find_harness_channel_logs must return newest-first per its docstring"
    )
