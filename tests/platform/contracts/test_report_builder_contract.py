"""Prevent executor→API contract drift at the report serialization boundary.

The executor builds the activation report from local dataclasses and serializes
via ``dataclasses.asdict``. The API consumes the same JSON through the Pydantic
``ActivationReport`` contract (``StrictContractModel`` → ``extra="forbid"``).

Historically these two sides have drifted silently: the executor would grow a
new field, `asdict` would emit it, and the API would 500 on the next poll.
``save_report_payload`` now validates the payload against the authoritative
Pydantic contract before writing. These tests lock that gate in place so that:

1. Representative payloads continue to round-trip.
2. Unknown fields (the exact shape of past drift) fail the gate.
3. ``RiskSignal.details`` — the field that caused the original outage — stays
   in the contract and survives the round-trip with non-empty content.
"""

from __future__ import annotations

import copy
import json
import sys
import warnings
from pathlib import Path

import pytest
from pydantic import ValidationError

from packages.analysis_contracts.contracts import (
    ACTIVATION_REPORT_SCHEMA_VERSION,
    ActivationReport,
)

_PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[3] / "executor" / "flows" / "playwright"
)
if str(_PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(_PLAYWRIGHT_DIR))

from report_builder import (  # noqa: E402
    ReportContractError,
    _validate_report_against_contract,
    build_report_data,
    save_report_payload,
)


_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "activation_reports" / "ms_python_python.json"
)


def _load_fixture() -> dict[str, object]:
    payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_baseline_fixture_passes_producer_gate() -> None:
    """The canonical ms-python fixture must satisfy the producer gate."""

    _validate_report_against_contract(_load_fixture())


def test_producer_gate_rejects_unknown_top_level_field() -> None:
    """Unknown top-level fields simulate dataclass drift and must fail fast."""

    payload = _load_fixture()
    payload["some_new_executor_field"] = "drifted"

    with pytest.raises(ReportContractError) as excinfo:
        _validate_report_against_contract(payload)
    assert "some_new_executor_field" in str(excinfo.value)


def test_producer_gate_rejects_unknown_risk_signal_field() -> None:
    """Nested drift (the exact shape of the original outage) must fail fast."""

    payload = _load_fixture()
    risk_signals = list(payload.get("risk_signals") or [])
    if not risk_signals:
        risk_signals.append(
            {
                "signal_id": "test_signal",
                "category": "test",
                "severity": "info",
                "confidence": 0.5,
            }
        )
    risk_signals[0] = {**risk_signals[0], "unknown_field": "drifted"}
    payload["risk_signals"] = risk_signals

    with pytest.raises(ReportContractError) as excinfo:
        _validate_report_against_contract(payload)
    message = str(excinfo.value)
    assert "risk_signals" in message
    assert "unknown_field" in message


def test_risk_signal_details_round_trips_through_contract() -> None:
    """``RiskSignal.details`` — the field that caused the outage — must survive
    a full validate/dump round-trip."""

    payload = _load_fixture()
    risk_signals = list(payload.get("risk_signals") or [])
    if not risk_signals:
        risk_signals.append(
            {
                "signal_id": "background_outbound_network",
                "category": "network",
                "severity": "medium",
                "confidence": 0.8,
                "summary": "Background extension reached out to an unclassified host.",
                "evidence_event_ids": [],
            }
        )
    risk_signals[0] = {
        **risk_signals[0],
        "details": {"peer": "example.com", "bytes": 1024},
    }
    payload["risk_signals"] = risk_signals

    parsed = ActivationReport.model_validate(payload)
    round_tripped = parsed.model_dump(mode="json")
    assert round_tripped["risk_signals"][0]["details"] == {
        "peer": "example.com",
        "bytes": 1024,
    }


def test_save_report_payload_writes_when_contract_is_satisfied(tmp_path: Path) -> None:
    payload = _load_fixture()
    out_path = tmp_path / "activation_report.json"

    result = save_report_payload(out_path, payload, announce=False)

    assert result == out_path
    assert out_path.exists()
    on_disk = json.loads(out_path.read_text(encoding="utf-8"))
    assert on_disk["target_extension_expected"] == payload["target_extension_expected"]


def test_save_report_payload_refuses_to_write_drifted_payload(tmp_path: Path) -> None:
    payload = _load_fixture()
    payload["ghost_field"] = "should never reach disk"
    out_path = tmp_path / "activation_report.json"

    with pytest.raises(ReportContractError):
        save_report_payload(out_path, payload, announce=False)

    assert not out_path.exists(), (
        "Producer gate must refuse the write, not merely validate after the fact."
    )


