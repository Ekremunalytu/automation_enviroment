from __future__ import annotations

import io
import json
from pathlib import Path

from executor.flows.playwright import monitor
from executor.flows.playwright.runtime_capture import network as network_capture
from packages.analysis_contracts import activation_report_invariant_issues


def test_activation_report_duration_prefers_monotonic_clock() -> None:
    report = monitor.ActivationReport(
        monitoring_start=100.0,
        monitoring_end=112.0,
        monitoring_started_monotonic=10.0,
        monitoring_ended_monotonic=18.5,
    )

    assert report.duration_s == 8.5


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
    assert payload["signal_summary"] == {}
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


def test_activation_report_save_uses_layered_attempt_coverage_to_avoid_synthetic_skips(
    tmp_path: Path,
) -> None:
    report = monitor.ActivationReport(
        target_extension_id="sample.ext",
        trigger_plan_requested=True,
        trigger_plan_loaded=True,
        trigger_plan_applied=True,
        trigger_execution_mode="layered_passes",
        requested_scenarios=[
            "project_exploration",
            "coding_session",
            "debug_session",
            "refactor_workflow",
        ],
        scenarios_run=["stale_scenario"],
        failed_scenarios=["stale_scenario"],
        scenario_traces=[
            monitor.ScenarioTrace(
                name="project_exploration",
                started_at=10.0,
                ended_at=20.0,
                status="completed",
            ),
            monitor.ScenarioTrace(
                name="coding_session",
                started_at=21.0,
                ended_at=32.0,
                status="failed",
            ),
        ],
        stimulus_passes=[
            monitor.StimulusPassTrace(
                pass_id="workspace_bootstrap",  # noqa: S106
                label="workspace/bootstrap pass",
                order=1,
                started_at=10.0,
                ended_at=12.0,
                status="completed",
                trigger_method="layered_deep",
            ),
            monitor.StimulusPassTrace(
                pass_id="ui_first_user_session",  # noqa: S106
                label="UI-first user session pass",
                order=2,
                started_at=12.5,
                ended_at=16.0,
                status="completed",
                trigger_method="layered_deep",
            ),
            monitor.StimulusPassTrace(
                pass_id="target_specific_activation",  # noqa: S106
                label="target-specific activation pass",
                order=3,
                started_at=16.5,
                ended_at=19.0,
                status="completed",
                trigger_method="layered_deep",
            ),
        ],
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="attempt-1",
                declared_event="workspaceContains:app.py",
                activation_event="workspaceContains:app.py",
                event_family="workspaceContains",
                track="official",
                attempted_passes=["workspace_bootstrap"],
                status="attempted_only",
            ),
            monitor.EventAttemptRecord(
                attempt_id="attempt-2",
                declared_event="onDebugInitialConfigurations",
                activation_event="onDebugInitialConfigurations",
                event_family="onDebugInitialConfigurations",
                executor_action="extra:debug_lifecycle",
                legacy_scenarios=["debug_session"],
                track="official",
                attempted_passes=["target_specific_activation"],
                status="attempted_only",
            ),
            monitor.EventAttemptRecord(
                attempt_id="attempt-3",
                declared_event="onCommand:test",
                activation_event="onCommand:test",
                event_family="onCommand",
                executor_action="command:auto",
                legacy_scenarios=["refactor_workflow"],
                track="official",
                attempted_passes=["ui_first_user_session"],
                status="attempted_only",
            ),
        ],
        official_event_coverage={
            "track": "official",
            "declared": 3,
            "verified": 0,
            "attempted_only": 3,
            "failed": 0,
            "blocked": 0,
            "unresolved": 3,
            "declared_events": [
                "workspaceContains:app.py",
                "onDebugInitialConfigurations",
                "onCommand:test",
            ],
        },
        monitoring_start=10.0,
        monitoring_end=40.0,
    )
    output_path = tmp_path / "aligned_report.json"

    report.save(output_path, announce=False)

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["summary"]["scenarios_run"] == [
        "project_exploration",
        "coding_session",
    ]
    assert payload["requested_scenarios"] == [
        "project_exploration",
        "coding_session",
        "debug_session",
        "refactor_workflow",
    ]
    assert payload["summary"]["failed_scenarios"] == ["coding_session"]
    assert payload["summary"]["skipped_scenarios"] == []
    assert payload["failed_scenarios"] == ["coding_session"]
    assert payload["skipped_scenarios"] == []
    assert activation_report_invariant_issues(payload) == []


