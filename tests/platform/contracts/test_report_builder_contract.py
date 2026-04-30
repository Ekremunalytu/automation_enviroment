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
from pathlib import Path

import pytest

from packages.analysis_contracts.contracts import ActivationReport

_PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[3] / "executor" / "flows" / "playwright"
)
if str(_PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(_PLAYWRIGHT_DIR))

from report_builder import (  # noqa: E402
    ReportContractError,
    _validate_report_against_contract,
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
