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
        target_extension_id="sample.ext",
        trigger_plan_requested=True,
        trigger_plan_applied=True,
        trigger_execution_mode="layered_passes",
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
    assert payload["report_version"] == 2
    assert payload["summary"]["total_activated"] == 1
    assert payload["summary"]["network_events"] == 1
    assert payload["activated"][0]["extension_id"] == "sample.ext"
    assert payload["network_events"][0]["host"] == "api.example.com"
    assert payload["target_extension_expected"] == "sample.ext"
    assert payload["target_extension_observed"] is True
    assert payload["run_quality"] == "inconclusive"
    assert payload["verdict"] == {}
    assert payload["automation_health"]["status"] == "inconclusive"
    assert "target_stream_missing" in payload["automation_health"]["reasons"]
    assert payload["log_health"]["extension_host_log_found"] is False
    assert payload["trigger_plan_requested"] is True
    assert payload["trigger_plan_loaded"] is False
    assert payload["trigger_plan_applied"] is True
    assert payload["trigger_execution_mode"] == "layered_passes"
    assert payload["summary"]["trigger_execution_mode"] == "layered_passes"
    assert payload["run_quality_reasons"]
    assert payload["evidence_events"][0]["event_id"].startswith("activation-")
    assert payload["evidence_events"][1]["event_id"].startswith("network-")
    assert payload["evidence_links"] == []
    assert payload["network_summary"]["unique_hosts"] == 1
    assert payload["attempted_capabilities"] == []
    assert payload["verified_capabilities"] == []
    assert not list(tmp_path.glob(".activation_report.json.*.tmp"))


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
    line = '1700000000.750 openat(AT_FDCWD, "/workspace/.env", O_RDONLY|O_CLOEXEC) = 42'

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


def test_annotate_file_events_preserves_duplicate_observers_and_emits_links() -> None:
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
            started_at=monitor._parse_iso_timestamp("2026-01-01T10:00:00.000") or 0.0,
            ended_at=monitor._parse_iso_timestamp("2026-01-01T10:00:02.000") or 0.0,
            status="completed",
        )
    ]

    annotated = monitor._annotate_file_events(
        file_events,
        activations,
        traces,
        "ms-python.python",
    )

    assert len(annotated) == 3
    assert annotated[0].source == "automation"
    assert annotated[0].attribution_status == "corroboration"
    assert annotated[1].source == "extension"
    assert annotated[1].attribution_status == "target_attributed"
    assert annotated[2].source == "automation"
    assert annotated[2].scenario_name == "coding_session"
    assert annotated[2].attribution_status == "automation_noise"

    report = monitor.ActivationReport(
        activated=activations,
        file_events=annotated,
        scenario_traces=traces,
        target_extension_id="ms-python.python",
        monitoring_start=monitor._parse_iso_timestamp("2026-01-01T10:00:00.000") or 0.0,
        monitoring_end=monitor._parse_iso_timestamp("2026-01-01T10:00:02.000") or 0.0,
    )
    links = report.canonical_evidence_links

    assert any(
        link.link_type == "duplicate_signal"
        and {link.from_event_id, link.to_event_id} == {"file-0001", "file-0002"}
        for link in links
    )
    assert any(
        link.link_type == "occurred_in_scenario"
        and link.from_event_id == "file-0003"
        and link.to_event_id == "scenario-0001"
        for link in links
    )
    assert any(link.link_type == "caused_by_target_extension" for link in links)
    assert any(link.link_type == "automation_noise" for link in links)


def test_canonical_evidence_links_mark_temporal_neighbors_low_confidence() -> None:
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="ms-python.python",
                activation_event="onLanguage:python",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        network_events=[
            monitor.NetworkEvent(
                timestamp="2026-01-01T10:00:04.500",
                rel_time_s=4.5,
                protocol="https",
                event_type="http_request",
                destination_ip="93.184.216.34",
                destination_port=443,
                host="api.example.com",
                related_extension_id="ms-python.python",
                related_activation_event="onLanguage:python",
                attribution_status="near_target_activation",
                attribution_basis="network event was only temporally close to the target activation",
                attribution_confidence=0.31,
                summary="GET /telemetry",
            )
        ],
        target_extension_id="ms-python.python",
        monitoring_start=1767261600.0,
        monitoring_end=1767261605.0,
    )

    links = report.canonical_evidence_links

    temporal_link = next(
        link for link in links if link.link_type == "near_target_activation"
    )
    assert temporal_link.from_event_id == "network-0001"
    assert temporal_link.to_event_id == "activation-0001"
    assert temporal_link.confidence < 0.5