def test_minimal_report_roundtrips_with_populated_risk_signal_details() -> None:
    """A minimal hand-built report with ``details`` populated must validate.

    Locks the contract surface so future executor dataclass changes cannot
    silently remove support for ``details``.
    """

    minimal = {
        "report_version": 2,
        "target_extension_expected": "extrace.smoke",
        "automation_health": {},
        "signal_summary": {},
        "summary": {},
        "scenario_traces": [],
        "evidence_events": [],
        "network_events": [],
        "file_events": [],
        "log_streams": {"automation": []},
        "risk_signals": [
            {
                "signal_id": "synthetic.regression_guard",
                "category": "synthetic",
                "severity": "info",
                "confidence": 0.0,
                "evidence_event_ids": [],
                "summary": "Regression guard for RiskSignal.details field.",
                "details": {"reason": "contract-pinning"},
            }
        ],
    }

    parsed = ActivationReport.model_validate(minimal)
    dumped = parsed.model_dump(mode="json")
    assert dumped["risk_signals"][0]["details"] == {"reason": "contract-pinning"}


def test_empty_risk_signal_details_is_permitted() -> None:
    """Defaulted empty ``details`` must also pass — existing fixtures rely on it."""

    minimal = {
        "report_version": 2,
        "target_extension_expected": "extrace.smoke",
        "automation_health": {},
        "signal_summary": {},
        "summary": {},
        "scenario_traces": [],
        "evidence_events": [],
        "network_events": [],
        "file_events": [],
        "log_streams": {"automation": []},
        "risk_signals": [
            {
                "signal_id": "synthetic.regression_guard",
                "category": "synthetic",
                "severity": "info",
                "confidence": 0.0,
                "details": {},
            }
        ],
    }

    parsed = ActivationReport.model_validate(minimal)
    assert parsed.risk_signals[0].details == {}


def test_copy_isolation_is_safe() -> None:
    """Ensure the test helpers don't mutate the fixture between cases."""

    payload = _load_fixture()
    _ = copy.deepcopy(payload)
    _validate_report_against_contract(payload)


def test_save_report_payload_persists_schema_version_when_input_omits_it(
    tmp_path: Path,
) -> None:
    """W10-FIXUP-1 regression pin: ``save_report_payload`` must write the
    parsed-and-dumped payload, so the ``schema_version`` injected by
    ``_validate_schema_version`` reaches disk even when the caller omits it.

    Pre-FIXUP, the validator's mutation lived only in the parsed model and
    the original (version-less) dict was serialized verbatim — defeating the
    whole point of the W10-1 evolution discipline at the on-disk boundary.
    """

    payload = _load_fixture()
    payload.pop("schema_version", None)
    out_path = tmp_path / "activation_report.json"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        save_report_payload(out_path, payload, announce=False)

    on_disk = json.loads(out_path.read_text(encoding="utf-8"))
    assert on_disk["schema_version"] == ACTIVATION_REPORT_SCHEMA_VERSION


class _MinimalReportFake:
    """Hand-rolled stand-in for the ``ActivationReport`` dataclass surface
    that ``build_report_data`` reads via ``getattr``. Only the fields the
    builder actually touches are populated; everything else falls back to
    the ``getattr`` default. Lets us assert the W11-3 surface is wired in
    one direction (dataclass → dict → contract round-trip) without
    spinning up the full executor module graph.
    """

    def __init__(
        self,
        *,
        activation_discovery_strategies: list[str],
        runner_exit_code: int | None,
        runner_status: str,
    ) -> None:
        self.activation_discovery_strategies = activation_discovery_strategies
        self.runner_exit_code = runner_exit_code
        self.runner_status = runner_status
        # Minimum surface for the rest of build_report_data to succeed.
        self.report_version = 2
        self.target_extension_id = "extrace.smoke"
        self.target_extension_observed = False
        self.trigger_plan_requested = False
        self.trigger_plan_loaded = False
        self.trigger_plan_applied = False
        self.trigger_plan_path = ""
        self.trigger_execution_mode = ""
        self.requested_scenarios: list[str] = []
        self.failed_scenarios: list[str] = []
        self.skipped_scenarios: list[object] = []
        self.extra_trigger_failures: list[str] = []
        self.verification_gap = 0
        self.heuristic_verification_gap = 0
        self.run_quality_reasons: list[str] = []
        self.signal_summary: dict[str, object] = {}
        self.runtime_official_attempted_capabilities: list[str] = []
        self.official_verified_capabilities: list[str] = []
        self.runtime_heuristic_attempted_capabilities: list[str] = []
        self.supported_heuristic_verified_capabilities: list[str] = []
        self.network_capture_error = ""
        self.file_capture_error = ""
        self.file_capture_diagnostics: dict[str, object] = {}
        self.activated: list[object] = []
        self.running_extensions: list[object] = []
        self.network_events: list[object] = []
        self.file_events: list[object] = []
        self.process_events: list[object] = []
        self.output_signal_events: list[object] = []
        self.scenario_traces: list[object] = []
        self.stimulus_passes: list[object] = []
        self.prerequisite_results: list[object] = []
        self.event_attempts: list[object] = []
        self.network_summary: dict[str, object] = {}
        self.file_summary: dict[str, object] = {}
        self.coverage_summary: dict[str, object] = {}
        self.coverage_matrix: list[object] = []
        self.coverage_tracks: dict[str, object] = {}
        self.official_event_coverage: dict[str, object] = {}
        self.heuristic_workflow_coverage: dict[str, object] = {}
        self.log_streams: dict[str, list[object]] = {"automation": []}
        self.extension_host_output = ""
        self.log_file_path = ""


