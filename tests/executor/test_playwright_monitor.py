from __future__ import annotations

import json
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


def test_activation_report_save_is_atomic(tmp_path: Path) -> None:
    report = monitor.ActivationReport(
        activated=[monitor.ActivationEntry(extension_id="sample.ext", source="log")],
        network_events=[
            monitor.NetworkEvent(
                timestamp="2026-01-01T10:00:00.000",
                rel_time_s=0.25,
                protocol="http",
                event_type="http_request",
                host="api.example.com",
                destination_port=443,
                summary="GET /api/health",
            )
        ],
        monitoring_start=0.0,
        monitoring_end=1.2,
    )
    output_path = tmp_path / "activation_report.json"
    output_path.write_text("stale-content")

    saved_path = report.save(output_path)

    assert saved_path == output_path
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["summary"]["total_activated"] == 1
    assert payload["summary"]["network_events"] == 1
    assert payload["activated"][0]["extension_id"] == "sample.ext"
    assert payload["network_events"][0]["host"] == "api.example.com"
    assert payload["network_summary"]["unique_hosts"] == 1
    assert not (tmp_path / ".activation_report.json.tmp").exists()


def test_parse_tshark_event_line_extracts_http_fields() -> None:
    line = (
        "1700000000.250\t10.0.0.2\t\t93.184.216.34\t\t443\t\t\t"
        "api.example.com\t/api/health\t\tHTTP\tGET /api/health HTTP/1.1"
    )

    event = monitor.parse_tshark_event_line(line, monitoring_start=1700000000.0)

    assert event is not None
    assert event.event_type == "http_request"
    assert event.protocol == "http"
    assert event.host == "api.example.com"
    assert event.destination_ip == "93.184.216.34"
    assert event.destination_port == 443
    assert event.rel_time_s == 0.25


def test_parse_strace_file_event_line_extracts_extension_io() -> None:
    line = (
        '1700000000.750 openat(AT_FDCWD, "/workspace/.env", ' "O_RDONLY|O_CLOEXEC) = 42"
    )

    event = monitor.parse_strace_file_event_line(line, monitoring_start=1700000000.0)

    assert event is not None
    assert event.operation == "read"
    assert event.path == "/workspace/.env"
    assert event.source == "extension"
    assert event.sensitive is True
    assert event.rel_time_s == 0.75


def test_parse_inotify_file_event_line_extracts_automation_io() -> None:
    event = monitor.parse_inotify_file_event_line(
        "/workspace/src/app.py\tCLOSE_WRITE,CLOSE\n",
        monitoring_start=1700000000.0,
        event_time=1700000001.5,
    )

    assert event is not None
    assert event.operation == "write"
    assert event.path == "/workspace/src/app.py"
    assert event.source == "automation"
    assert event.rel_time_s == 1.5


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


