"""W16 carry-over pin (post-W16-7): ``unaccounted_dropout`` surface round-trip.

W14-1's symptomatic fix (conservation accountant) is already pinned by
the accountant-level unit tests in
``tests/executor/test_playwright_monitor_scenario_accountant.py`` and the
W14-1 root-cause repro vectors in
``tests/security/test_scenario_dropout_repro.py``. W16-1 added the
**upstream emit-site instrumentation** that surfaces silent dispatch
drops to the same accountant — closing the bug class instead of the
symptom.

This module pins the **post-save report surface** for the
``unaccounted_dropout`` reason_code, mirroring the live shape observed
in the W16 close-out production scan
(``output/activation_report_ms-python.python-2026.5.2026051501-8d552b05271e.json``,
``2026-05-18`` 13:41). The scan showed 5 requested scenarios, 3 ran, 2
surfaced as ``unaccounted_dropout`` with the W16-1 ``detail`` string —
which is exactly the regression-vs-silent-dropout signal operators
read from the JSON.

Why a post-save pin in addition to the accountant unit tests: those
test ``record.reason_code == "unaccounted_dropout"`` at the dataclass
level, but the JSON consumed by the analyst console + UI is the result
of ``ActivationReport.save()`` →
``build_report_data()`` → ``save_report_payload()`` (strict-forbid
contract round-trip via
``packages/analysis_contracts/contracts.ActivationReport``). A future
refactor that drops the field from the contract, the report builder,
or the SkippedScenarioRecord serialization would silently break the
operator-visible surface without failing any accountant-level test.
This file catches that class of drift.

Companion regression file for the five additive top-level scalars:
``tests/security/test_report_finalize_field_sync.py`` (W16-3).
"""

from __future__ import annotations

import json
from pathlib import Path

from executor.flows.playwright.monitor.records import (
    ScenarioTrace,
    SkippedScenarioRecord,
)
from executor.flows.playwright.monitor.types import ActivationReport


_UNACCOUNTED_DROPOUT_DETAIL = (
    "Scenario was requested but never recorded as run, "
    "failed, or skipped by the upstream planner / "
    "executor / harness."
)


def _report_with_two_unaccounted_dropouts() -> ActivationReport:
    """Mirror the live scan shape: 5 requested, 3 ran, 2 unaccounted_dropout.

    The conservation accountant in
    ``executor/flows/playwright/monitor/scenario_accountant.py:427-438``
    is what writes these records on the live path. Here the records are
    populated directly so the test stays decoupled from the accountant
    and isolates the **save-time surface** the contract round-trip can
    drop.
    """
    report = ActivationReport(target_extension_id="publisher.tool")
    report.requested_scenarios = [
        "coding_session",
        "project_exploration",
        "debug_session",
        "terminal_usage",
        "refactor_workflow",
    ]
    report.scenarios_run = [
        "coding_session",
        "project_exploration",
        "terminal_usage",
    ]
    report.scenario_traces = [
        ScenarioTrace(name="coding_session", started_at=0.0, status="completed"),
        ScenarioTrace(
            name="project_exploration", started_at=0.0, status="completed"
        ),
        ScenarioTrace(name="terminal_usage", started_at=0.0, status="completed"),
    ]
    report.skipped_scenarios = [
        SkippedScenarioRecord(
            name="debug_session",
            reason_code="unaccounted_dropout",
            detail=_UNACCOUNTED_DROPOUT_DETAIL,
        ),
        SkippedScenarioRecord(
            name="refactor_workflow",
            reason_code="unaccounted_dropout",
            detail=_UNACCOUNTED_DROPOUT_DETAIL,
        ),
    ]
    return report


def test_save_persists_unaccounted_dropout_records_with_reason_and_detail(
    tmp_path: Path,
) -> None:
    """Top-level ``skipped_scenarios`` keeps ``name``, ``reason_code``, ``detail``.

    Survives the strict-forbid contract validation in
    ``packages/analysis_contracts/contracts.ActivationReport``. If a
    future refactor narrows the contract's ``skipped_scenarios`` slot
    (e.g. drops ``detail`` or coerces ``reason_code`` to an enum that
    omits ``unaccounted_dropout``), this assertion catches it before
    the operator-visible JSON loses the signal.
    """
    report = _report_with_two_unaccounted_dropouts()
    out = tmp_path / "report.json"

    report.save(out, announce=False)
    payload = json.loads(out.read_text(encoding="utf-8"))

    records = {item["name"]: item for item in payload["skipped_scenarios"]}
    assert set(records) == {"debug_session", "refactor_workflow"}
    for record in records.values():
        assert record["reason_code"] == "unaccounted_dropout"
        assert record["detail"] == _UNACCOUNTED_DROPOUT_DETAIL


def test_save_propagates_unaccounted_dropout_to_automation_health(
    tmp_path: Path,
) -> None:
    """``automation_health.skipped_scenarios`` (names) + ``status='degraded'`` + ``'skipped_scenarios_present'`` reason.

    Pins the W16-1 + W14-1 honesty invariant from the operator chip:
    when the report carries any ``unaccounted_dropout`` records,
    ``executor/flows/playwright/health/summary.py:305-306`` must add
    ``'skipped_scenarios_present'`` to ``automation_health.reasons``
    and the status must not be ``'healthy'``.
    """
    report = _report_with_two_unaccounted_dropouts()
    out = tmp_path / "report.json"

    report.save(out, announce=False)
    payload = json.loads(out.read_text(encoding="utf-8"))

    health = payload["automation_health"]
    assert sorted(health["skipped_scenarios"]) == [
        "debug_session",
        "refactor_workflow",
    ]
    assert "skipped_scenarios_present" in health["reasons"]
    assert health["status"] != "healthy"


def test_save_propagates_unaccounted_dropout_to_run_quality(
    tmp_path: Path,
) -> None:
    """``run_quality_reasons`` carries the human-readable skipped-scenarios line.

    The mapping
    ``executor/flows/playwright/health/summary.py:25``
    binds ``skipped_scenarios_present`` →
    ``"One or more requested scenarios were skipped."``. Operators
    reading ``run_quality_reasons`` (UI report header + JSON downloads)
    must see this exact line whenever an unaccounted dropout is
    surfaced — otherwise the report drops to ``low`` quality with no
    visible cause.
    """
    report = _report_with_two_unaccounted_dropouts()
    out = tmp_path / "report.json"

    report.save(out, announce=False)
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert (
        "One or more requested scenarios were skipped."
        in payload["run_quality_reasons"]
    )
    assert payload["run_quality"] != "high"
