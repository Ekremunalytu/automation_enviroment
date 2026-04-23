from __future__ import annotations

import json
import sys
from pathlib import Path

from packages.analysis_contracts import TriggerPayload

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import monitor  # noqa: E402


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
        return [
            monitor.ActivationEntry(
                extension_id="already.active",
                activation_event="onStartupFinished",
                timestamp="2026-01-01 10:00:00.500",
                source="log",
            ),
            monitor.ActivationEntry(
                extension_id="other.extension",
                activation_event="onCommand:test",
                timestamp="2026-01-01 10:00:01.500",
                source="log",
            ),
        ]

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

    mon = monitor.ExtensionMonitor(
        DummyPage(),
        target_extension_id="already.active",
    )
    mon.start()
    mon.record_scenario_event(
        "start",
        "coding_session",
        metadata={"intent": "exercise editor workflows"},
    )
    mon.record_scenario_event(
        "end",
        "coding_session",
        "completed",
        metadata={"intent": "exercise editor workflows"},
    )
    report = mon.stop()

    assert captured_offsets == expected_offsets
    assert report.log_file_path == str(log_file)
    assert report.extension_host_output == "output-lines"
    assert [entry.extension_id for entry in report.activated] == [
        "already.active",
        "other.extension",
    ]
    assert [ext.extension_id for ext in report.running_extensions] == [
        "already.active",
        "new.ui",
    ]
    assert report.running_extensions[1].activation_time_ms == 21
    assert (
        report.log_streams["target_extension_host"][0].extension_id == "already.active"
    )
    assert (
        report.log_streams["other_extension_host"][0].extension_id == "other.extension"
    )
    assert report.log_streams["automation"][0].kind == "scenario"
    assert report.target_extension_observed is True
    assert report.run_quality in {"medium", "high"}


def test_extension_monitor_stop_reconciles_startup_activation_from_output(
    monkeypatch,
) -> None:
    class DummyPage:
        pass

    waited: list[float] = []

    monkeypatch.setattr(monitor, "_snapshot_log_offsets", lambda: {})
    monkeypatch.setattr(
        monitor,
        "parse_all_exthost_logs",
        lambda start_offsets=None: [],
    )
    monkeypatch.setattr(monitor, "find_exthost_logs", lambda: [])
    monkeypatch.setattr(monitor, "get_running_extensions", lambda page: [])
    monkeypatch.setattr(
        monitor,
        "read_extension_host_output",
        lambda page=None: (
            "[2026-01-01 10:00:00.500] activating extension "
            "'esbenp.prettier-vscode' because of 'onStartupFinished'\n"
        ),
    )
    monkeypatch.setattr(monitor.time, "sleep", lambda seconds: waited.append(seconds))
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

    mon = monitor.ExtensionMonitor(
        DummyPage(),
        target_extension_id="esbenp.prettier-vscode",
    )
    mon.start()
    mon.report.monitoring_start = monitor._parse_iso_timestamp(
        "2026-01-01 10:00:00.000"
    )
    mon.report.event_attempts = [
        monitor.EventAttemptRecord(
            attempt_id="startup",
            declared_event="onStartupFinished",
            activation_event="onStartupFinished",
            event_family="onStartupFinished",
            track="official",
        )
    ]

    report = mon.stop()

    assert waited == [2.0]
    assert [entry.extension_id for entry in report.activated] == [
        "esbenp.prettier-vscode"
    ]
    assert report.activated[0].source == "output"
    assert report.target_extension_observed is True
    assert "target_extension_not_observed" not in report.automation_health["reasons"]
    assert "target_activation_missing" not in report.automation_health["reasons"]
    assert report.run_quality != "inconclusive"


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
    mon.record_automation_event(
        "command",
        "Running command Analyze Workspace",
        "completed",
        activation_event="onCommand",
    )

    initial_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert initial_payload["network_events"][0]["host"] == "github.com"

    final_report = mon.stop()
    final_payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert final_report.network_events[0].host == "github.com"
    assert final_payload["network_summary"]["total_events"] == 1
    assert final_payload["summary"]["network_hosts"] == 1
    assert final_payload["log_streams"]["automation"][0]["kind"] == "command"
    assert (
        final_payload["log_streams"]["automation"][0]["message"]
        == "Running command Analyze Workspace"
    )


