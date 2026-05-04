"""W11-3 contract tests.

Pin the three schema-2.1 additions:
* ``activation_discovery_strategies`` — list[str], populated by
  ``MonitorRuntime.stop()`` via the ``ReportAssembler`` callback.
* ``runner_exit_code`` — int | None, populated by ``entrypoint_runner``
  immediately before ``SystemExit``.
* ``runner_status`` — RunnerStatusLiteral, derived from exit_code by
  the assembler (`0 -> success`, `!= 0 -> error`, no call -> `unknown`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from packages.analysis_contracts import (
    ACTIVATION_REPORT_SCHEMA_VERSION,
    ActivationReport,
    RunnerStatusLiteral,
)


_FIXTURE = (
    Path(__file__).parent / "fixtures" / "activation_reports" / "ms_python_python.json"
)


def _load_baseline() -> dict[str, object]:
    payload = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    payload["schema_version"] = ACTIVATION_REPORT_SCHEMA_VERSION
    return payload


def test_default_construction_initializes_w11_3_fields() -> None:
    """Pin the post-W11-3 defaults so producers that never call the
    assembler setters still emit a contract-valid report."""
    report = ActivationReport(
        report_version=1,
        target_extension_expected="example.target",
        automation_health={
            "status": "inconclusive",
            "reasons": [],
            "trigger_requested": False,
            "trigger_loaded": False,
            "trigger_applied": False,
        },
        signal_summary={},
        summary={},
        scenario_traces=[],
        evidence_events=[],
        network_events=[],
        file_events=[],
        log_streams={},
    )

    assert report.activation_discovery_strategies == []
    assert report.runner_exit_code is None
    assert report.runner_status == "unknown"


def test_round_trip_with_w11_3_fields_populated() -> None:
    """Producer-shaped payload with all three new fields set survives
    validate -> dump -> validate without loss."""
    payload = _load_baseline()
    payload["activation_discovery_strategies"] = [
        "exthost_log_parse",
        "exthost_output_parse",
    ]
    payload["runner_exit_code"] = 0
    payload["runner_status"] = "success"

    parsed = ActivationReport.model_validate(payload)
    dumped = parsed.model_dump(mode="json")

    assert dumped["activation_discovery_strategies"] == [
        "exthost_log_parse",
        "exthost_output_parse",
    ]
    assert dumped["runner_exit_code"] == 0
    assert dumped["runner_status"] == "success"

    reparsed = ActivationReport.model_validate(dumped)
    assert reparsed == parsed


@pytest.mark.parametrize("status", ["success", "error", "unknown"])
def test_accepts_all_runner_status_literal_values(
    status: RunnerStatusLiteral,
) -> None:
    """The assembler maps exit_code -> status and writes the result
    here; every value the producer can emit must validate."""
    payload = _load_baseline()
    payload["runner_status"] = status

    parsed = ActivationReport.model_validate(payload)
    assert parsed.runner_status == status


def test_rejects_unknown_runner_status_value() -> None:
    """Defends against producer drift sneaking a new status string past
    the typed contract — analysts read this enum to short-circuit
    activation_health rollup, so an unrecognized value must fail fast."""
    payload = _load_baseline()
    payload["runner_status"] = "timeout"

    with pytest.raises(ValidationError):
        ActivationReport.model_validate(payload)


def test_rejects_non_int_runner_exit_code() -> None:
    """Non-coercible inputs (list, dict, arbitrary str) are rejected;
    pydantic's lenient int parser still folds in numeric strings, so
    pin the rejection on a value the parser cannot legally interpret."""
    payload = _load_baseline()
    payload["runner_exit_code"] = ["nonzero"]

    with pytest.raises(ValidationError):
        ActivationReport.model_validate(payload)


def test_rejects_non_list_activation_discovery_strategies() -> None:
    payload = _load_baseline()
    payload["activation_discovery_strategies"] = "exthost_log_parse"

    with pytest.raises(ValidationError):
        ActivationReport.model_validate(payload)


def test_strict_contract_model_extras_still_forbidden() -> None:
    """The new field block sits before the model validators; pin that
    StrictContractModel's ``extra=forbid`` behavior covers the new
    surface (i.e. typo'd `runner_exit` is rejected, not silently
    dropped)."""
    payload = _load_baseline()
    payload["runner_exit"] = 0  # intentional typo

    with pytest.raises(ValidationError):
        ActivationReport.model_validate(payload)


def test_runner_exit_code_accepts_none_when_runner_never_finalized() -> None:
    """The runner can fail to call set_runner_status (e.g. cancelled
    job whose monitor stopped before runner cleanup); the field default
    survives that path."""
    payload = _load_baseline()
    payload["runner_exit_code"] = None
    payload["runner_status"] = "unknown"

    parsed = ActivationReport.model_validate(payload)
    assert parsed.runner_exit_code is None
    assert parsed.runner_status == "unknown"
