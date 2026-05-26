"""W19-3 [GOAL harness-verification-contract-event-level] invariants.

Pins the bridge contract between the new
``EventAttemptRecord.confirmation_source`` field landed in W19-3 and the
existing ``automation_health.reasons`` emission rules that surfaced the
W19 driving signal (`harness_verification_unconfirmed_present` was one
of four reasons reported by the 2026-05-21 Codex live-run validation of
``ms-python.python`` @ ``992ad028f3df``).

W19-3 is schema-only: the field lands at default ``"none"`` everywhere
and emit-site stamps wait for W19-4 (``"harness_nonce"`` for the
``onDebug*`` family) and W19-5 (``"log_record"`` for
``onTerminalShellIntegration`` + ``onLanguageModelTool:*`` local-only
confirmation). The tests below pin three W19-3-shaped invariants:

1. Executor dataclass ↔ Pydantic model field parity (wire shape stays
   round-trip-clean across the trigger-payload boundary).
2. Default ``"none"`` is back-compat — a pre-W19-3 attempt dict that
   omits the field deserializes through ``populate_report_from_trigger_payload``
   and lands at ``confirmation_source="none"``.
3. The new field is orthogonal to the existing
   ``harness_verification_unconfirmed_present`` reason emission rule at
   ``executor/flows/playwright/health/summary.py:327-332`` — setting a
   non-default ``confirmation_source`` on an attempt that carries
   ``failure_reason_code="harness_verification_unconfirmed"`` still
   triggers the reason; setting one on an attempt that does not carry
   the failure code still does not.

The reason-emission rule itself is pinned by
``test_playwright_health_summary.py::test_harness_verification_unconfirmed_attempt_propagates_to_health_reasons``;
the tests below do not duplicate that pin — they prove the W19-3 schema
landing did not regress it.
"""

from __future__ import annotations

from dataclasses import fields as dataclass_fields

import pytest
from pydantic import ValidationError

from executor.flows.playwright.health.summary import (
    build_automation_health,
    build_run_quality,
)
from executor.flows.playwright.monitor.payload import (
    populate_report_from_trigger_payload,
)
from executor.flows.playwright.monitor.records import (
    EventAttemptRecord as ExecutorEventAttemptRecord,
)
from executor.flows.playwright.monitor.records import (
    LogStreamEntry,
)
from executor.flows.playwright.monitor.types import ActivationReport
from executor.flows.playwright.runtime_capture.events import ActivationEntry
from packages.analysis_contracts import (
    EventAttemptRecord as ContractEventAttemptRecord,
)


_W19_3_DOCUMENTED_CONFIRMATION_SOURCES = ("harness_nonce", "log_record", "none")


def _minimal_attempt_dict(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "attempt_id": "probe-1",
        "declared_event": "onCommand:test",
        "activation_event": "onCommand:test",
        "event_family": "onCommand",
        "executor_action": "harness:run_current_stimulus",
        "status": "attempted_only",
    }
    base.update(overrides)
    return base


class _PayloadStub:
    """Bare trigger-payload shape consumed by ``populate_report_from_trigger_payload``."""

    def __init__(self, event_attempts: list[dict[str, object]]) -> None:
        self.event_attempts = event_attempts
        self.stimulus_passes: list[dict[str, object]] = []
        self.prerequisite_results: list[dict[str, object]] = []
        self.coverage_tracks: dict[str, object] = {}
        self.coverage_summary: dict[str, object] = {}
        self.coverage_matrix: list[object] = []
        self.official_event_coverage: dict[str, object] = {}
        self.heuristic_workflow_coverage: dict[str, object] = {}
        self.selected_scenarios: list[str] = []
        self.target_extension_id: str = ""


def _partial_evidence_report() -> ActivationReport:
    target_id = "publisher.tool"
    report = ActivationReport()
    report.target_extension_id = target_id
    report.extension_host_output = "host output"
    report.activated.append(
        ActivationEntry(
            extension_id=target_id,
            activation_event="onCommand:test",
            timestamp="2026-01-01 10:00:00.000",
            source="log",
        )
    )
    report.log_entries.append(
        LogStreamEntry(
            stream="target_extension_host",
            kind="activation",
            extension_id=target_id,
            message="Activated publisher.tool",
            is_target_extension=True,
        )
    )
    report.trigger_plan_requested = True
    report.trigger_plan_loaded = True
    report.trigger_plan_applied = True
    report.trigger_execution_mode = "layered_passes"
    return report


