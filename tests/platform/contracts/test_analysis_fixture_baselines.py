from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from packages.analysis_contracts import (
    ActivationReport,
    TriggerPayload,
    activation_report_invariant_issues,
    scenario_trace_names,
)


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
        "verdict",
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
    assert isinstance(report["verdict"], dict)
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
    assert report["requested_scenarios"] != report["summary"]["scenarios_run"]
    assert report["summary"]["scenarios_run"] == scenario_trace_names(report)
    assert activation_report_invariant_issues(report) == []

    parsed = ActivationReport.model_validate(report)
    round_tripped = parsed.model_dump(mode="json")

    assert ActivationReport.model_validate(round_tripped) == parsed


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