def test_parse_activations_from_log_preserves_distinct_events_and_parses_timestamp(
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
    assert [entry.extension_id for entry in entries] == [
        "dup.ext",
        "dup.ext",
        "other.ext",
    ]
    assert entries[0].activation_event == "onLanguage:python"
    assert entries[0].timestamp == "2026-01-01 10:00:00.123"
    assert entries[1].activation_event == "onCommand:test"
    assert entries[2].activation_event == "onStartupFinished"
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


def test_extension_monitor_stop_keeps_runtime_snapshot_separate(
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
    monkeypatch.setattr(
        monitor,
        "NetworkCapture",
        lambda monitoring_start, on_event=None: _FakeNetworkCapture(
            monitoring_start,
            on_event,
            [],
        ),
    )
    monkeypatch.setattr(
        monitor,
        "FileSystemCapture",
        lambda monitoring_start, on_event=None: _FakeFileCapture(
            monitoring_start,
            on_event,
            [],
        ),
    )
    monkeypatch.setattr(
        monitor,
        "ExtensionHostFileCapture",
        lambda monitoring_start, on_event=None: _FakeFileCapture(
            monitoring_start,
            on_event,
            [],
        ),
    )

    mon = monitor.ExtensionMonitor(DummyPage())
    mon.start()
    report = mon.stop()

    assert captured_offsets == expected_offsets
    assert report.log_file_path == str(log_file)
    assert report.extension_host_output == "output-lines"
    assert [entry.extension_id for entry in report.activated] == ["already.active"]
    assert [ext.extension_id for ext in report.running_extensions] == [
        "already.active",
        "new.ui",
    ]
    assert report.running_extensions[1].activation_time_ms == 21


def test_extension_monitor_persists_live_report_with_network_events(
    monkeypatch,
    tmp_path: Path,
) -> None:
    class DummyPage:
        pass

    network_event = monitor.NetworkEvent(
        timestamp="2026-01-01T10:00:00.000",
        rel_time_s=0.5,
        protocol="tls",
        event_type="tls_client_hello",
        source_ip="10.0.0.2",
        destination_ip="140.82.112.3",
        destination_port=443,
        host="github.com",
        summary="Client Hello",
    )

    monkeypatch.setattr(monitor, "_snapshot_log_offsets", lambda: {})
    monkeypatch.setattr(
        monitor,
        "parse_all_exthost_logs",
        lambda start_offsets=None: [],
    )
    monkeypatch.setattr(monitor, "find_exthost_logs", lambda: [])
    monkeypatch.setattr(monitor, "get_running_extensions", lambda page: [])
    monkeypatch.setattr(monitor, "read_extension_host_output", lambda page=None: "")
    monkeypatch.setattr(
        monitor,
        "NetworkCapture",
        lambda monitoring_start, on_event=None: _FakeNetworkCapture(
            monitoring_start,
            on_event,
            [network_event],
        ),
    )
    monkeypatch.setattr(
        monitor,
        "FileSystemCapture",
        lambda monitoring_start, on_event=None: _FakeFileCapture(
            monitoring_start,
            on_event,
            [],
        ),
    )
    monkeypatch.setattr(
        monitor,
        "ExtensionHostFileCapture",
        lambda monitoring_start, on_event=None: _FakeFileCapture(
            monitoring_start,
            on_event,
            [],
        ),
    )

    report_path = tmp_path / "live_report.json"
    mon = monitor.ExtensionMonitor(DummyPage(), report_path=report_path)
    mon.start()

    initial_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert initial_payload["network_events"][0]["host"] == "github.com"

    final_report = mon.stop()
    final_payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert final_report.network_events[0].host == "github.com"
    assert final_payload["network_summary"]["total_events"] == 1
    assert final_payload["summary"]["network_hosts"] == 1


def test_annotate_file_events_prefers_extension_trace_over_inotify_shadow() -> None:
    file_events = [
        monitor.FileEvent(
            timestamp="2026-01-01T10:00:00.500",
            rel_time_s=0.5,
            operation="read",
            path="/workspace/.env",
            source="automation",
            observer="inotify",
            summary="read: /workspace/.env",
        ),
        monitor.FileEvent(
            timestamp="2026-01-01T10:00:00.600",
            rel_time_s=0.6,
            operation="read",
            path="/workspace/.env",
            source="extension",
            observer="strace",
            summary="read: /workspace/.env",
        ),
        monitor.FileEvent(
            timestamp="2026-01-01T10:00:01.200",
            rel_time_s=1.2,
            operation="write",
            path="/workspace/src/app.py",
            source="automation",
            observer="inotify",
            scenario_name="coding_session",
            summary="write: /workspace/src/app.py",
        ),
    ]
    activations = [
        monitor.ActivationEntry(
            extension_id="ms-python.python",
            activation_event="onLanguage:python",
            timestamp="2026-01-01 10:00:00.650",
            source="log",
        )
    ]
    traces = [
        monitor.ScenarioTrace(
            name="coding_session",
            started_at=1767261600.0,
            ended_at=1767261602.0,
            status="completed",
        )
    ]

    annotated = monitor._annotate_file_events(file_events, activations, traces)

    assert len(annotated) == 2
    assert annotated[0].source == "extension"
    assert annotated[0].related_extension_id == "ms-python.python"
    assert annotated[1].source == "automation"
    assert annotated[1].scenario_name == "coding_session"


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


class _FakeNetworkCapture:
    def __init__(
        self,
        monitoring_start: float,
        on_event,
        events: list[monitor.NetworkEvent],
    ) -> None:
        self.monitoring_start = monitoring_start
        self.on_event = on_event
        self.events = events
        self.start_error = ""

    def start(self) -> None:
        if self.on_event is not None:
            for event in self.events:
                self.on_event(event)

    def stop(self) -> list[monitor.NetworkEvent]:
        return list(self.events)


class _FakeFileCapture:
    def __init__(
        self,
        monitoring_start: float,
        on_event,
        events: list[monitor.FileEvent],
    ) -> None:
        self.monitoring_start = monitoring_start
        self.on_event = on_event
        self.events = events
        self.start_error = ""

    def start(self) -> None:
        if self.on_event is not None:
            for event in self.events:
                self.on_event(event)

    def stop(self) -> list[monitor.FileEvent]:
        return list(self.events)
