"""Unit tests for the /proc PPID/cwd backfill helpers (Workstream 1).

These seed parent/cwd lineage for processes that already exist when strace
attaches (and so never emit a clone/fork/vfork line for strace to observe).
The helpers read ``/proc`` directly, so the tests fake ``Path.read_text`` /
``os.readlink`` to stay deterministic and host-independent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from executor.flows.playwright.runtime_capture import _shared
from executor.flows.playwright.runtime_capture._shared import (
    _read_proc_ppid,
    backfill_ppids_from_proc,
)


def _fake_read_text(mapping: dict[str, str]):
    """Build a ``Path.read_text`` replacement backed by a path->content map."""

    def _reader(self: Path, *_args: object, **_kwargs: object) -> str:
        key = str(self)
        if key in mapping:
            return mapping[key]
        raise FileNotFoundError(key)

    return _reader


def test_read_proc_ppid_prefers_status_ppid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        Path,
        "read_text",
        _fake_read_text({"/proc/100/status": "Name:\tnode\nPPid:\t42\nUid:\t0\n"}),
    )
    assert _read_proc_ppid(100) == 42


def test_read_proc_ppid_falls_back_to_stat_field_four(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # status missing -> parse /proc/<pid>/stat: "pid (comm) state ppid ...".
    monkeypatch.setattr(
        Path,
        "read_text",
        _fake_read_text({"/proc/200/stat": "200 (node) S 55 200 200 0 -1 ..."}),
    )
    assert _read_proc_ppid(200) == 55


def test_read_proc_ppid_handles_comm_with_spaces_and_parens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The comm field can contain spaces and parentheses; parsing must key off
    # the FINAL ')' so the ppid token is read correctly.
    monkeypatch.setattr(
        Path,
        "read_text",
        _fake_read_text({"/proc/300/stat": "300 (weird (cmd) name) R 77 300 ..."}),
    )
    assert _read_proc_ppid(300) == 77


def test_read_proc_ppid_returns_none_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "read_text", _fake_read_text({}))
    assert _read_proc_ppid(999999) is None


def test_backfill_seeds_ppid_and_cwd(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_shared, "_read_proc_ppid", lambda pid: {7: 1, 8: 7}.get(pid))
    monkeypatch.setattr(
        _shared, "_read_proc_cwd", lambda pid: {7: "/workspace"}.get(pid, "")
    )

    ppid_by_pid: dict[int, int | None] = {}
    cwd_by_pid: dict[int, str] = {}
    backfill_ppids_from_proc([7, 8], ppid_by_pid, cwd_by_pid=cwd_by_pid)

    assert ppid_by_pid == {7: 1, 8: 7}
    assert cwd_by_pid == {7: "/workspace"}


def test_backfill_does_not_clobber_observed_lineage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # An entry already observed from a live clone line must win over the
    # /proc snapshot (last-writer-wins, observed parentage authoritative).
    monkeypatch.setattr(_shared, "_read_proc_ppid", lambda pid: 1)
    monkeypatch.setattr(_shared, "_read_proc_cwd", lambda pid: "")

    ppid_by_pid: dict[int, int | None] = {5: 99}
    backfill_ppids_from_proc([5], ppid_by_pid)

    assert ppid_by_pid == {5: 99}
