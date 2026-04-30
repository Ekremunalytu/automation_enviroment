from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from appcore.contracts.schemas import ExtensionSchema
from packages.analysis_contracts import (
    EVENT_ATTEMPT_LIFECYCLE_STATES,
    ActivationReport,
    EventAttemptRecord,
    TriggerPayload,
    activation_report_invariant_issues,
    detection_report_invariant_issues,
    scenario_trace_names,
)
from packages.analysis_engine.runner import run_detection
from workflows.extension_catalog.manifest_parser import (
    parse_activation_events,
    parse_contributes,
)
from workflows.extension_catalog.manifest_reader import get_package_json
from workflows.marketplace.client import download_and_extract_vsix


_EXTENSIONS_DIR = Path(__file__).parents[3] / "extensions"


def _fixture_identity(name: str, version: str) -> tuple[str, str, str]:
    return ("extrace", name, version)


BASELINE_EXTENSION_FIXTURES = [
    ("ms-python", "python", "2026.5.2026032701"),
    _fixture_identity("fixture-chat", "0.0.1"),
    _fixture_identity("fixture-theme", "0.0.1"),
]


def _load_fixture(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_activation_report_fixture_exposes_minimum_shape() -> None:
    fixture_path = (
        Path(__file__).parent
        / "fixtures"
        / "activation_reports"
        / "ms_python_python.json"
    )

    report = _load_fixture(fixture_path)

    required_keys = {
        "report_version",
        "target_extension_expected",
        "automation_health",
        "signal_summary",
        "summary",
        "scenario_traces",
        "evidence_events",
        "network_events",
        "file_events",
        "log_streams",
    }

    assert required_keys.issubset(report)
    assert report["target_extension_expected"] == "ms-python.python"
    assert isinstance(report["automation_health"], dict)
    assert isinstance(report["signal_summary"], dict)
    assert isinstance(report["summary"], dict)
    assert isinstance(report["scenario_traces"], list)
    assert isinstance(report["evidence_events"], list)
    assert isinstance(report["network_events"], list)
    assert isinstance(report["file_events"], list)
    assert isinstance(report["log_streams"], dict)
    assert "automation" in report["log_streams"]
    assert report["trigger_execution_mode"] == "layered_passes"
    assert isinstance(report["stimulus_passes"], list)
    assert report["stimulus_passes"]
    assert isinstance(report["event_attempts"], list)
    assert report["event_attempts"]
    assert isinstance(report["official_event_coverage"], dict)
    assert report["official_event_coverage"]
    assert report["automation_health"]["status"] == "healthy"
    assert report["automation_health"]["reasons"] == []
    assert report["summary"]["skipped_scenarios"] == []
    assert report["skipped_scenarios"] == []
    assert report["run_quality"] == "medium"
    assert report["requested_scenarios"] != report["summary"]["scenarios_run"]
    assert report["summary"]["scenarios_run"] == scenario_trace_names(report)
    assert activation_report_invariant_issues(report) == []
    assert isinstance(report["risk_signals"], list)
    assert "correlative_suspicious_activity" not in report["risk_summary"]["categories"]

    parsed = ActivationReport.model_validate(report)
    round_tripped = parsed.model_dump(mode="json")

    assert ActivationReport.model_validate(round_tripped) == parsed


def test_color_theme_activation_report_fixture_supports_zero_scenario_semantics() -> (
    None
):
    fixture_path = (
        Path(__file__).parent
        / "fixtures"
        / "activation_reports"
        / "extrace_fixture_theme.json"
    )

    report = _load_fixture(fixture_path)

    assert report["target_extension_expected"] == "extrace.fixture-theme"
    assert report["trigger_execution_mode"] == "skip_automation"
    assert report["summary"]["scenarios_run"] == []
    assert report["summary"]["failed_scenarios"] == []
    assert report["summary"]["trigger_plan_applied"] is False
    assert report["scenario_traces"] == []
    assert report["stimulus_passes"] == []
    assert report["event_attempts"] == []
    assert report["run_quality"] == "scenario_zero"
    assert report["run_quality_reasons"] == [
        "No automation scenario was required for this non-executable fixture."
    ]
    assert report["automation_health"]["target_activation_count"] == 0
    assert activation_report_invariant_issues(report) == []

    parsed = ActivationReport.model_validate(report)
    round_tripped = parsed.model_dump(mode="json")

    assert round_tripped["trigger_execution_mode"] == "skip_automation"
    assert round_tripped["summary"]["scenarios_run"] == []
    assert ActivationReport.model_validate(round_tripped) == parsed


def test_activation_report_accepts_legacy_verdict_field() -> None:
    fixture_path = (
        Path(__file__).parent
        / "fixtures"
        / "activation_reports"
        / "ms_python_python.json"
    )
    report = _load_fixture(fixture_path)

    legacy = deepcopy(report)
    legacy["verdict"] = legacy.pop("signal_summary")
    assert "signal_summary" not in legacy
    assert "verdict" in legacy

    parsed = ActivationReport.model_validate(legacy)
    dumped = parsed.model_dump(mode="json")

    assert "signal_summary" in dumped
    assert "verdict" not in dumped
    assert dumped["signal_summary"] == report["signal_summary"]

    reparsed = ActivationReport.model_validate(dumped)
    assert reparsed == parsed


def _minimal_event_attempt_payload(status: str) -> dict[str, object]:
    return {
        "attempt_id": "attempt-1",
        "declared_event": "onLanguage:python",
        "activation_event": "onLanguage:python",
        "event_family": "onLanguage",
        "status": status,
    }


@pytest.mark.parametrize("status", sorted(EVENT_ATTEMPT_LIFECYCLE_STATES))
def test_event_attempt_record_accepts_all_documented_lifecycle_states(
    status: str,
) -> None:
    record = EventAttemptRecord.model_validate(_minimal_event_attempt_payload(status))
    assert record.status == status


def test_event_attempt_record_rejects_unknown_status() -> None:
    with pytest.raises(ValidationError) as exc:
        EventAttemptRecord.model_validate(_minimal_event_attempt_payload("bogus"))
    assert "EventAttemptRecord.status 'bogus'" in str(exc.value)


def test_event_attempt_lifecycle_states_cover_current_runtime_emitters() -> None:
    runtime_emitted_statuses = {
        "planned",
        "running",
        "attempted_only",
        "verified",
        "blocked",
        "failed",
    }
    missing = runtime_emitted_statuses - EVENT_ATTEMPT_LIFECYCLE_STATES
    assert not missing, (
        f"Runtime emits statuses the contract does not accept: {sorted(missing)}"
    )


@patch("workflows.marketplace.client.httpx.Client", side_effect=AssertionError)
def test_baseline_extension_fixtures_resolve_from_local_artifacts_without_network(
    _mock_http_client: object,
) -> None:
    for publisher, name, version in BASELINE_EXTENSION_FIXTURES:
        resolved = download_and_extract_vsix(publisher, name, version)
        assert (
            resolved.resolve()
            == (_EXTENSIONS_DIR / f"{publisher}.{name}-{version}").resolve()
        )
        assert resolved.exists()


def test_baseline_extension_fixtures_round_trip_through_extension_schema() -> None:
    expected_activation_event_types = {
        "ms-python.python": {
            "onLanguage",
            "workspaceContains",
            "onLanguageModelTool",
            "onTerminalShellIntegration",
        },
        "extrace.fixture-chat": {"onChatParticipant"},
        "extrace.fixture-theme": set(),
    }

    for publisher, name, version in BASELINE_EXTENSION_FIXTURES:
        extension_id = f"{publisher}.{name}"
        extension_dir = _EXTENSIONS_DIR / f"{extension_id}-{version}"
        vsix_path = _EXTENSIONS_DIR / f"{extension_id}-{version}.vsix"

        package_json = get_package_json(extension_dir)
        parsed = ExtensionSchema.model_validate(package_json)
        round_tripped = parsed.model_dump(mode="json")
        contributes = parse_contributes(package_json) or {}
        activation_events = parse_activation_events(package_json) or []
        parsed_event_types = {item["event_type"] for item in activation_events}

        assert vsix_path.exists(), f"VSIX fixture missing for {extension_id}@{version}"
        assert ExtensionSchema.model_validate(round_tripped) == parsed
        assert parsed_event_types >= expected_activation_event_types[extension_id]
        assert len(activation_events) == len(package_json.get("activationEvents", []))
        assert all(
            "event_type" in item and "event_value" in item for item in activation_events
        )

        if extension_id == "extrace.fixture-chat":
            assert package_json["activationEvents"] == [
                "onChatParticipant:extrace.fixture-chat.agent"
            ]
        if extension_id == "extrace.fixture-theme":
            assert contributes["themes"][0]["label"] == "ExTrace Fixture Theme"
            assert activation_events == []


def test_trigger_payload_fixture_exposes_minimum_shape() -> None:
    fixture_path = (
        Path(__file__).parents[2]
        / "workflows"
        / "marketplace"
        / "fixtures"
        / "trigger_payloads"
        / "ms_python_python.json"
    )

    payload = _load_fixture(fixture_path)

    required_keys = {
        "analysis_profile",
        "target_extension_id",
        "selected_scenarios",
        "coverage_tracks",
        "coverage_summary",
        "event_attempts",
        "official_event_coverage",
    }

    assert required_keys.issubset(payload)
    assert payload["analysis_profile"] == "layered_deep"
    assert payload["target_extension_id"] == "ms-python.python"
    assert isinstance(payload["selected_scenarios"], list)
    assert isinstance(payload["coverage_tracks"], dict)
    assert isinstance(payload["coverage_summary"], dict)
    assert isinstance(payload["event_attempts"], list)
    assert isinstance(payload["official_event_coverage"], dict)

    parsed = TriggerPayload.model_validate(payload)
    round_tripped = parsed.model_dump(mode="json")

    assert TriggerPayload.model_validate(round_tripped) == parsed


def test_benign_fixture_detection_report_links_resolve_cleanly() -> None:
    fixture_path = (
        Path(__file__).parent
        / "fixtures"
        / "activation_reports"
        / "ms_python_python.json"
    )
    payload = _load_fixture(fixture_path)
    activation_report = ActivationReport.model_validate(payload)

    detection_report = run_detection(activation_report)

    assert (
        detection_report_invariant_issues(
            detection_report.model_dump(mode="json"), payload
        )
        == []
    )


def test_activation_report_invariants_detect_failed_scenario_drift() -> None:
    payload = {
        "summary": {
            "scenarios_run": ["coding_session"],
            "failed_scenarios": [],
        },
        "scenario_traces": [
            {
                "name": "coding_session",
                "started_at": 1.0,
                "ended_at": 2.0,
                "status": "failed",
            }
        ],
        "failed_scenarios": [],
        "trigger_execution_mode": "layered_passes",
        "stimulus_passes": [
            {
                "pass_id": "ui_first_user_session",
                "attempt_ids": ["attempt-1"],
            }
        ],
        "event_attempts": [
            {
                "attempt_id": "attempt-1",
                "status": "failed",
                "attempted_passes": ["ui_first_user_session"],
                "executor_action": "scenario:coding_session",
            }
        ],
        "official_event_coverage": {"track": "official"},
        "requested_scenarios": ["coding_session", "debug_session"],
    }

    issues = activation_report_invariant_issues(payload)

    assert "summary.failed_scenarios does not match failed scenario_traces." in issues
    assert "failed_scenarios does not match failed scenario_traces." in issues


def test_activation_report_invariants_detect_layered_reference_gaps() -> None:
    fixture_path = (
        Path(__file__).parent
        / "fixtures"
        / "activation_reports"
        / "ms_python_python.json"
    )
    report = deepcopy(_load_fixture(fixture_path))
    report["scenario_traces"] = [
        {
            "name": "project_exploration",
            "started_at": 10.0,
            "ended_at": 20.0,
            "status": "completed",
        }
    ]
    report["summary"]["scenarios_run"] = ["project_exploration"]
    report["summary"]["failed_scenarios"] = []
    report["failed_scenarios"] = []
    report["stimulus_passes"] = [
        {
            "pass_id": "workspace_bootstrap",
            "attempt_ids": ["missing-attempt"],
            "status": "completed",
        }
    ]
    report["event_attempts"] = [
        {
            "attempt_id": "attempt-1",
            "status": "attempted_only",
            "attempted_passes": ["missing-pass"],
            "executor_action": "scenario:coding_session",
        }
    ]
    report["official_event_coverage"] = {"track": "official"}

    issues = activation_report_invariant_issues(report)

    assert (
        "stimulus_passes reference unknown event_attempt ids: missing-attempt" in issues
    )
    assert "event_attempts reference unknown stimulus_pass ids: missing-pass" in issues
    assert (
        "scenario-style event_attempts have runtime evidence but no matching "
        "scenario_traces: coding_session"
    ) in issues