def test_executor_dataclass_and_pydantic_contract_share_confirmation_source_field() -> (
    None
):
    """W19-3 wire-shape parity: both ledger types carry the new field.

    W19-6 widening: assertion now checks the *full field-set parity*
    between the executor dataclass and the Pydantic contract (not just
    the W19-3 `confirmation_source` addition). Future field additions
    to `EventAttemptRecord` must land on both sides in the same commit
    or this gate breaks — preventing the kind of silent half-landing
    that the W19-3-followup-2 audit (2026-05-25) called out as a
    standing risk.
    """
    executor_field_names = {
        f.name for f in dataclass_fields(ExecutorEventAttemptRecord)
    }
    contract_field_names = set(ContractEventAttemptRecord.model_fields.keys())

    # W19-3 pin (preserved): the specific field that motivated the W19-3
    # schema landing must be on both sides.
    assert "confirmation_source" in executor_field_names
    assert "confirmation_source" in contract_field_names

    executor_default = next(
        f
        for f in dataclass_fields(ExecutorEventAttemptRecord)
        if f.name == "confirmation_source"
    ).default
    contract_default = ContractEventAttemptRecord.model_fields[
        "confirmation_source"
    ].default

    assert executor_default == "none"
    assert contract_default == "none"

    # W19-6 widening: full field-set parity. Any future addition (or
    # removal) of an `EventAttemptRecord` field must land symmetrically
    # on both sides; an asymmetric landing breaks this gate.
    assert executor_field_names == contract_field_names, (
        "EventAttemptRecord field-set drift detected — "
        f"executor-only fields: {sorted(executor_field_names - contract_field_names)}; "
        f"contract-only fields: {sorted(contract_field_names - executor_field_names)}"
    )


def test_trigger_payload_deserialization_defaults_confirmation_source_to_none() -> None:
    """Pre-W19-3 attempt dict (no confirmation_source) lands at 'none'."""
    report = ActivationReport()
    populate_report_from_trigger_payload(
        report,
        _PayloadStub([_minimal_attempt_dict()]),
    )
    assert len(report.event_attempts) == 1
    assert report.event_attempts[0].confirmation_source == "none"


@pytest.mark.parametrize("source", _W19_3_DOCUMENTED_CONFIRMATION_SOURCES)
def test_trigger_payload_deserialization_preserves_confirmation_source(
    source: str,
) -> None:
    """Documented confirmation_source values flow through the payload boundary."""
    report = ActivationReport()
    populate_report_from_trigger_payload(
        report,
        _PayloadStub([_minimal_attempt_dict(confirmation_source=source)]),
    )
    assert report.event_attempts[0].confirmation_source == source


def test_confirmation_source_validator_rejects_unknown_value_on_contract() -> None:
    """Validator pins the closed set; unknown values fail at ingest."""
    with pytest.raises(ValidationError) as exc:
        ContractEventAttemptRecord.model_validate(
            {
                "attempt_id": "probe-1",
                "declared_event": "onCommand:test",
                "activation_event": "onCommand:test",
                "event_family": "onCommand",
                "confirmation_source": "remote_service_call",
            }
        )
    assert "EventAttemptRecord.confirmation_source 'remote_service_call'" in str(
        exc.value
    )


@pytest.mark.parametrize("source", _W19_3_DOCUMENTED_CONFIRMATION_SOURCES)
def test_confirmation_source_is_orthogonal_to_unconfirmed_reason_emission(
    source: str,
) -> None:
    """W19-3 schema landing must not regress the existing reason rule.

    The ``harness_verification_unconfirmed_present`` reason is emitted iff
    any ``event_attempt`` carries
    ``failure_reason_code="harness_verification_unconfirmed"``. The new
    ``confirmation_source`` field is orthogonal to that rule today (W19-4
    and W19-5 wire it later); whether the field is at default ``"none"``
    or a populated value must not change emission for an attempt that
    carries the failure code.
    """
    report = _partial_evidence_report()
    report.event_attempts = [
        ExecutorEventAttemptRecord(
            attempt_id="probe-1",
            declared_event="onCommand:test",
            activation_event="onCommand:test",
            event_family="onCommand",
            executor_action="harness:run_current_stimulus",
            status="attempted_only",
            failure_reason_code="harness_verification_unconfirmed",
            confirmation_source=source,
        )
    ]

    health = build_automation_health(
        report,
        extension_host_log_found=True,
        extension_host_log_present=True,
    )
    quality, _ = build_run_quality(report, automation_health=health)

    assert "harness_verification_unconfirmed_present" in health["reasons"]
    assert health["status"] == "degraded"
    assert quality == "medium"


@pytest.mark.parametrize("source", _W19_3_DOCUMENTED_CONFIRMATION_SOURCES)
def test_confirmation_source_alone_does_not_trigger_unconfirmed_reason(
    source: str,
) -> None:
    """A populated confirmation_source without the failure code stays clean.

    Inverse orthogonality pin: an attempt that carries a non-default
    ``confirmation_source`` but does NOT carry
    ``failure_reason_code="harness_verification_unconfirmed"`` must not
    cause the reason to appear. Guards against a future W19-4/W19-5 emit
    site accidentally re-purposing the field as a reason trigger.
    """
    report = _partial_evidence_report()
    report.event_attempts = [
        ExecutorEventAttemptRecord(
            attempt_id="probe-2",
            declared_event="onCommand:test",
            activation_event="onCommand:test",
            event_family="onCommand",
            executor_action="harness:run_current_stimulus",
            status="verified",
            confirmation_source=source,
        )
    ]

    health = build_automation_health(
        report,
        extension_host_log_found=True,
        extension_host_log_present=True,
    )

    assert "harness_verification_unconfirmed_present" not in health["reasons"]
