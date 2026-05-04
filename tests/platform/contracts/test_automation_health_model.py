"""W10-4 contract tests: AutomationHealth typed projection."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.analysis_contracts import AutomationHealth, AutomationHealthStatusLiteral


def test_default_construction_is_inconclusive() -> None:
    health = AutomationHealth()
    assert health.status == "inconclusive"
    assert health.reasons == []
    assert health.target_activation_count == 0
    assert health.skipped_scenarios == []


def test_round_trip_from_executor_shaped_dict() -> None:
    """The producer (executor build_automation_health) emits a 14-field
    dict; the typed model must accept it without loss."""
    raw = {
        "status": "healthy",
        "reasons": [],
        "trigger_requested": True,
        "trigger_loaded": True,
        "trigger_applied": True,
        "extension_host_log_present": True,
        "extension_host_log_found": True,
        "extension_host_output_present": True,
        "target_stream_present": True,
        "target_activation_count": 1,
        "failed_scenarios": [],
        "extra_trigger_failures": [],
        "extra_trigger_failure_count": 0,
        "skipped_scenarios": [],
    }
    health = AutomationHealth.model_validate(raw)
    assert health.model_dump() == raw


@pytest.mark.parametrize("status", ["healthy", "degraded", "inconclusive"])
def test_accepts_all_producer_status_values(
    status: AutomationHealthStatusLiteral,
) -> None:
    health = AutomationHealth(status=status)
    assert health.status == status


def test_rejects_unknown_status_value() -> None:
    """ADR 0003 rollup keys off this status; an unknown value must fail
    fast at ingest, not silently degrade verdict semantics."""
    with pytest.raises(ValidationError):
        AutomationHealth.model_validate({"status": "ok"})


def test_extra_field_rejected() -> None:
    """StrictContractModel base forbids extras; defends against producer
    drift sneaking new fields past the typed contract."""
    with pytest.raises(ValidationError):
        AutomationHealth.model_validate({"status": "healthy", "unexpected": True})


def test_skip_automation_subset_validates() -> None:
    """The executor's skip_automation execution mode emits a 5-field
    subset of the full schema. Defaults must let it ingest cleanly."""
    raw = {
        "status": "healthy",
        "reasons": [],
        "trigger_requested": False,
        "trigger_loaded": False,
        "trigger_applied": False,
    }
    health = AutomationHealth.model_validate(raw)
    assert health.status == "healthy"
    assert health.target_activation_count == 0
