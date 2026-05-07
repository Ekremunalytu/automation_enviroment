"""W11-3 + W12-2 contract tests.

Pin the three schema-2.1 additions (W12-2 upgrades the discovery field):
* ``activation_discovery_strategy_outcomes`` — dict[str, str], populated
  by ``MonitorRuntime.stop()`` via the ``ReportAssembler`` callback.
  Outcomes use the literals ``"succeeded_with_new_activations"``,
  ``"succeeded_no_new_activations"``, and ``"failed:<ExcClassName>"``
  (the W12-2 outcome-detail upgrade from W11-3's list[str]).
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

    assert report.activation_discovery_strategy_outcomes == {}
    assert report.runner_exit_code is None
    assert report.runner_status == "unknown"


def test_round_trip_with_w12_2_fields_populated() -> None:
    """Producer-shaped payload with all three new fields set survives
    validate -> dump -> validate without loss."""
    payload = _load_baseline()
    payload["activation_discovery_strategy_outcomes"] = {
        "exthost_log_parse": "succeeded_with_new_activations",
        "running_extensions_ui": "succeeded_no_new_activations",
        "exthost_output_parse": "failed:OSError",
    }
    payload["runner_exit_code"] = 0
    payload["runner_status"] = "success"

    parsed = ActivationReport.model_validate(payload)
    dumped = parsed.model_dump(mode="json")

    assert dumped["activation_discovery_strategy_outcomes"] == {
        "exthost_log_parse": "succeeded_with_new_activations",
        "running_extensions_ui": "succeeded_no_new_activations",
        "exthost_output_parse": "failed:OSError",
    }
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


def test_rejects_non_dict_activation_discovery_strategy_outcomes() -> None:
    payload = _load_baseline()
    payload["activation_discovery_strategy_outcomes"] = "exthost_log_parse"

    with pytest.raises(ValidationError):
        ActivationReport.model_validate(payload)


def test_accepts_failed_outcome_with_arbitrary_exception_class() -> None:
    """W12-2: ``failed:<ExcClassName>`` outcome literal carries the caught
    exception's class name verbatim. The contract field type is plain
    ``dict[str, str]`` so the literal validation lives on the producer
    side; this contract test just confirms the schema accepts the format
    the producer emits (e.g. ``failed:TimeoutError``,
    ``failed:ProcessLookupError``)."""
    payload = _load_baseline()
    payload["activation_discovery_strategy_outcomes"] = {
        "exthost_log_parse": "failed:TimeoutError",
        "running_extensions_ui": "failed:PlaywrightError",
        "exthost_output_parse": "failed:ProcessLookupError",
    }

    parsed = ActivationReport.model_validate(payload)
    assert (
        parsed.activation_discovery_strategy_outcomes["exthost_log_parse"]
        == "failed:TimeoutError"
    )


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


# --- W12-2 P3 legacy field migration regressions ---


def test_legacy_strategies_field_migrates_to_outcomes_dict() -> None:
    """Reports persisted between W11-3 and W12-2 P3 carry the legacy
    ``activation_discovery_strategies: list[str]`` under the same
    schema_version 2.1. ``StrictContractModel`` (extra=forbid) would
    reject those reports on ingest unless the before-validator drops
    the legacy field and synthesizes the new dict. The legacy list
    only carried "succeeded-and-produced-new" entries, so each id
    maps to ``"succeeded_with_new_activations"``."""
    payload = _load_baseline()
    payload["activation_discovery_strategies"] = [
        "exthost_log_parse",
        "running_extensions_ui",
    ]

    parsed = ActivationReport.model_validate(payload)
    assert parsed.activation_discovery_strategy_outcomes == {
        "exthost_log_parse": "succeeded_with_new_activations",
        "running_extensions_ui": "succeeded_with_new_activations",
    }


def test_legacy_strategies_field_dropped_when_new_field_present() -> None:
    """Defensive: if both fields are present (e.g. a producer wrote
    them in parallel during the W12-2 transition), the new field wins
    and the legacy field is dropped silently."""
    payload = _load_baseline()
    payload["activation_discovery_strategies"] = ["legacy_strategy_id"]
    payload["activation_discovery_strategy_outcomes"] = {
        "exthost_log_parse": "succeeded_with_new_activations",
    }

    parsed = ActivationReport.model_validate(payload)
    assert parsed.activation_discovery_strategy_outcomes == {
        "exthost_log_parse": "succeeded_with_new_activations",
    }


def test_legacy_strategies_non_list_payload_falls_back_to_empty_dict() -> None:
    """A malformed legacy field (e.g. None, a string, a dict typed by
    a buggy producer) is still dropped without raising, because the
    extra=forbid rejection it triggers would block ingest entirely.
    The migration coerces it to an empty outcomes dict."""
    payload = _load_baseline()
    payload["activation_discovery_strategies"] = None

    parsed = ActivationReport.model_validate(payload)
    assert parsed.activation_discovery_strategy_outcomes == {}