def test_activation_report_save_supports_skip_automation_scenario_zero(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(monitor, "find_exthost_logs", lambda: [])

    report = monitor.ActivationReport(
        target_extension_id="extrace.fixture-theme",
        trigger_execution_mode="skip_automation",
        monitoring_start=0.0,
        monitoring_end=0.0,
    )
    output_path = tmp_path / "scenario_zero_report.json"

    report.save(output_path, announce=False)

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["trigger_execution_mode"] == "skip_automation"
    assert payload["summary"]["trigger_execution_mode"] == "skip_automation"
    assert payload["summary"]["scenarios_run"] == []
    assert payload["summary"]["failed_scenarios"] == []
    assert payload["scenario_traces"] == []
    assert payload["stimulus_passes"] == []
    assert payload["event_attempts"] == []
    assert payload["run_quality"] == "scenario_zero"
    assert payload["run_quality_reasons"] == [
        "No automation scenario was required for this non-executable fixture."
    ]
    assert payload["trigger_plan_requested"] is False
    assert payload["trigger_plan_loaded"] is False
    assert payload["trigger_plan_applied"] is False
    assert payload["summary"]["trigger_plan_applied"] is False
    assert payload["automation_health"]["status"] == "healthy"
    assert payload["automation_health"]["target_activation_count"] == 0
    assert activation_report_invariant_issues(payload) == []


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


def test_parse_tshark_event_line_extracts_text_http_body_preview() -> None:
    line = (
        "1700000000.250\t10.0.0.2\t\t93.184.216.34\t\t443\t\t\t"
        "api.example.com\t/api/health\t\tHTTP\tPOST /api/health HTTP/1.1\t"
        'POST\t200\tapplication/json\t{"status":"ok"}'
    )

    event = monitor.parse_tshark_event_line(line, monitoring_start=1700000000.0)

    assert event is not None
    assert event.request_body_preview == '{"status":"ok"}'
    assert event.request_body_sha256
    assert event.request_body_truncated is False


def test_parse_tshark_event_line_redacts_secrets_in_body_preview() -> None:
    line = (
        "1700000000.250\t10.0.0.2\t\t93.184.216.34\t\t443\t\t\t"
        "api.example.com\t/api/login\t\tHTTP\tPOST /api/login HTTP/1.1\t"
        "POST\t200\tapplication/json\t"
        '{"key":"AKIA1234567890ABCDEF","auth":"Bearer eyJabcdef.ghijklmn.opqrstu"}'
    )

    event = monitor.parse_tshark_event_line(line, monitoring_start=1700000000.0)

    assert event is not None
    assert "AKIA1234567890ABCDEF" not in event.request_body_preview
    assert "eyJabcdef.ghijklmn.opqrstu" not in event.request_body_preview
    assert "[REDACTED:aws]" in event.request_body_preview
    assert "[REDACTED:bearer]" in event.request_body_preview
    assert event.request_body_sha256


def test_network_capture_surfaces_immediate_tshark_field_failure(
    monkeypatch,
) -> None:
    class _ExitedTsharkProc:
        def __init__(self) -> None:
            self.stdout = io.StringIO("")
            self.stderr = io.StringIO(
                "tshark: Some fields aren't valid:\n\thttp.file_data\n"
            )
            self.returncode = 1

        def wait(self, timeout: float | None = None) -> int:
            _ = timeout
            return self.returncode

        def poll(self) -> int:
            return self.returncode

        def terminate(self) -> None:
            self.returncode = -15

        def kill(self) -> None:
            self.returncode = -9

    monkeypatch.setattr(
        network_capture.subprocess,
        "Popen",
        lambda *args, **kwargs: _ExitedTsharkProc(),
    )

    capture = network_capture.NetworkCapture(monitoring_start=0.0)
    capture.start()

    assert "http.file_data" in capture.capture_error
    assert capture.start_error == capture.capture_error


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


def test_parse_activations_from_output_filters_pre_start_entries() -> None:
    output = (
        "[2026-01-01 09:59:59.900] activating extension 'old.ext' because of "
        "'onStartupFinished'\n"
        "[2026-01-01 10:00:00.500] activating extension 'new.ext' because of "
        "'onStartupFinished'\n"
    )

    monitoring_start = monitor._parse_iso_timestamp("2026-01-01 10:00:00.000")
    assert monitoring_start is not None

    entries = monitor.parse_activations_from_output(
        output,
        monitoring_start=monitoring_start,
    )

    assert [entry.extension_id for entry in entries] == ["new.ext"]
    assert entries[0].source == "output"


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
    assert "--- exthost.log ---\n" in output
    assert "\\n" not in output


# W19-X — harness channel log files (``output_logging_*/*ExTrace Harness.log``)
# carry the ``[extrace-harness]`` stimulus markers because launch_vscode.sh
# discards Extension Host stdout (``</dev/null >/dev/null 2>&1 &``).
# ``read_extension_host_output`` must read them alongside ``exthost.log`` or
# the verifier sees no signed markers and onDebug* attempts stay unstamped.


def _write_harness_channel_log(
    base: Path, session: str, output_logging: str, body: str
) -> Path:
    log_dir = base / session / "window1" / "exthost" / output_logging
    log_dir.mkdir(parents=True)
    log_path = log_dir / "1-ExTrace Harness.log"
    log_path.write_text(body, encoding="utf-8")
    return log_path


def test_read_extension_host_output_reads_harness_channel_logs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_harness_channel_log(
        tmp_path,
        "session-1",
        "output_logging_t1",
        '[extrace-harness] {"kind":"stimulus","phase":"start","family":"onDebug"}\n',
    )

    monkeypatch.setattr(monitor.sources, "resolve_monitor_api", lambda: monitor)
    monkeypatch.setattr(monitor, "find_exthost_logs", lambda: [])
    monkeypatch.setattr(monitor, "VSCODE_LOGS_DIR", tmp_path)

    output = monitor.read_extension_host_output()

    assert "[extrace-harness]" in output
    assert "onDebug" in output


def test_read_extension_host_output_combines_exthost_and_harness_channel_logs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    exthost_log = tmp_path / "session-2" / "window1" / "exthost" / "exthost.log"
    exthost_log.parent.mkdir(parents=True)
    exthost_log.write_text("activating extension 'ms-python.python'\n")

    _write_harness_channel_log(
        tmp_path,
        "session-2",
        "output_logging_t1",
        '[extrace-harness] {"kind":"stimulus","phase":"complete"}\n',
    )

    monkeypatch.setattr(monitor.sources, "resolve_monitor_api", lambda: monitor)
    monkeypatch.setattr(monitor, "find_exthost_logs", lambda: [exthost_log])
    monkeypatch.setattr(monitor, "VSCODE_LOGS_DIR", tmp_path)

    output = monitor.read_extension_host_output()

    assert "ms-python.python" in output
    assert "[extrace-harness]" in output


def test_read_extension_host_output_reads_all_harness_channel_logs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Each VS Code reactivation creates its own ``output_logging_*`` directory
    with a fresh harness channel log; the W19-X live case had three. All must
    be read or the verifier misses the stimulus markers from a later
    reactivation."""
    _write_harness_channel_log(
        tmp_path,
        "session-3",
        "output_logging_t1",
        '[extrace-harness] {"phase":"start","family":"onDebugInitialConfigurations"}\n',
    )
    _write_harness_channel_log(
        tmp_path,
        "session-3",
        "output_logging_t2",
        '[extrace-harness] {"phase":"start","family":"onDebugResolve"}\n',
    )

    monkeypatch.setattr(monitor.sources, "resolve_monitor_api", lambda: monitor)
    monkeypatch.setattr(monitor, "find_exthost_logs", lambda: [])
    monkeypatch.setattr(monitor, "VSCODE_LOGS_DIR", tmp_path)

    output = monitor.read_extension_host_output()

    assert "onDebugInitialConfigurations" in output
    assert "onDebugResolve" in output


def test_activation_report_print_summary_uses_real_newlines(capsys) -> None:
    report = monitor.ActivationReport(
        activated=[monitor.ActivationEntry(extension_id="sample.ext", source="log")],
    )

    report.print_summary()

    output = capsys.readouterr().out
    assert output.startswith("\n" + "=" * 60)
    assert "\\n  Activated extensions:" not in output


def test_extract_user_data_dir_matches_equals_and_space_forms() -> None:
    assert (
        monitor._extract_user_data_dir("--user-data-dir=/workspace/profile")
        == "/workspace/profile"
    )
    assert (
        monitor._extract_user_data_dir("--foo --user-data-dir /workspace/profile --bar")
        == "/workspace/profile"
    )


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


def test_select_extension_host_pid_prefers_matching_profile_when_multiple_instances() -> (
    None
):
    entries = monitor._parse_process_table(
        "100 1 /usr/share/code/code --user-data-dir=/tmp/profile-a\n"
        "110 100 /usr/share/code/code --type=utility --utility-sub-type=node.mojom.NodeService --user-data-dir=/tmp/profile-a --inspect-port=0\n"
        "120 100 helper --clientProcessId=110\n"
        "200 1 /usr/share/code/code --user-data-dir=/tmp/profile-b\n"
        "210 200 /usr/share/code/code --type=utility --utility-sub-type=node.mojom.NodeService --user-data-dir=/tmp/profile-b --inspect-port=0\n"
        "220 200 helper --clientProcessId=210\n"
    )

    assert monitor._select_extension_host_pid(entries) == 110


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


def test_parse_activation_function_entry_marker(tmp_path: Path) -> None:
    log_file = tmp_path / "exthost.log"
    log_file.write_text(
        "[2026-04-26 09:00:01.123] activate(sample.publisher) entered\n"
    )

    entries = monitor.parse_activations_from_log(log_file)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.extension_id == "sample.publisher"
    assert entry.marker_type == "activate_fn_entry"
    assert entry.duration_ms is None


def test_parse_activation_function_exit_marker_with_duration(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "exthost.log"
    log_file.write_text(
        "[2026-04-26 09:00:02.500] activate completed sample.publisher in 42ms\n"
    )

    entries = monitor.parse_activations_from_log(log_file)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.extension_id == "sample.publisher"
    assert entry.marker_type == "activate_fn_exit"
    assert entry.duration_ms == 42


def test_parse_command_register_marker_attaches_to_target_id(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "exthost.log"
    log_file.write_text(
        "[2026-04-26 09:00:03.001] registered command 'extrace.example.run' "
        "for sample.publisher\n"
    )

    entries = monitor.parse_activations_from_log(log_file)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.extension_id == "sample.publisher"
    assert entry.activation_event == "extrace.example.run"
    assert entry.marker_type == "command_register"


def test_parse_provider_register_marker(tmp_path: Path) -> None:
    log_file = tmp_path / "exthost.log"
    log_file.write_text(
        "[2026-04-26 09:00:04.002] registered HoverProvider for sample.publisher\n"
    )

    entries = monitor.parse_activations_from_log(log_file)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.extension_id == "sample.publisher"
    assert entry.activation_event == "HoverProvider"
    assert entry.marker_type == "provider_register"


def test_marker_type_in_dedup_key_keeps_entry_and_exit(tmp_path: Path) -> None:
    log_file = tmp_path / "exthost.log"
    log_file.write_text(
        "[2026-04-26 09:00:05.001] activate(sample.publisher) entered\n"
        "[2026-04-26 09:00:05.001] activate completed sample.publisher\n"
    )

    entries = monitor.parse_activations_from_log(log_file)

    marker_types = [entry.marker_type for entry in entries]
    assert marker_types == ["activate_fn_entry", "activate_fn_exit"]
    assert all(entry.extension_id == "sample.publisher" for entry in entries)