def test_inotify_events_never_claim_target_ownership() -> None:
    activations = [
        monitor.ActivationEntry(
            extension_id="publisher.tool",
            activation_event="onCommand:run",
            timestamp="2026-01-01 10:00:00.400",
            source="log",
        )
    ]
    traces = [
        monitor.ScenarioTrace(
            name="coding_session",
            started_at=monitor._parse_iso_timestamp("2026-01-01T10:00:00.000") or 0.0,
            ended_at=monitor._parse_iso_timestamp("2026-01-01T10:00:02.000") or 0.0,
            status="completed",
        )
    ]
    file_events = [
        monitor.FileEvent(
            timestamp="2026-01-01T10:00:00.500",
            rel_time_s=0.5,
            operation="read",
            path="/workspace/package.json",
            source="automation",
            observer="inotify",
            summary="read: /workspace/package.json",
        )
    ]

    annotated = monitor._annotate_file_events(
        file_events,
        activations,
        traces,
        "publisher.tool",
    )

    assert annotated[0].attribution_status == "automation_noise"
    assert annotated[0].is_target_extension_event is False
    assert annotated[0].noise_reason
    assert annotated[0].artifact_class == "workspace_runtime"


def test_strace_event_with_competing_activation_is_not_owned_by_target() -> None:
    activations = [
        monitor.ActivationEntry(
            extension_id="publisher.tool",
            activation_event="onStartupFinished",
            timestamp="2026-01-01 10:00:00.500",
            source="log",
        ),
        monitor.ActivationEntry(
            extension_id="other.extension",
            activation_event="onCommand:other",
            timestamp="2026-01-01 10:00:00.600",
            source="log",
        ),
    ]
    traces: list[monitor.ScenarioTrace] = []
    file_events = [
        monitor.FileEvent(
            timestamp="2026-01-01T10:00:00.650",
            rel_time_s=0.65,
            operation="read",
            path="/home/executor/.ssh/config",
            source="extension",
            observer="strace",
            summary="read: /home/executor/.ssh/config",
            sensitive=True,
        )
    ]

    annotated = monitor._annotate_file_events(
        file_events,
        activations,
        traces,
        "publisher.tool",
    )

    assert annotated[0].attribution_status == "competing_candidate"
    assert annotated[0].is_target_extension_event is False
    assert "competing" in annotated[0].noise_reason


def test_network_events_without_target_activation_stay_unattributed() -> None:
    network_events = [
        monitor.NetworkEvent(
            timestamp="2026-01-01T10:00:03.000",
            rel_time_s=3.0,
            protocol="https",
            event_type="http_request",
            destination_ip="93.184.216.34",
            destination_port=443,
            host="api.example.com",
            summary="GET /collect",
        )
    ]
    activations = [
        monitor.ActivationEntry(
            extension_id="other.extension",
            activation_event="onCommand:other",
            timestamp="2026-01-01 10:00:00.000",
            source="log",
        )
    ]

    annotated = monitor._annotate_network_events(
        network_events,
        activations,
        [],
        "publisher.tool",
    )

    assert annotated[0].attribution_status == "unattributed"
    assert annotated[0].is_target_extension_event is False
    assert annotated[0].related_extension_id == ""


def test_reconcile_coverage_marks_attempted_only_when_not_verified() -> None:
    report = monitor.ActivationReport(
        coverage_tracks={
            "official": {
                "summary": {"covered": 2, "partial": 0, "missing": 1},
                "matrix": [
                    {"capability": "commands", "status": "covered"},
                    {"capability": "workspace_fs", "status": "covered"},
                    {"capability": "chat", "status": "missing"},
                ],
            },
            "heuristic": {
                "summary": {"covered": 1, "partial": 0, "missing": 0},
                "matrix": [{"capability": "search_views", "status": "covered"}],
            },
        },
        coverage_summary={"covered": 2, "partial": 0, "missing": 1},
        coverage_matrix=[
            {"capability": "commands", "status": "covered"},
            {"capability": "workspace_fs", "status": "covered"},
            {"capability": "chat", "status": "missing"},
        ],
        attempted_capabilities=["commands", "workspace_fs"],
        verified_capabilities=["workspace_fs"],
        heuristic_attempted_capabilities=["search_views"],
    )

    summary, matrix, coverage_tracks = monitor._reconcile_coverage_verification(report)

    assert summary["attempted"] == 2
    assert summary["verified"] == 1
    commands_entry = next(item for item in matrix if item["capability"] == "commands")
    workspace_entry = next(
        item for item in matrix if item["capability"] == "workspace_fs"
    )
    assert commands_entry["verification_status"] == "attempted_only"
    assert workspace_entry["verification_status"] == "verified"
    assert coverage_tracks["heuristic"]["summary"]["attempted"] == 1