def test_extension_monitor_apply_trigger_payload_accepts_contract_models() -> None:
    payload = TriggerPayload(
        target_extension_id="ms-python.python",
        selected_scenarios=["project_exploration"],
        event_attempts=[
            {
                "attempt_id": "a1",
                "declared_event": "workspaceContains:app.py",
                "activation_event": "workspaceContains:app.py",
                "event_family": "workspaceContains",
                "event_value": "app.py",
                "executor_action": "scenario:project_exploration",
                "trigger_method": "ui_simulation",
            }
        ],
        stimulus_passes=[
            {
                "pass_id": "workspace_bootstrap",
                "label": "workspace/bootstrap pass",
                "order": 1,
                "attempt_ids": ["a1"],
                "prerequisite_keys": ["workspace_contains_fixture"],
            }
        ],
        prerequisite_results=[
            {
                "prerequisite_id": "prep-workspace",
                "key": "workspace_contains_fixture",
                "label": "workspace fixture",
                "attempt_ids": ["a1"],
            }
        ],
    )

    mon = monitor.ExtensionMonitor(object(), target_extension_id="")
    mon.apply_trigger_payload(payload)

    assert mon.report.trigger_plan_requested is True
    assert mon.report.trigger_plan_loaded is True
    assert mon.report.target_extension_id == "ms-python.python"
    assert mon.report.requested_scenarios == ["project_exploration"]
    assert [item.pass_id for item in mon.report.stimulus_passes] == [
        "workspace_bootstrap"
    ]
    assert [item.key for item in mon.report.prerequisite_results] == [
        "workspace_contains_fixture"
    ]
    assert [item.attempt_id for item in mon.report.event_attempts] == ["a1"]


def test_attach_runtime_tracers_records_failure_without_crashing(monkeypatch) -> None:
    class DummyPage:
        pass

    class FailingCapture:
        def __init__(self, monitoring_start: float, on_event=None) -> None:
            self.monitoring_start = monitoring_start
            self.on_event = on_event
            self.start_error = (
                "Extension Host PID not found; file attribution unavailable."
            )
            self.attach_attempts = 4
            self.diagnostics = {
                "attempts": 4,
                "selected_pid": None,
                "status": "failed",
            }
            self.pid = None

        def start(self) -> None:
            return None

    monkeypatch.setattr(monitor, "ExtensionHostFileCapture", FailingCapture)

    mon = monitor.ExtensionMonitor(DummyPage(), target_extension_id="publisher.tool")
    mon.report.monitoring_start = 0.0
    mon.attach_runtime_tracers()

    assert mon.report.file_capture_error
    assert mon.report.file_capture_diagnostics["attempts"] == 4
    assert any(
        entry.kind == "runtime_tracer_attach" and entry.status == "failed"
        for entry in mon.report.log_entries
    )


def test_extension_monitor_surfaces_runtime_network_capture_failure(
    monkeypatch,
) -> None:
    class DummyPage:
        pass

    monkeypatch.setattr(monitor, "_snapshot_log_offsets", lambda: {})
    monkeypatch.setattr(
        monitor, "parse_all_exthost_logs", lambda start_offsets=None: []
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
            [],
            capture_error="tshark capture exited unexpectedly: invalid field http.file_data",
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

    mon = monitor.ExtensionMonitor(DummyPage(), target_extension_id="sample.ext")

    mon.start()
    report = mon.stop()

    assert "invalid field http.file_data" in report.network_capture_error
    assert any(
        entry.stream == "automation"
        and entry.kind == "network_capture"
        and entry.status == "failed"
        for entry in report.log_entries
    )


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
        *,
        capture_error: str = "",
    ) -> None:
        self.monitoring_start = monitoring_start
        self.on_event = on_event
        self.events = events
        self.start_error = ""
        self.capture_error = capture_error

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
