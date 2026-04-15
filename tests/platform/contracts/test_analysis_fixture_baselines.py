from __future__ import annotations

import json
from pathlib import Path

from packages.analysis_contracts import ActivationReport, TriggerPayload


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