def test_verification_gap_ignores_unsupported_capabilities() -> None:
    report = monitor.ActivationReport(
        coverage_tracks={
            "official": {
                "summary": {"covered": 1, "partial": 0, "missing": 1},
                "matrix": [
                    {
                        "capability": "commands",
                        "status": "covered",
                        "support_status": "covered",
                    },
                    {
                        "capability": "chat",
                        "status": "missing",
                        "support_status": "missing",
                    },
                ],
            }
        },
        coverage_matrix=[
            {
                "capability": "commands",
                "status": "covered",
                "support_status": "covered",
            },
            {"capability": "chat", "status": "missing", "support_status": "missing"},
        ],
        attempted_capabilities=["commands", "chat"],
        verified_capabilities=[],
    )

    assert report.official_attempted_capabilities == ["commands"]
    assert report.verification_gap == 1


def test_runtime_attempted_capabilities_ignore_static_payload_bloat() -> None:
    report = monitor.ActivationReport(
        coverage_tracks={
            "official": {
                "summary": {"covered": 3, "partial": 0, "missing": 0},
                "matrix": [
                    {
                        "capability": "commands",
                        "status": "covered",
                        "support_status": "covered",
                    },
                    {
                        "capability": "languages_editor",
                        "status": "covered",
                        "support_status": "covered",
                    },
                    {
                        "capability": "debug",
                        "status": "covered",
                        "support_status": "covered",
                    },
                ],
            }
        },
        coverage_matrix=[
            {
                "capability": "commands",
                "status": "covered",
                "support_status": "covered",
            },
            {
                "capability": "languages_editor",
                "status": "covered",
                "support_status": "covered",
            },
            {"capability": "debug", "status": "covered", "support_status": "covered"},
        ],
        attempted_capabilities=["commands", "languages_editor", "debug"],
        verified_capabilities=["commands"],
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="cmd",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                track="official",
                capability_tags=["commands"],
                attempted_passes=["ui_first_user_session"],
                status="attempted_only",
            ),
            monitor.EventAttemptRecord(
                attempt_id="blocked",
                declared_event="onDebugResolve:python",
                activation_event="onDebugResolve:python",
                event_family="onDebugResolve",
                track="official",
                capability_tags=["debug"],
                status="blocked",
            ),
        ],
    )

    assert report.official_attempted_capabilities == [
        "commands",
        "debug",
        "languages_editor",
    ]
    assert report.runtime_official_attempted_capabilities == ["commands"]
    assert report.official_verified_capabilities == []
    assert report.verification_gap == 1


def test_runtime_verified_capabilities_drive_quality_gap() -> None:
    report = monitor.ActivationReport(
        coverage_tracks={
            "official": {
                "summary": {"covered": 3, "partial": 0, "missing": 0},
                "matrix": [
                    {
                        "capability": "commands",
                        "status": "covered",
                        "support_status": "covered",
                    },
                    {
                        "capability": "languages_editor",
                        "status": "covered",
                        "support_status": "covered",
                    },
                    {
                        "capability": "debug",
                        "status": "covered",
                        "support_status": "covered",
                    },
                ],
            }
        },
        coverage_matrix=[
            {
                "capability": "commands",
                "status": "covered",
                "support_status": "covered",
            },
            {
                "capability": "languages_editor",
                "status": "covered",
                "support_status": "covered",
            },
            {"capability": "debug", "status": "covered", "support_status": "covered"},
        ],
        attempted_capabilities=["commands", "languages_editor", "debug"],
        verified_capabilities=["window_ui"],
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="cmd",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                track="official",
                capability_tags=["commands"],
                attempted_passes=["ui_first_user_session"],
                status="verified",
            ),
            monitor.EventAttemptRecord(
                attempt_id="lang",
                declared_event="workspaceContains:app.py",
                activation_event="workspaceContains:app.py",
                event_family="workspaceContains",
                track="official",
                capability_tags=["languages_editor"],
                attempted_passes=["workspace_bootstrap"],
                status="verified",
            ),
            monitor.EventAttemptRecord(
                attempt_id="debug",
                declared_event="onDebugResolve:python",
                activation_event="onDebugResolve:python",
                event_family="onDebugResolve",
                track="official",
                capability_tags=["debug"],
                attempted_passes=["target_specific_activation"],
                status="attempted_only",
            ),
        ],
    )

    assert report.runtime_official_attempted_capabilities == [
        "commands",
        "debug",
        "languages_editor",
    ]
    assert report.official_verified_capabilities == ["commands", "languages_editor"]
    assert report.verification_gap == 1

    quality, _ = monitor.build_run_quality(
        report,
        automation_health={
            "status": "degraded",
            "reasons": ["verification_gap_present"],
        },
    )

    assert quality == "medium"


