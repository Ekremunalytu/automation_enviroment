from __future__ import annotations

import sys
from pathlib import Path

PLAYWRIGHT_DIR = Path(__file__).resolve().parents[2] / "executor" / "playwright"
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import monitor  # noqa: E402


def test_parse_activations_from_log_respects_start_offset(tmp_path: Path) -> None:
    log_file = tmp_path / "exthost.log"
    old_line = "activating extension 'old.publisher' because of 'onLanguage:python'\n"
    new_line = "activating extension 'new.publisher' because of 'onCommand:test'\n"
    log_file.write_text(old_line + new_line)

    start_offset = len(old_line.encode("utf-8"))
    entries = monitor.parse_activations_from_log(log_file, start_offset=start_offset)

    assert [entry.extension_id for entry in entries] == ["new.publisher"]
    assert entries[0].activation_event == "onCommand:test"


def test_parse_all_exthost_logs_uses_per_file_offsets(
    monkeypatch,
    tmp_path: Path,
) -> None:
    first_log = tmp_path / "first.log"
    second_log = tmp_path / "second.log"

    first_old = "activating extension 'first.old' because of 'onStartupFinished'\n"
    first_new = "activating extension 'first.new' because of 'onView:explorer'\n"
    second_line = "activating extension 'second.ext' because of 'onLanguage:json'\n"

    first_log.write_text(first_old + first_new)
    second_log.write_text(second_line)

    monkeypatch.setattr(monitor, "find_exthost_logs", lambda: [first_log, second_log])

    offsets = {
        str(first_log.resolve()): len(first_old.encode("utf-8")),
    }
    entries = monitor.parse_all_exthost_logs(start_offsets=offsets)

    assert [entry.extension_id for entry in entries] == ["first.new", "second.ext"]


def test_parse_activations_from_log_deduplicates_and_parses_timestamp(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "exthost.log"
    log_file.write_text(
        "[2026-01-01 10:00:00.123] activating extension 'dup.ext' because of "
        "'onLanguage:python'\n"
        "[2026-01-01 10:00:00.456] activating extension 'dup.ext' because of "
        "'onCommand:test'\n"
        "2026-01-01 10:00:01.000 ExtensionService#_doActivateExtension other.ext "
        "activationEvent: 'onStartupFinished'\n"
    )

    entries = monitor.parse_activations_from_log(log_file, start_offset=-10)
    assert [entry.extension_id for entry in entries] == ["dup.ext", "other.ext"]
    assert entries[0].activation_event == "onLanguage:python"
    assert entries[0].timestamp == "2026-01-01 10:00:00.123"
    assert entries[1].activation_event == "onStartupFinished"
    assert all(entry.source == "log" for entry in entries)

    beyond_eof_entries = monitor.parse_activations_from_log(
        log_file,
        start_offset=999_999,
    )
    assert beyond_eof_entries == []


def test_parse_running_extension_row_handles_builtin_and_fallback_id() -> None:
    built_in = monitor._parse_running_extension_row(
        text="Git\n1.0.0\nStartup Activation: 39ms",
        aria_label="git",
    )
    assert built_in is not None
    assert built_in.extension_id == "vscode.git"
    assert built_in.name == "Git"
    assert built_in.activation_time_ms == 39

    marketplace = monitor._parse_running_extension_row(
        text="Python\nActivation: 125ms",
        aria_label="ms-python.python",
    )
    assert marketplace is not None
    assert marketplace.extension_id == "ms-python.python"
    assert marketplace.activation_time_ms == 125

    fallback = monitor._parse_running_extension_row(
        text="Custom Extension\nActivation: 15ms",
        aria_label="",
    )
    assert fallback is not None
    assert fallback.extension_id == "Custom Extension"
    assert fallback.activation_time_ms == 15

    assert monitor._parse_running_extension_row("", aria_label="git") is None


def test_read_extension_host_output_falls_back_to_exthost_rglob(
    monkeypatch,
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "session" / "window1" / "exthost" / "exthost.log"
    log_file.parent.mkdir(parents=True)
    log_file.write_text("extension activated ms-python.python in 12ms\n")

    monkeypatch.setattr(monitor, "find_exthost_logs", lambda: [])
    monkeypatch.setattr(monitor, "VSCODE_LOGS_DIR", tmp_path)

    output = monitor.read_extension_host_output()

    assert "--- exthost.log ---" in output
    assert "ms-python.python" in output


def test_extension_monitor_stop_merges_new_ui_entries(
    monkeypatch,
    tmp_path: Path,
) -> None:
    class DummyPage:
        pass

    expected_offsets = {"snapshot.log": 42}
    captured_offsets: dict[str, int] | None = None

    def fake_parse_all_exthost_logs(start_offsets=None):
        nonlocal captured_offsets
        captured_offsets = start_offsets
        return [monitor.ActivationEntry(extension_id="already.active", source="log")]

    log_file = tmp_path / "exthost.log"
    log_file.write_text("content")

    monkeypatch.setattr(monitor, "_snapshot_log_offsets", lambda: expected_offsets)
    monkeypatch.setattr(monitor, "parse_all_exthost_logs", fake_parse_all_exthost_logs)
    monkeypatch.setattr(monitor, "find_exthost_logs", lambda: [log_file])
    monkeypatch.setattr(
        monitor,
        "get_running_extensions",
        lambda page: [
            monitor.RunningExtension(
                extension_id="already.active",
                activation_time_ms=5,
            ),
            monitor.RunningExtension(extension_id="new.ui", activation_time_ms=21),
        ],
    )
    monkeypatch.setattr(
        monitor, "read_extension_host_output", lambda page=None: "output-lines"
    )

    mon = monitor.ExtensionMonitor(DummyPage())
    mon.start()
    report = mon.stop()

    assert captured_offsets == expected_offsets
    assert report.log_file_path == str(log_file)
    assert report.extension_host_output == "output-lines"
    assert [entry.extension_id for entry in report.activated] == [
        "already.active",
        "new.ui",
    ]
    assert report.activated[1].source == "ui"
    assert report.activated[1].duration_ms == 21


def test_check_extension_activated_uses_logs_then_ui(monkeypatch) -> None:
    monkeypatch.setattr(
        monitor,
        "parse_all_exthost_logs",
        lambda: [monitor.ActivationEntry(extension_id="from.log")],
    )
    monkeypatch.setattr(
        monitor,
        "get_running_extensions",
        lambda page: [monitor.RunningExtension(extension_id="from.ui")],
    )

    assert monitor.check_extension_activated("from.log") is True
    assert monitor.check_extension_activated("from.ui", page=object()) is True
    assert monitor.check_extension_activated("missing", page=object()) is False
