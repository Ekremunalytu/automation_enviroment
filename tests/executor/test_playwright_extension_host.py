"""Direct-module tests for ``runtime_capture.extension_host``.

[FOLLOWUP w11-precursor-tests] safety net before the W11 ``monitor_lifecycle``
split. Imports the module by its real path (not via the ``monitor`` facade) so
the public parse/discovery surface is pinned independently of the facade
re-exports that the W11 refactor will rearrange.

Scope: pure parsers and the file-discovery helper. The strace-attached
``ExtensionHostFileCapture`` class is left to integration coverage — its
public state (``__init__`` defaults + ``pid`` property) is asserted only at the
shape level here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from executor.flows.playwright.runtime_capture import extension_host
from executor.flows.playwright.runtime_capture.events import ActivationEntry


# ---------------------------------------------------------------------------
# parse_activations_from_output — pure string parser
# ---------------------------------------------------------------------------


def test_parse_activations_from_output_empty_returns_empty() -> None:
    assert extension_host.parse_activations_from_output("") == []


def test_parse_activations_from_output_extracts_do_activate_pattern() -> None:
    output = (
        "[2026-01-01 10:00:01.000] [exthost] info "
        "ExtensionService#_doActivateExtension publisher.tool, "
        "activationEvent: 'onCommand:tool.run'"
    )

    entries = extension_host.parse_activations_from_output(output)

    assert len(entries) == 1
    assert entries[0].extension_id == "publisher.tool"
    assert entries[0].activation_event == "onCommand:tool.run"
    assert entries[0].source == "output"
    assert entries[0].timestamp == "2026-01-01 10:00:01.000"


def test_parse_activations_from_output_dedups_identical_entries() -> None:
    line = (
        "[2026-01-01 10:00:01.000] ExtensionService#_doActivateExtension "
        "publisher.tool, activationEvent: 'onCommand:tool.run'"
    )

    entries = extension_host.parse_activations_from_output("\n".join([line, line]))

    assert len(entries) == 1


def test_parse_activations_from_output_captures_eager_and_extension_activated() -> None:
    output = "\n".join(
        [
            "[2026-01-01 10:00:00.500] eager activation publisher.eager",
            "[2026-01-01 10:00:00.700] extension activated publisher.timed in 42 ms",
        ]
    )

    entries = extension_host.parse_activations_from_output(output)

    by_id = {e.extension_id: e for e in entries}
    assert "publisher.eager" in by_id
    assert "publisher.timed" in by_id
    assert by_id["publisher.timed"].duration_ms == 42


def test_parse_activations_from_output_emits_lifecycle_marker_types() -> None:
    output = "\n".join(
        [
            "[2026-01-01 10:00:00.100] activate(publisher.tool) entered",
            "[2026-01-01 10:00:00.200] activate(publisher.tool) returned in 17 ms",
            "[2026-01-01 10:00:00.300] registered command 'tool.run' for publisher.tool",
            "[2026-01-01 10:00:00.400] registered TaskProvider for publisher.tool",
        ]
    )

    entries = extension_host.parse_activations_from_output(output)
    markers = sorted({e.marker_type for e in entries if e.marker_type})

    assert "activate_fn_entry" in markers
    assert "activate_fn_exit" in markers
    assert "command_register" in markers
    assert "provider_register" in markers


# ---------------------------------------------------------------------------
# W15-5 I4 — tightened ``activate entered/returned <id>`` lifecycle markers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "line, expected_id, expected_marker, expected_ms",
    [
        # entry — explicit "for" keyword
        (
            "[2026-01-01 10:00:00.100] activateFunction entered for ms-python.python",
            "ms-python.python",
            "activate_fn_entry",
            None,
        ),
        # entry — no "for" keyword (legacy variant preserved)
        (
            "[2026-01-01 10:00:00.110] activate entered redhat.vscode-yaml",
            "redhat.vscode-yaml",
            "activate_fn_entry",
            None,
        ),
        # exit — "returned for <id> in <N>ms" with ms capture
        (
            "[2026-01-01 10:00:00.200] activate returned for ms-python.python in 42 ms",
            "ms-python.python",
            "activate_fn_exit",
            42,
        ),
        # exit — "completed <id>" no "for", no ms
        (
            "[2026-01-01 10:00:00.300] activate completed dbaeumer.vscode-eslint",
            "dbaeumer.vscode-eslint",
            "activate_fn_exit",
            None,
        ),
    ],
)
def test_lifecycle_marker_tightened_positive_cases(
    line: str,
    expected_id: str,
    expected_marker: str,
    expected_ms: int | None,
) -> None:
    """W15-5 I4: real publisher.name ids still match after the regex tightening."""
    entries = extension_host.parse_activations_from_output(line)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.extension_id == expected_id
    assert entry.marker_type == expected_marker
    assert entry.duration_ms == expected_ms


@pytest.mark.parametrize(
    "line",
    [
        # No id at all — pre-W15-5 the loose `.*?(?P<id>[\w.\-]+)` could capture
        # any trailing token; tightened regex requires a publisher.name shape.
        "[2026-01-01 10:00:00.000] activate entered",
        # id lacks a dot — `200` is not `<publisher>.<name>`.
        "[2026-01-01 10:00:00.000] activate returned 200",
        # Timestamp-like trailing token; `12:34:56.789` is not [\w-]+\.[\w.-]+
        # because the `:` characters fall outside the id charset.
        "[2026-01-01 10:00:00.000] activate entered 12:34:56.789",
        # Different verb ("activating", "activated") — only literal
        # "entered" / "returned" / "completed" should match.
        "[2026-01-01 10:00:00.000] activating ms-python.python",
        "[2026-01-01 10:00:00.000] activated returned ms-python.python",
    ],
)
def test_lifecycle_marker_tightened_rejects_broad_matches(line: str) -> None:
    """W15-5 I4: broad false-positive shapes the pre-W15-5 regex tolerated."""
    entries = extension_host.parse_activations_from_output(line)
    lifecycle_markers = [
        e.marker_type
        for e in entries
        if e.marker_type in {"activate_fn_entry", "activate_fn_exit"}
    ]

    assert lifecycle_markers == []


def test_parse_activations_from_output_filters_by_monitoring_start() -> None:
    """Entries whose timestamp predates ``monitoring_start`` are dropped."""
    # Pick a monitoring start at noon UTC; one entry is before, one after.
    before_line = (
        "[2026-01-01 11:59:59.000] ExtensionService#_doActivateExtension "
        "publisher.before, activationEvent: 'onStartupFinished'"
    )
    after_line = (
        "[2026-01-01 12:00:01.000] ExtensionService#_doActivateExtension "
        "publisher.after, activationEvent: 'onCommand:run'"
    )
    monitoring_start = extension_host._parse_iso_timestamp("2026-01-01 12:00:00.000")
    assert monitoring_start is not None

    entries = extension_host.parse_activations_from_output(
        "\n".join([before_line, after_line]),
        monitoring_start=monitoring_start,
    )

    ids = {e.extension_id for e in entries}
    assert "publisher.after" in ids
    assert "publisher.before" not in ids


# ---------------------------------------------------------------------------
# parse_activations_from_log — file IO + start_offset
# ---------------------------------------------------------------------------


def test_parse_activations_from_log_returns_empty_when_path_missing(
    tmp_path: Path,
) -> None:
    assert extension_host.parse_activations_from_log(tmp_path / "missing.log") == []


def test_parse_activations_from_log_reads_full_file_when_offset_zero(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "exthost.log"
    log_path.write_text(
        "[2026-01-01 10:00:00.000] eager activation publisher.tool\n",
        encoding="utf-8",
    )

    entries = extension_host.parse_activations_from_log(log_path)

    assert len(entries) == 1
    assert entries[0].extension_id == "publisher.tool"
    assert entries[0].source == "log"


def test_parse_activations_from_log_respects_start_offset(tmp_path: Path) -> None:
    """``start_offset`` skips already-consumed prefix bytes — incremental tail."""
    log_path = tmp_path / "exthost.log"
    prefix = "[2026-01-01 09:59:00.000] eager activation publisher.skipped\n"
    suffix = "[2026-01-01 10:00:00.000] eager activation publisher.kept\n"
    log_path.write_text(prefix + suffix, encoding="utf-8")

    entries = extension_host.parse_activations_from_log(
        log_path, start_offset=len(prefix.encode("utf-8"))
    )

    ids = [e.extension_id for e in entries]
    assert ids == ["publisher.kept"]


def test_parse_activations_from_log_clamps_negative_and_oversized_offsets(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "exthost.log"
    log_path.write_text(
        "[2026-01-01 10:00:00.000] eager activation publisher.tool\n",
        encoding="utf-8",
    )

    # Negative offset clamps to 0 → reads full file.
    entries = extension_host.parse_activations_from_log(log_path, start_offset=-50)
    assert len(entries) == 1

    # Oversized offset clamps to file size → reads nothing.
    huge_offset = log_path.stat().st_size + 1024
    assert (
        extension_host.parse_activations_from_log(log_path, start_offset=huge_offset)
        == []
    )


# ---------------------------------------------------------------------------
# parse_strace_process_event_line — pure strace line parser
# ---------------------------------------------------------------------------


def test_parse_strace_process_event_line_returns_none_on_unrelated_line() -> None:
    result = extension_host.parse_strace_process_event_line(
        "1700000000.000 read(0, 0x...) = 0",
        monitoring_start=0.0,
        root_pid=1,
        ppid_by_pid={},
        cwd_by_pid={},
    )
    assert result is None


def test_parse_strace_process_event_line_parses_execve_and_uses_cwd() -> None:
    cwd_by_pid: dict[int, str] = {1234: "/workspace"}
    ppid_by_pid: dict[int, int | None] = {1234: 100}

    event = extension_host.parse_strace_process_event_line(
        '[pid 1234] 1700000000.500 execve("/usr/bin/node", ["node", "ext.js"], 0x...) = 0',
        monitoring_start=1700000000.0,
        root_pid=100,
        ppid_by_pid=ppid_by_pid,
        cwd_by_pid=cwd_by_pid,
    )

    assert event is not None
    assert event.operation == "exec"
    assert event.command == "/usr/bin/node"
    assert event.pid == 1234
    assert event.ppid == 100
    assert event.cwd == "/workspace"
    assert event.rel_time_s == 0.5  # 1700000000.500 - 1700000000.0


def test_parse_strace_process_event_line_clone_records_child_ppid() -> None:
    ppid_by_pid: dict[int, int | None] = {}
    event = extension_host.parse_strace_process_event_line(
        "[pid 100] 1700000001.000 clone(child_stack=NULL) = 4242",
        monitoring_start=0.0,
        root_pid=100,
        ppid_by_pid=ppid_by_pid,
        cwd_by_pid={},
    )

    assert event is not None
    assert event.operation == "spawn"
    assert event.pid == 4242
    assert event.ppid == 100
    # Side effect: child PID is registered with its parent, so subsequent lines
    # for the child can resolve their ppid.
    assert ppid_by_pid[4242] == 100


def test_parse_strace_process_event_line_chdir_updates_cwd_table() -> None:
    cwd_by_pid: dict[int, str] = {}
    event = extension_host.parse_strace_process_event_line(
        '[pid 100] 1700000002.000 chdir("/workspace/work") = 0',
        monitoring_start=0.0,
        root_pid=100,
        ppid_by_pid={},
        cwd_by_pid=cwd_by_pid,
    )

    assert event is not None
    assert event.operation == "chdir"
    assert event.cwd == "/workspace/work"
    assert cwd_by_pid[100] == "/workspace/work"


def test_parse_strace_bounded_arguments_preview_truncates_long_args() -> None:
    """Arguments past the 256-byte budget are clipped with ellipsis (W12-5)."""
    long_arg = "A" * 400
    line = (
        f'[pid 100] 1700000003.000 execve("/usr/bin/node", '
        f'["node", "{long_arg}"], 0x...) = 0'
    )

    event = extension_host.parse_strace_process_event_line(
        line,
        monitoring_start=0.0,
        root_pid=100,
        ppid_by_pid={},
        cwd_by_pid={},
    )

    assert event is not None
    assert event.operation == "exec"
    # Preview honors the 256-byte budget and signals truncation with an ellipsis.
    assert len(event.arguments_preview) == 256
    assert event.arguments_preview.endswith("...")


@pytest.mark.parametrize(
    ("secret_class", "secret_literal", "expected_placeholder", "forbidden_substring"),
    [
        (
            "aws",
            "AKIAIOSFODNN7EXAMPLE",
            "[REDACTED:aws]",
            "AKIAIOSFODNN7EXAMPLE",
        ),
        (
            "bearer",
            "Bearer abcdef12345678",
            "[REDACTED:bearer]",
            "abcdef12345678",
        ),
        (
            "api_key",
            "api_key=abc123def456ghi",
            "[REDACTED:api_key]",
            "abc123def456ghi",
        ),
        (
            "db_url",
            "postgresql://user:hunter2@host/db",
            "[REDACTED:db_url]",
            "user:hunter2",
        ),
        (
            "private_key",
            # PEM markers built at runtime so the test source does not trip
            # `detect-private-key` (mirrors the pattern at
            # `tests/platform/security/test_output_signals_redaction.py:50-51`).
            "-----" + "BEGIN " + "PRIVATE " + "KEY-----"
            "abcdEFGH"
            "-----" + "END " + "PRIVATE " + "KEY-----",
            "[REDACTED:private_key]",
            "BEGIN " + "PRIVATE " + "KEY",
        ),
    ],
)
def test_parse_strace_event_arguments_preview_redacts_secrets(
    secret_class: str,
    secret_literal: str,
    expected_placeholder: str,
    forbidden_substring: str,
) -> None:
    """W13-6 — strace-parsed ``arguments_preview`` must route through ``redact_secrets()``.

    Each secret class lives inside a quoted strace argument; the parser strips
    the outer quotes and joins the remaining items into ``arguments_preview``.
    After W13-6 ``_bounded_arguments_preview()`` applies ``redact_secrets``
    before truncation, so the redaction placeholder must appear and the raw
    secret body must not.
    """
    line = (
        f'[pid 100] 1700000003.000 execve("/usr/bin/node", '
        f'["node", "{secret_literal}"], 0x...) = 0'
    )

    event = extension_host.parse_strace_process_event_line(
        line,
        monitoring_start=0.0,
        root_pid=100,
        ppid_by_pid={},
        cwd_by_pid={},
    )

    assert event is not None
    assert event.operation == "exec"
    assert expected_placeholder in event.arguments_preview, (
        f"{secret_class} placeholder missing from preview: {event.arguments_preview!r}"
    )
    assert forbidden_substring not in event.arguments_preview, (
        f"{secret_class} raw secret leaked into preview: {event.arguments_preview!r}"
    )


def test_parse_strace_clone_with_non_numeric_child_pid_returns_none() -> None:
    """A malformed clone return (e.g. ``= ?``) must not raise; just drop the line."""
    event = extension_host.parse_strace_process_event_line(
        "[pid 100] 1700000004.000 clone(child_stack=NULL) = ?",
        monitoring_start=0.0,
        root_pid=100,
        ppid_by_pid={},
        cwd_by_pid={},
    )

    assert event is None


def test_parse_strace_process_event_line_roundtrip_clone_then_execve() -> None:
    """Clone registers ppid; the subsequent execve on the child resolves it."""
    ppid_by_pid: dict[int, int | None] = {}
    cwd_by_pid: dict[int, str] = {100: "/workspace"}

    spawn = extension_host.parse_strace_process_event_line(
        "[pid 100] 1700000005.000 clone(child_stack=NULL) = 4242",
        monitoring_start=0.0,
        root_pid=100,
        ppid_by_pid=ppid_by_pid,
        cwd_by_pid=cwd_by_pid,
    )

    assert spawn is not None
    assert spawn.operation == "spawn"
    assert ppid_by_pid[4242] == 100

    exec_event = extension_host.parse_strace_process_event_line(
        '[pid 4242] 1700000005.500 execve("/usr/bin/node", ["node", "child.js"], 0x...) = 0',
        monitoring_start=0.0,
        root_pid=100,
        ppid_by_pid=ppid_by_pid,
        cwd_by_pid=cwd_by_pid,
    )

    assert exec_event is not None
    assert exec_event.operation == "exec"
    assert exec_event.pid == 4242
    # ppid resolution flows from the clone-side side effect on ppid_by_pid.
    assert exec_event.ppid == 100


# ---------------------------------------------------------------------------
# find_exthost_logs / parse_all_exthost_logs — filesystem discovery
# ---------------------------------------------------------------------------


def test_find_exthost_logs_returns_empty_when_root_missing(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path / "no_such_dir")
    assert extension_host.find_exthost_logs() == []


def test_find_exthost_logs_discovers_and_sorts_newest_first(
    tmp_path: Path, monkeypatch
) -> None:
    older = tmp_path / "20260101T000000" / "exthost1"
    newer = tmp_path / "20260102T000000" / "exthost1"
    older.mkdir(parents=True)
    newer.mkdir(parents=True)
    older_log = older / "exthost.log"
    newer_log = newer / "exthost.log"
    older_log.write_text("old\n", encoding="utf-8")
    newer_log.write_text("new\n", encoding="utf-8")

    import os

    # Force mtimes so ordering is deterministic regardless of write order.
    os.utime(older_log, (1_700_000_000, 1_700_000_000))
    os.utime(newer_log, (1_700_000_500, 1_700_000_500))

    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)
    found = extension_host.find_exthost_logs()

    assert [p.name for p in found] == ["exthost.log", "exthost.log"]
    assert found[0].resolve() == newer_log.resolve()
    assert found[1].resolve() == older_log.resolve()


def test_parse_all_exthost_logs_applies_per_file_start_offset(
    tmp_path: Path, monkeypatch
) -> None:
    log_dir = tmp_path / "20260101T000000" / "exthost1"
    log_dir.mkdir(parents=True)
    log_path = log_dir / "exthost.log"

    prefix = "[2026-01-01 09:59:00.000] eager activation publisher.skip\n"
    suffix = "[2026-01-01 10:00:00.000] eager activation publisher.keep\n"
    log_path.write_text(prefix + suffix, encoding="utf-8")

    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)
    offsets = {str(log_path.resolve()): len(prefix.encode("utf-8"))}

    entries = extension_host.parse_all_exthost_logs(start_offsets=offsets)

    assert [e.extension_id for e in entries] == ["publisher.keep"]


def test_parse_all_exthost_logs_dedups_across_files(
    tmp_path: Path, monkeypatch
) -> None:
    """Same activation in two log files collapses to one entry."""
    dir_a = tmp_path / "a" / "exthost1"
    dir_b = tmp_path / "b" / "exthost1"
    dir_a.mkdir(parents=True)
    dir_b.mkdir(parents=True)
    line = "[2026-01-01 10:00:00.000] eager activation publisher.tool\n"
    (dir_a / "exthost.log").write_text(line, encoding="utf-8")
    (dir_b / "exthost.log").write_text(line, encoding="utf-8")

    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)

    entries = extension_host.parse_all_exthost_logs()
    ids = [e.extension_id for e in entries]
    assert ids.count("publisher.tool") == 1


# ---------------------------------------------------------------------------
# read_extension_host_output — file fallback path
# ---------------------------------------------------------------------------


def test_read_extension_host_output_returns_empty_when_no_logs(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path / "missing")
    # ``page`` is intentionally None — we want the file-fallback path.
    assert extension_host.read_extension_host_output(page=None) == ""


def test_read_extension_host_output_reads_first_log_when_present(
    tmp_path: Path, monkeypatch
) -> None:
    log_dir = tmp_path / "20260101T000000" / "exthost1"
    log_dir.mkdir(parents=True)
    log_path = log_dir / "exthost.log"
    log_path.write_text("hello exthost\n", encoding="utf-8")

    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)

    output = extension_host.read_extension_host_output(page=None)
    assert "hello exthost" in output


# ---------------------------------------------------------------------------
# ExtensionHostFileCapture — shape only (no subprocess)
# ---------------------------------------------------------------------------


def test_extension_host_file_capture_initial_state_is_planned() -> None:
    cap = extension_host.ExtensionHostFileCapture(monitoring_start=0.0)

    assert cap.pid is None
    assert cap.events == []
    assert cap.process_events == []
    assert cap.start_error == ""
    assert cap.attach_attempts == 0
    assert cap.diagnostics["status"] == "planned"
    assert cap.diagnostics["selected_pid"] is None
    assert cap.diagnostics["failure_reason"] == ""


def test_extension_host_file_capture_stop_without_start_returns_empty_events() -> None:
    cap = extension_host.ExtensionHostFileCapture(monitoring_start=0.0)
    # ``stop()`` must be safe to call even when ``start()`` was never invoked.
    assert cap.stop() == []


# ---------------------------------------------------------------------------
# log_parse internal helpers (W12-5 split safety net)
# ---------------------------------------------------------------------------


def test_resolve_vscode_logs_dir_reads_facade_value_lazily(
    tmp_path: Path, monkeypatch
) -> None:
    """The W12-5 lazy facade lookup must honor a monkey-patched VSCODE_LOGS_DIR.

    23-case W11 precursor suite already monkey-patches
    ``extension_host.VSCODE_LOGS_DIR`` to redirect file discovery into a
    fixture directory. Post-W12-5, ``find_exthost_logs`` lives in
    ``extension_host_log_parse`` but reads ``VSCODE_LOGS_DIR`` through the
    facade via a lazy ``_resolve_vscode_logs_dir`` helper. This test pins
    the lazy-lookup invariant so a future cleanup that hoists the import
    would fire here before the precursor suite breaks.
    """
    from executor.flows.playwright.runtime_capture import (
        extension_host_log_parse,
    )

    monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)
    assert extension_host_log_parse._resolve_vscode_logs_dir() == tmp_path


def test_activation_within_monitoring_window_includes_event_at_exact_start() -> None:
    """An activation whose timestamp equals ``monitoring_start`` is kept."""
    monitoring_start = extension_host._parse_iso_timestamp("2026-01-01 10:00:00.000")
    assert monitoring_start is not None

    entries = extension_host.parse_activations_from_output(
        "[2026-01-01 10:00:00.000] eager activation publisher.boundary",
        monitoring_start=monitoring_start,
    )

    assert [e.extension_id for e in entries] == ["publisher.boundary"]


def test_activation_within_monitoring_window_drops_event_just_before_start() -> None:
    """A 1ms-earlier activation is dropped — boundary check is inclusive on the right."""
    monitoring_start = extension_host._parse_iso_timestamp("2026-01-01 10:00:00.000")
    assert monitoring_start is not None

    entries = extension_host.parse_activations_from_output(
        "[2026-01-01 09:59:59.999] eager activation publisher.early",
        monitoring_start=monitoring_start,
    )

    assert entries == []


# ---------------------------------------------------------------------------
# Sanity guard — ActivationEntry is the public dataclass
# ---------------------------------------------------------------------------


def test_parse_activations_returns_activation_entry_instances() -> None:
    output = "[2026-01-01 10:00:00.000] eager activation publisher.tool"
    entries = extension_host.parse_activations_from_output(output)

    assert all(isinstance(e, ActivationEntry) for e in entries)
