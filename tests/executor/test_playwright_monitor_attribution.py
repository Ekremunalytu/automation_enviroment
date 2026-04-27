from __future__ import annotations

import json
import sys
from pathlib import Path

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import monitor  # noqa: E402


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
    assert "could not be confirmed" in attempts[0].result_details


def test_reconcile_event_attempts_keeps_chat_tool_attempt_attempted_only_without_target_reaction() -> (
    None
):
    report = monitor.ActivationReport(
        target_extension_id="publisher.tool",
        extension_host_output=(
            '[extrace-harness] {"kind":"stimulus","phase":"complete",'
            '"attempt_id":"harness","family":"onLanguageModelTool",'
            '"activation_event":"onLanguageModelTool:test"}\n'
        ),
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="harness",
                declared_event="onLanguageModelTool:test",
                activation_event="onLanguageModelTool:test",
                event_family="onLanguageModelTool",
                executor_action="harness:run_current_stimulus",
                attempted_passes=["target_specific_activation"],
                capability_tags=["chat"],
                verification_contract=["activation_log_prefix", "automation_trace"],
            )
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    assert attempts[0].status == "attempted_only"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"
    assert "target verification remained unresolved" in attempts[0].result_details


def test_reconcile_event_attempts_verifies_chat_tool_with_marker_and_activation() -> (
    None
):
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onLanguageModelTool:test",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        extension_host_output=(
            '[extrace-harness] {"kind":"stimulus","phase":"start",'
            '"attempt_id":"harness","family":"onLanguageModelTool",'
            '"activation_event":"onLanguageModelTool:test"}\n'
            '[extrace-harness] {"kind":"stimulus","phase":"complete",'
            '"attempt_id":"harness","family":"onLanguageModelTool",'
            '"activation_event":"onLanguageModelTool:test"}\n'
        ),
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="harness",
                declared_event="onLanguageModelTool:test",
                activation_event="onLanguageModelTool:test",
                event_family="onLanguageModelTool",
                executor_action="harness:run_current_stimulus",
                attempted_passes=["target_specific_activation"],
                capability_tags=["chat"],
                verification_contract=["activation_log_prefix", "automation_trace"],
            )
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    assert attempts[0].status == "verified"
    assert "onLanguageModelTool:test" in attempts[0].evidence
    assert "harness_trace:harness" in attempts[0].evidence


def test_reconcile_event_attempts_upgrades_to_activation_seen_when_target_activates_without_runtime_evidence() -> (
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
                attempt_id="seen",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["chat"],
                verification_contract=["target_runtime_delta"],
            )
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    assert attempts[0].status == "activation_seen"
    assert attempts[0].verification_status == "activation_seen"
    assert "onCommand:run" in attempts[0].evidence
    assert "activation observed" in attempts[0].result_details