def test_reconcile_event_attempts_respects_attempted_blocked_and_verified_states() -> (
    None
):
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:run",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="attempted",
                declared_event="onLanguage:python",
                activation_event="onLanguage:python",
                event_family="onLanguage",
                capability_tags=["languages_editor"],
                attempted_passes=["ui_first_user_session"],
            ),
            monitor.EventAttemptRecord(
                attempt_id="blocked",
                declared_event="onUri",
                activation_event="onUri",
                event_family="onUri",
                blocked_reason_code="missing_uri_target",
            ),
            monitor.EventAttemptRecord(
                attempt_id="verified",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["commands"],
            ),
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    assert attempts[0].status == "attempted_only"
    assert attempts[0].verification_status == "attempted_only"
    assert attempts[1].status == "blocked"
    assert attempts[1].verification_status == "blocked"
    assert attempts[2].status == "verified"
    assert attempts[2].verification_status == "verified"


def test_reconcile_event_attempts_marks_unverified_harness_attempts() -> None:
    report = monitor.ActivationReport(
        target_extension_id="publisher.tool",
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="harness",
                declared_event="onLanguageModelTool:test",
                activation_event="onLanguageModelTool:test",
                event_family="onLanguageModelTool",
                executor_action="harness:run_current_stimulus",
                attempted_passes=["target_specific_activation"],
                capability_tags=["chat"],
            )
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    assert attempts[0].status == "attempted_only"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"
    assert "Harness stimulus executed" in attempts[0].result_details


def test_verdict_stays_bounded_when_only_correlative_sensitive_activity_exists() -> (
    None
):
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onStartupFinished",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        file_events=[
            monitor.FileEvent(
                timestamp="2026-01-01T10:00:00.900",
                rel_time_s=0.9,
                operation="read",
                path="/workspace/.env",
                observer="strace",
                scenario_name="project_exploration",
                attribution_status="near_target_activation",
                attribution_basis="correlative only",
                attribution_confidence=0.41,
                sensitive=True,
                summary="read: /workspace/.env",
            )
        ],
        target_extension_id="publisher.tool",
    )

    verdict = monitor._build_verdict(report)

    assert verdict["level"] in {"needs_review", "suspicious"}
    assert verdict["level"] != "likely_malicious"
    assert verdict["reasons"]


def test_inconclusive_run_never_returns_benign() -> None:
    report = monitor.ActivationReport(
        activated=[],
        target_extension_id="publisher.tool",
        trigger_plan_requested=True,
        trigger_plan_applied=False,
    )

    verdict = monitor._build_verdict(report)

    assert report.run_quality == "inconclusive"
    assert verdict["level"] == "needs_review"
    assert "inconclusive" in verdict["note"].lower()


def test_trigger_requested_but_not_loaded_is_inconclusive() -> None:
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:test",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        extension_host_output="extension output",
        log_file_path="/workspace/exthost.log",
        target_extension_id="publisher.tool",
        trigger_plan_requested=True,
        trigger_plan_loaded=False,
        trigger_plan_applied=False,
    )
    report.log_entries.append(
        monitor.LogStreamEntry(
            timestamp="2026-01-01T10:00:00.000",
            stream="target_extension_host",
            kind="activation",
            extension_id="publisher.tool",
            message="Activated publisher.tool via onCommand:test",
            status="completed",
            is_target_extension=True,
        )
    )

    health = report.automation_health

    assert health["status"] == "inconclusive"
    assert "trigger_plan_not_loaded" in health["reasons"]
    assert "trigger_plan_not_applied" in health["reasons"]
    assert monitor._build_verdict(report)["level"] != "benign"