def test_w11_3_fields_round_trip_through_build_report_data_and_save(
    tmp_path: Path,
) -> None:
    """W11-3 producer values must survive ``build_report_data`` → contract
    validation → ``save_report_payload`` → on-disk JSON.

    Regression pin for the gap surfaced by the first W11-3 live scan,
    where ``ReportAssembler.set_runner_status`` and
    ``set_discovery_strategies`` mutated the dataclass correctly but the
    builder's manual ``asdict``-style serializer never read the new
    fields, so the on-disk payload defaulted them. This test fails on
    the pre-fix builder and passes once the builder explicitly forwards
    the three fields.
    """

    fake = _MinimalReportFake(
        activation_discovery_strategies=[
            "exthost_log_parse",
            "exthost_output_parse",
        ],
        runner_exit_code=0,
        runner_status="success",
    )
    minimal_health = {
        "status": "inconclusive",
        "reasons": [],
        "trigger_requested": False,
        "trigger_loaded": False,
        "trigger_applied": False,
    }
    data = build_report_data(
        fake,
        evidence_events=[],
        evidence_links=[],
        risk_signals=[],
        risk_summary={},
        run_quality="medium",
        automation_health=minimal_health,
        log_health={},
        attribution_summary={},
        summary={},
    )

    # Builder dict carries the fields straight through.
    assert data["activation_discovery_strategies"] == [
        "exthost_log_parse",
        "exthost_output_parse",
    ]
    assert data["runner_exit_code"] == 0
    assert data["runner_status"] == "success"

    # ...and so does the on-disk payload after the producer gate +
    # validate-then-dump round-trip.
    out_path = tmp_path / "activation_report.json"
    save_report_payload(out_path, data, announce=False)
    on_disk = json.loads(out_path.read_text(encoding="utf-8"))
    assert on_disk["activation_discovery_strategies"] == [
        "exthost_log_parse",
        "exthost_output_parse",
    ]
    assert on_disk["runner_exit_code"] == 0
    assert on_disk["runner_status"] == "success"


def test_w11_3_fields_default_to_unknown_when_producer_skips_setters(
    tmp_path: Path,
) -> None:
    """If the runtime never invokes the W11-3 setters (e.g. report-only
    ingest), the builder forwards the dataclass defaults and the
    contract preserves them: empty strategies list, ``None`` exit code,
    ``"unknown"`` status. This is the W11-3 ``unknown`` semantics
    locked at the serialization boundary."""

    fake = _MinimalReportFake(
        activation_discovery_strategies=[],
        runner_exit_code=None,
        runner_status="unknown",
    )
    minimal_health = {
        "status": "inconclusive",
        "reasons": [],
        "trigger_requested": False,
        "trigger_loaded": False,
        "trigger_applied": False,
    }
    data = build_report_data(
        fake,
        evidence_events=[],
        evidence_links=[],
        risk_signals=[],
        risk_summary={},
        run_quality="medium",
        automation_health=minimal_health,
        log_health={},
        attribution_summary={},
        summary={},
    )
    out_path = tmp_path / "activation_report.json"
    save_report_payload(out_path, data, announce=False)
    on_disk = json.loads(out_path.read_text(encoding="utf-8"))

    assert on_disk["activation_discovery_strategies"] == []
    assert on_disk["runner_exit_code"] is None
    assert on_disk["runner_status"] == "unknown"


def test_contract_rejects_missing_automation_health() -> None:
    """W10-FIXUP-2 regression pin: ``automation_health`` is a first-class
    required field at the report root. A producer regression that drops it
    must fail the contract gate, not silently default to an empty health
    ledger (which would erase the distinction between "we genuinely could
    not assess" and "we forgot to record")."""

    minimal_without_automation_health = {
        "report_version": 2,
        "target_extension_expected": "extrace.smoke",
        "signal_summary": {},
        "summary": {},
        "scenario_traces": [],
        "evidence_events": [],
        "network_events": [],
        "file_events": [],
        "log_streams": {"automation": []},
    }

    with pytest.raises(ValidationError) as excinfo:
        ActivationReport.model_validate(minimal_without_automation_health)

    assert "automation_health" in str(excinfo.value)