def test_reconcile_event_attempts_upgrades_to_target_log_seen_when_target_logs_present() -> (
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
        log_entries=[
            monitor.LogStreamEntry(
                timestamp="2026-01-01 10:00:00.100",
                stream="target_extension_host",
                kind="info",
                message="Tool registered successfully",
                extension_id="publisher.tool",
                is_target_extension=True,
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="log-seen",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["chat"],
                verification_contract=["target_runtime_delta"],
            )
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    assert attempts[0].status == "target_log_seen"
    assert attempts[0].verification_status == "target_log_seen"
    assert "onCommand:run" in attempts[0].evidence
    assert any("Tool registered successfully" in item for item in attempts[0].evidence)
    assert "log evidence observed" in attempts[0].result_details


def test_reconcile_event_attempts_activation_log_entry_alone_keeps_activation_seen() -> (
    None
):
    """PR345 followup: an ActivationEntry mirrored into target_extension_host
    must NOT count as separate target log evidence.

    Without the kind=='activation' guard in _target_log_stream_summaries,
    every target activation would auto-upgrade to ``target_log_seen`` because
    ``_append_activation_log_entries`` writes the activation into the stream
    with kind="activation" + is_target_extension=True. Lifecycle expects an
    additional, post-activation log/output event before the upgrade.
    """
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:run",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        log_entries=[
            # Mirrors what _append_activation_log_entries produces — kind="activation".
            monitor.LogStreamEntry(
                timestamp="2026-01-01 10:00:00.000",
                stream="target_extension_host",
                kind="activation",
                message="Activation publisher.tool via onCommand:run",
                extension_id="publisher.tool",
                activation_event="onCommand:run",
                is_target_extension=True,
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="seen",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["chat"],
                verification_contract=["target_runtime_delta"],
            )
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    assert attempts[0].status == "activation_seen"
    assert attempts[0].verification_status == "activation_seen"


def test_reconcile_event_attempts_target_output_signal_upgrades_to_target_log_seen() -> (
    None
):
    """PR345 followup: a target-attributed OutputSignalEvent counts as
    post-activation evidence and upgrades the attempt to ``target_log_seen``.

    Per ADR 0006 §5 the output-channel signal is exactly the kind of
    "target emitted something after activation" milestone target_log_seen
    was meant to capture.
    """
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:run",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        output_signal_events=[
            monitor.OutputSignalEvent(
                timestamp="2026-01-01T10:00:00.250",
                rel_time_s=0.25,
                channel="Tool Output",
                text="Boot complete",
                extension_id="publisher.tool",
                activation_event="onCommand:run",
                is_target_extension_event=True,
                attribution_status="near_target_activation",
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="output-seen",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["chat"],
                verification_contract=["target_runtime_delta"],
            )
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    assert attempts[0].status == "target_log_seen"
    assert attempts[0].verification_status == "target_log_seen"
    assert any("output_channel(Tool Output)" in item for item in attempts[0].evidence)


def test_reconcile_event_attempts_keeps_attempted_only_when_no_activation_match() -> (
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
        log_entries=[
            monitor.LogStreamEntry(
                timestamp="2026-01-01 10:00:00.100",
                stream="target_extension_host",
                kind="info",
                message="Unrelated activity",
                extension_id="publisher.tool",
                is_target_extension=True,
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="no-match",
                declared_event="onLanguage:python",
                activation_event="onLanguage:python",
                event_family="onLanguage",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["languages_editor"],
            )
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    assert attempts[0].status == "attempted_only"
    assert attempts[0].verification_status == "attempted_only"


def test_reconcile_event_attempts_harness_attempt_keeps_unconfirmed_signal_over_activation_seen() -> (
    None
):
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onLanguageModelTool:test",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="harness-no-trace",
                declared_event="onLanguageModelTool:test",
                activation_event="onLanguageModelTool:test",
                event_family="onLanguageModelTool",
                executor_action="harness:run_current_stimulus",
                attempted_passes=["target_specific_activation"],
                capability_tags=["chat"],
                verification_contract=["activation_log_prefix", "automation_trace"],
            )
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    assert attempts[0].status == "attempted_only"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"


def test_reconcile_event_attempts_target_log_seen_requires_target_attributed_entry() -> (
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
        log_entries=[
            monitor.LogStreamEntry(
                timestamp="2026-01-01 10:00:00.100",
                stream="other_extension_host",
                kind="info",
                message="Background chatter",
                extension_id="publisher.other",
                is_target_extension=False,
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="no-target-log",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["chat"],
                verification_contract=["target_runtime_delta"],
            )
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    assert attempts[0].status == "activation_seen"


def test_reconcile_event_attempts_target_log_seen_skips_extension_id_mismatch() -> None:
    """``is_target_extension=True`` is not enough; the entry's ``extension_id``
    must also match ``target_extension_id`` when the latter is set. Guards
    against a stale/wrong attribution flag silently promoting a non-target log
    entry into target-owned evidence.
    """

    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:run",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        log_entries=[
            monitor.LogStreamEntry(
                timestamp="2026-01-01 10:00:00.100",
                stream="target_extension_host",
                kind="info",
                message="Stale flag — wrong extension id",
                extension_id="publisher.other",
                is_target_extension=True,
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="mismatch",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["chat"],
                verification_contract=["target_runtime_delta"],
            )
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    assert attempts[0].status == "activation_seen"
    assert not any("Stale flag" in item for item in attempts[0].evidence)


def test_reconcile_event_attempts_target_log_summaries_capped_at_five() -> None:
    """Defensive cap on log-summary noise: even if dozens of target-owned log
    entries exist, only the first five should be folded into evidence so the
    report stays readable.
    """

    log_entries = [
        monitor.LogStreamEntry(
            timestamp=f"2026-01-01 10:00:00.{idx:03d}",
            stream="target_extension_host",
            kind="info",
            message=f"target log line {idx}",
            extension_id="publisher.tool",
            is_target_extension=True,
        )
        for idx in range(8)
    ]

    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:run",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        log_entries=log_entries,
        target_extension_id="publisher.tool",
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="capped",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["chat"],
                verification_contract=["target_runtime_delta"],
            )
        ],
    )

    attempts = monitor.reconcile_event_attempts(report)

    target_log_evidence = [
        item for item in attempts[0].evidence if item.startswith("Target log entry:")
    ]
    assert len(target_log_evidence) == 5


def test_attempt_has_runtime_evidence_accepts_lifecycle_observation_states() -> None:
    """``activation_seen`` and ``target_log_seen`` are strictly stronger than
    ``attempted_only`` so they must count as runtime evidence in coverage
    rollups. Without this, a target that activated would be silently treated
    as if no stimulus had reached it.
    """

    import health_runtime_facts

    for status in ("activation_seen", "target_log_seen", "attempted_only", "verified"):
        attempt = monitor.EventAttemptRecord(
            attempt_id=f"runtime-{status}",
            declared_event="onCommand:run",
            activation_event="onCommand:run",
            event_family="onCommand",
            status=status,
        )
        assert health_runtime_facts.attempt_has_runtime_evidence(attempt), status

    for status in ("planned", "running", "blocked"):
        attempt = monitor.EventAttemptRecord(
            attempt_id=f"runtime-{status}",
            declared_event="onCommand:run",
            activation_event="onCommand:run",
            event_family="onCommand",
            status=status,
        )
        assert not health_runtime_facts.attempt_has_runtime_evidence(attempt), status


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

    signal_summary = monitor._build_signal_summary(report)

    assert signal_summary["level"] in {"needs_review", "suspicious"}
    assert signal_summary["level"] != "likely_malicious"
    assert signal_summary["reasons"]


def test_inconclusive_run_never_returns_benign() -> None:
    report = monitor.ActivationReport(
        activated=[],
        target_extension_id="publisher.tool",
        trigger_plan_requested=True,
        trigger_plan_applied=False,
    )

    signal_summary = monitor._build_signal_summary(report)

    assert report.run_quality == "inconclusive"
    assert signal_summary["level"] == "needs_review"
    assert "inconclusive" in signal_summary["note"].lower()


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
    assert monitor._build_signal_summary(report)["level"] != "benign"


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


def test_layered_harness_chat_tool_attempt_degrades_health_and_keeps_quality_medium(
    monkeypatch,
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "exthost.log"
    log_file.write_text("extension host activity\n", encoding="utf-8")

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
        log_file_path=str(log_file),
        trigger_plan_requested=True,
        trigger_plan_loaded=True,
        trigger_plan_applied=True,
        trigger_execution_mode="layered_passes",
        requested_scenarios=["coding_session"],
        scenario_traces=[
            monitor.ScenarioTrace(
                name="coding_session",
                started_at=1.0,
                ended_at=2.0,
                status="completed",
            )
        ],
        event_attempts=[
            monitor.EventAttemptRecord(
                attempt_id="chat",
                declared_event="onLanguageModelTool:test",
                activation_event="onLanguageModelTool:test",
                event_family="onLanguageModelTool",
                executor_action="harness:run_current_stimulus",
                attempted_passes=["target_specific_activation"],
                capability_tags=["chat"],
                status="attempted_only",
                official=True,
                verification_contract=["activation_log_prefix", "automation_trace"],
            )
        ],
        official_event_coverage={
            "track": "official",
            "declared": 1,
            "verified": 0,
            "attempted_only": 1,
            "failed": 0,
            "blocked": 0,
            "unresolved": 1,
            "declared_events": ["onLanguageModelTool:test"],
        },
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

    # FOLLOWUP codex-automation-3: partial-evidence signals (verification
    # gap, official unresolved) now demote automation_health.status to
    # "degraded" and surface their reason codes there. run_quality stays
    # "medium" because partial-evidence degradation is not a run failure.
    # ``chat_tool_verification_incomplete`` is still gated on
    # ``official_unresolved_chat_tool_attempts`` semantics — a single
    # ``attempted_only`` harness chat attempt does not qualify.
    assert health["status"] == "degraded"
    assert "verification_gap_present" in health["reasons"]
    assert "official_unresolved_present" in health["reasons"]
    assert "chat_tool_verification_incomplete" not in health["reasons"]
    assert report.run_quality == "medium"


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


def test_risk_signals_ignore_loopback_only_correlative_network_activity() -> None:
    report = monitor.ActivationReport(
        activated=[
            monitor.ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:test",
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
                related_activation_event="onCommand:test",
                attribution_status="near_target_activation",
                attribution_basis="correlative only",
                attribution_confidence=0.41,
                sensitive=True,
                summary="read: /workspace/.env",
            )
        ],
        network_events=[
            monitor.NetworkEvent(
                timestamp="2026-01-01T10:00:00.700",
                rel_time_s=0.7,
                protocol="http",
                event_type="http_request",
                source_ip="127.0.0.1",
                destination_ip="127.0.0.11",
                destination_port=6080,
                host="localhost:6080",
                related_activation_event="onCommand:test",
                attribution_status="near_target_activation",
                attribution_basis="correlative only",
                attribution_confidence=0.38,
                summary="GET /health",
            )
        ],
        target_extension_id="publisher.tool",
    )

    assert all(
        signal.category != "correlative_suspicious_activity"
        for signal in report.risk_signals
    )