def test_target_running_alone_does_not_verify_window_ui() -> None:
    report = monitor.ActivationReport(
        running_extensions=[
            monitor.RunningExtension(
                extension_id="publisher.tool", activation_time_ms=5
            )
        ],
        target_extension_id="publisher.tool",
    )

    assert monitor._derive_verified_capabilities(report) == []


def test_verify_target_reaction_requires_strong_target_activity(monkeypatch) -> None:
    class DummyPage:
        pass

    mon = monitor.ExtensionMonitor(DummyPage(), target_extension_id="publisher.tool")
    mon.report.monitoring_start = 0.0
    mon.report.file_events.append(
        monitor.FileEvent(
            path="/workspace/package.json",
            operation="read",
            source="extension",
            observer="strace",
            attribution_status="near_target_activation",
            is_target_extension_event=False,
            summary="correlative read",
        )
    )
    mon.report.attempted_capabilities = ["commands"]

    monkeypatch.setattr(
        monitor, "parse_all_exthost_logs", lambda start_offsets=None: []
    )

    verified = mon.verify_target_reaction(
        {
            "target_activations": 0,
            "target_file_events": 0,
            "target_network_events": 0,
            "ui_blockers": 0,
        },
        capability="commands",
        trigger_label="Run Analysis",
        activation_event="onCommand",
    )

    assert verified is False
    assert mon.report.verified_capabilities == []


def test_heuristic_verification_gap_is_separate_from_official_gap() -> None:
    report = monitor.ActivationReport(
        attempted_capabilities=["commands"],
        verified_capabilities=[],
        heuristic_attempted_capabilities=["search_views", "settings"],
        heuristic_verified_capabilities=["search_views"],
    )

    assert report.verification_gap == 1
    assert report.heuristic_verification_gap == 1


def test_empty_extension_host_output_degrades_run_health() -> None:
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:test",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        log_file_path="/workspace/exthost.log",
    )
    report.log_entries.append(
        monitor.LogStreamEntry(
            timestamp="2026-01-01T10:00:00.000",
            stream="target_extension_host",
            kind="activation",
            extension_id="publisher.tool",
            message="Activated publisher.tool via onCommand:test",
            status="completed",
            is_target_extension=True,
        )
    )

    health = report.automation_health

    assert health["status"] == "degraded"
    assert "extension_host_output_missing" in health["reasons"]


def test_failed_scenarios_degrade_run_health() -> None:
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:test",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        extension_host_output="extension output",
        log_file_path="/workspace/exthost.log",
        failed_scenarios=["coding_session"],
    )
    report.log_entries.append(
        monitor.LogStreamEntry(
            timestamp="2026-01-01T10:00:00.000",
            stream="target_extension_host",
            kind="activation",
            extension_id="publisher.tool",
            message="Activated publisher.tool via onCommand:test",
            status="completed",
            is_target_extension=True,
        )
    )

    health = report.automation_health

    assert health["status"] == "degraded"
    assert health["failed_scenarios"] == ["coding_session"]
    assert "scenario_failures_present" in health["reasons"]


def test_extra_trigger_failures_degrade_and_serialize_health(
    monkeypatch,
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "exthost.log"
    log_file.write_text("extension host output")
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:test",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        extension_host_output="extension output",
        log_offsets_snapshot={str(log_file.resolve()): 0},
        failed_scenarios=["coding_session"],
        extra_trigger_failures=["uri_trigger", "command:Extension: Fail"],
    )
    report.log_entries.append(
        monitor.LogStreamEntry(
            timestamp="2026-01-01T10:00:00.000",
            stream="target_extension_host",
            kind="activation",
            extension_id="publisher.tool",
            message="Activated publisher.tool via onCommand:test",
            status="completed",
            is_target_extension=True,
        )
    )
    monkeypatch.setattr(monitor, "find_exthost_logs", lambda: [log_file])

    health = report.automation_health
    output_path = tmp_path / "activation_report.json"
    report.save(output_path, announce=False)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert health["status"] == "degraded"
    assert "scenario_failures_present" in health["reasons"]
    assert "extra_trigger_failures_present" in health["reasons"]
    assert health["failed_scenarios"] == ["coding_session"]
    assert health["extra_trigger_failures"] == [
        "command:Extension: Fail",
        "uri_trigger",
    ]
    assert health["extra_trigger_failure_count"] == 2
    assert payload["extra_trigger_failures"] == [
        "uri_trigger",
        "command:Extension: Fail",
    ]
    assert payload["automation_health"]["extra_trigger_failures"] == [
        "command:Extension: Fail",
        "uri_trigger",
    ]
    assert payload["automation_health"]["extra_trigger_failure_count"] == 2


def test_risk_signals_capture_sensitive_file_and_network_combo() -> None:
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onStartupFinished",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        file_events=[
            monitor.FileEvent(
                timestamp="2026-01-01T10:00:00.500",
                rel_time_s=0.5,
                operation="read",
                path="/workspace/.env",
                observer="strace",
                related_extension_id="publisher.tool",
                related_activation_event="onStartupFinished",
                attribution_status="target_attributed",
                attribution_basis="strong attribution",
                attribution_confidence=0.93,
                is_target_extension_event=True,
                sensitive=True,
                summary="read: /workspace/.env",
            )
        ],
        network_events=[
            monitor.NetworkEvent(
                timestamp="2026-01-01T10:00:00.700",
                rel_time_s=0.7,
                protocol="https",
                event_type="http_request",
                destination_ip="93.184.216.34",
                destination_port=443,
                host="api.example.com",
                related_extension_id="publisher.tool",
                related_activation_event="onStartupFinished",
                attribution_status="target_attributed",
                attribution_basis="strong attribution",
                attribution_confidence=0.89,
                is_target_extension_event=True,
                summary="GET /collect",
            )
        ],
        target_extension_id="publisher.tool",
    )

    signals = report.risk_signals
    summary = report.risk_summary

    assert any(
        signal.category == "sensitive_file_and_network_combo" for signal in signals
    )
    assert summary["total_signals"] >= 2


def test_select_extension_host_pid_prefers_legacy_extension_host() -> None:
    entries = monitor._parse_process_table(
        "101 1 /usr/share/code/code --user-data-dir=/tmp/profile\n"
        "202 101 /usr/share/code/code --type=utility extensionHost --user-data-dir=/tmp/profile\n"
        "203 101 /usr/share/code/code --type=utility --utility-sub-type=node.mojom.NodeService --user-data-dir=/tmp/profile\n"
    )

    assert monitor._select_extension_host_pid(entries) == 202


def test_select_extension_host_pid_uses_modern_node_service_candidates() -> None:
    entries = monitor._parse_process_table(
        "100 1 /usr/share/code/code --user-data-dir=/tmp/profile\n"
        "1184 100 /usr/share/code/code --type=utility --utility-sub-type=node.mojom.NodeService --user-data-dir=/tmp/profile --inspect-port=0\n"
        "1200 100 /usr/share/code/code --type=utility --utility-sub-type=node.mojom.NodeService --user-data-dir=/tmp/profile /extensions/ms-python/server.bundle.js --clientProcessId=1184\n"
        "1201 100 /usr/share/code/code --type=utility --utility-sub-type=node.mojom.NodeService --user-data-dir=/tmp/profile /extensions/json/jsonServerMain --clientProcessId=1184\n"
        "1300 1184 pylance --clientProcessId=1184\n"
    )

    assert monitor._select_extension_host_pid(entries) == 1184


def test_select_extension_host_pid_returns_none_for_only_excluded_candidates() -> None:
    entries = monitor._parse_process_table(
        "100 1 /usr/share/code/code --user-data-dir=/tmp/profile\n"
        "1200 100 /usr/share/code/code --type=utility --utility-sub-type=node.mojom.NodeService --user-data-dir=/tmp/profile /extensions/ms-python/server.bundle.js\n"
        "1201 100 /usr/share/code/code --type=utility --utility-sub-type=node.mojom.NodeService --user-data-dir=/tmp/profile /extensions/typescript/tsserver.js\n"
    )

    assert monitor._select_extension_host_pid(entries) is None


def test_wait_for_extension_host_pid_retries_until_candidate_appears(
    monkeypatch,
) -> None:
    seen = {"count": 0}

    def fake_find_pid() -> int | None:
        seen["count"] += 1
        return 1184 if seen["count"] >= 3 else None

    monkeypatch.setattr(monitor, "_find_extension_host_pid", fake_find_pid)
    monkeypatch.setattr(monitor.time, "sleep", lambda _: None)

    pid, diagnostics = monitor._wait_for_extension_host_pid(
        timeout_s=1.0, poll_interval_s=0.01
    )

    assert pid == 1184
    assert diagnostics["attempts"] == 3


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
