"""W14-1: Deterministic repro fixture for [BUG scenario-dropout-upstream-root-cause].

Pre-W14, the bug's last-mile catch
(``ScenarioAccountant._validate_scenario_conservation``,
``executor/flows/playwright/monitor/scenario_accountant.py:392-438``) reports
``unaccounted_dropout`` for scenarios that reach the report's
``requested_scenarios`` but never appear in any of ``scenarios_run`` /
``failed_scenarios`` / ``skipped_scenarios``. The upstream root cause (where in
planner / ``stimulus_passes`` / harness dispatch the scenarios disappear)
remained open.

W14-1 BLOCKER triage converts that BUG into a **deterministic, parametrized
repro** at the accountant boundary so any upstream regression that re-introduces
silent dropout fires this test FIRST (alongside the production conservation
guard). The matrix covers all currently-known dropout vectors:

* **vec_ms_python_python**: Live ms-python.python regression — 5 requested, 3
  ran, 2 silent drop. Sibling pin lives in
  ``tests/executor/test_playwright_monitor_scenario_accountant.py``; the W14-1
  version sits at the ``tests/security/`` boundary so the W7 §10.7 invariant is
  also gated from this layer.
* **vec_stimulus_collapse**: Stimulus dispatch returned an empty result (the
  ``dispatch._normalize_execution_result`` ``outcome is None`` branch at
  ``executor/flows/playwright/entrypoint/dispatch.py:91-95``) — every
  requested scenario surfaces as a dropout.
* **vec_all_accounted**: Healthy run — every requested scenario lands in
  exactly one bucket. Conservation guard MUST stay silent (no false-positive
  ``unaccounted_dropout``).
* **vec_all_explicit_skip**: Every requested scenario explicitly skipped with
  a known reason code (``harness_unavailable``). Conservation guard MUST stay
  silent.
* **vec_partial_failed**: Mixed bucket (ran + failed + explicit skip) covering
  every requested scenario. Conservation guard MUST stay silent.

Each vector pins the W14-1 stochastic-bound conclusion: even though the
upstream emit-site (planner / stimulus / dispatch) is still silent on *why* a
scenario was dropped, the last-mile conservation guard is the deterministic
fix-of-record — every dropout is caught and labelled. If an upstream layer is
later instrumented to emit a more-specific reason code (e.g. via
``stimulus.passes._record_scenario_reason`` or a future
``dispatch._normalize_execution_result`` diagnostic), individual vectors here
flip to expect the specific code instead of ``unaccounted_dropout``.

See [`documents/active-work/W14-codex-acceptance-observability.md`](../../documents/active-work/W14-codex-acceptance-observability.md)
§"W14-1 scope" for the BLOCKER triage decision record.

W16-1 (active 2026-05-18) closes the dispatch-layer half of that emit-site:
``_normalize_execution_result``'s ``outcome is None`` branch at
``executor/flows/playwright/entrypoint/dispatch.py`` now emits
``dispatch_outcome_none`` for each requested scenario, so the downstream
conservation guard no longer has to fall back to ``unaccounted_dropout`` when
the dispatcher collapsed. ``test_dispatch_outcome_none_emits_specific_reason_code``
below pins that upstream instrumentation directly. The existing
accountant-boundary vectors retain their last-mile fallback semantics for the
remaining (non-dispatch) silent drop sites — planner or future
``stimulus.passes`` layers that fail to record a specific reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from executor.flows.playwright.monitor.records import ScenarioTrace
from executor.flows.playwright.monitor.scenario_accountant import ScenarioAccountant
from executor.flows.playwright.monitor.types import ActivationReport


# ---------------------------------------------------------------------------
# Test helpers — locally defined to keep the W14-1 boundary independent of
# the sibling unit-test module's helpers.
# ---------------------------------------------------------------------------


@dataclass
class _SkipShape:
    """Minimal entry matching ``SkippedScenarioRecord`` for ``Any``-typed intake."""

    name: str
    reason_code: str
    detail: str = ""


@dataclass
class _ExecResult:
    """Minimal ``AutomationExecutionResult`` shape used at the accountant boundary."""

    requested_scenarios: list[str]
    skipped_scenarios: list[_SkipShape]
    extra_trigger_failures: list[str]
    failed_scenarios: list[str]


def _build_accountant() -> tuple[ScenarioAccountant, ActivationReport]:
    report = ActivationReport(target_extension_id="publisher.tool")

    def _persist(_force: bool) -> None:
        return None

    def _record_event(_kind: str, _message: str, **_kwargs: Any) -> None:
        return None

    accountant = ScenarioAccountant(
        report=report,
        record_automation_event=_record_event,
        persist=_persist,
    )
    return accountant, report


# ---------------------------------------------------------------------------
# W14-1 repro vectors — deterministic dropout matrix
# ---------------------------------------------------------------------------


# Each row: (vector_id, requested, ran, failed, explicit_skips, expected_dropouts)
_DROPOUT_VECTORS: list[
    tuple[str, list[str], list[str], list[str], list[tuple[str, str]], set[str]]
] = [
    (
        "vec_ms_python_python",
        [
            "coding_session",
            "project_exploration",
            "debug_session",
            "terminal_usage",
            "refactor_workflow",
        ],
        ["coding_session", "project_exploration", "terminal_usage"],
        [],
        [],
        {"debug_session", "refactor_workflow"},
    ),
    (
        "vec_stimulus_collapse",
        ["x1", "x2", "x3"],
        [],
        [],
        [],
        {"x1", "x2", "x3"},
    ),
    (
        "vec_all_accounted",
        ["s1", "s2"],
        ["s1", "s2"],
        [],
        [],
        set(),
    ),
    (
        "vec_all_explicit_skip",
        ["s1", "s2"],
        [],
        [],
        [("s1", "harness_unavailable"), ("s2", "harness_unavailable")],
        set(),
    ),
    (
        "vec_partial_failed",
        ["a", "b", "c"],
        ["a"],
        ["b"],
        [("c", "precondition_unmet")],
        set(),
    ),
]


def _build_traces(ran: list[str], failed: list[str]) -> list[ScenarioTrace]:
    """Mirror what ``_run_scenario_sequence`` writes during a real run.

    ``ScenarioAccountant._synchronize_scenario_truth`` derives both
    ``scenarios_run`` and ``failed_scenarios`` from ``scenario_traces`` (see
    ``scenario_accountant.py:440-452``); test fixtures therefore have to seed
    the trace list rather than the two derived lists.
    """
    traces: list[ScenarioTrace] = [
        ScenarioTrace(name=name, started_at=0.0, status="completed") for name in ran
    ]
    traces.extend(
        ScenarioTrace(name=name, started_at=0.0, status="failed") for name in failed
    )
    return traces


@pytest.mark.parametrize(
    "vector_id,requested,ran,failed,explicit_skips,expected_dropouts",
    _DROPOUT_VECTORS,
    ids=[entry[0] for entry in _DROPOUT_VECTORS],
)
def test_scenario_dropout_repro_matrix(
    vector_id: str,
    requested: list[str],
    ran: list[str],
    failed: list[str],
    explicit_skips: list[tuple[str, str]],
    expected_dropouts: set[str],
) -> None:
    """W14-1: every dropout vector resolves correctly under the last-mile guard.

    Non-empty ``expected_dropouts`` rows MUST surface each missing scenario
    with ``reason_code='unaccounted_dropout'``. Empty rows MUST keep
    ``unaccounted_dropout`` out of the report (no false positives). The W7
    §10.7 conservation invariant (``requested ⊆ run U failed U skipped``) MUST
    hold for every row.
    """
    accountant, report = _build_accountant()
    report.scenario_traces = _build_traces(ran, failed)

    accountant.record_execution_result(
        _ExecResult(
            requested_scenarios=list(requested),
            skipped_scenarios=[
                _SkipShape(name=name, reason_code=code) for name, code in explicit_skips
            ],
            extra_trigger_failures=[],
            failed_scenarios=list(failed),
        )
    )

    by_name = {record.name: record for record in report.skipped_scenarios}
    dropout_records = {
        name
        for name, rec in by_name.items()
        if rec.reason_code == "unaccounted_dropout"
    }
    assert dropout_records == expected_dropouts, (
        f"{vector_id}: dropouts differ; "
        f"expected={sorted(expected_dropouts)}, got={sorted(dropout_records)}"
    )

    accounted = (
        set(report.scenarios_run)
        | set(report.failed_scenarios)
        | {record.name for record in report.skipped_scenarios}
    )
    assert set(requested) == accounted, (
        f"{vector_id}: conservation invariant broken; "
        f"requested={sorted(set(requested))}, accounted={sorted(accounted)}"
    )


def test_scenario_dropout_repro_idempotent_on_second_record_call() -> None:
    """W14-1: a second ``record_execution_result`` with the same dropout state
    MUST NOT double-append ``unaccounted_dropout`` records.

    Idempotency is what keeps the conservation guard safe to call from both
    ``record_execution_result`` and ``finalize_running_scenarios``; without it
    a finalize-time second pass would re-append every previously-pinned
    dropout.
    """
    accountant, report = _build_accountant()
    report.scenario_traces = [
        ScenarioTrace(name="coding_session", started_at=0.0, status="completed")
    ]
    payload = _ExecResult(
        requested_scenarios=["coding_session", "missing_scenario"],
        skipped_scenarios=[],
        extra_trigger_failures=[],
        failed_scenarios=[],
    )

    accountant.record_execution_result(payload)
    first_pass = [(r.name, r.reason_code) for r in report.skipped_scenarios]
    accountant.record_execution_result(payload)
    second_pass = [(r.name, r.reason_code) for r in report.skipped_scenarios]

    assert first_pass == [("missing_scenario", "unaccounted_dropout")]
    assert first_pass == second_pass


def test_scenario_dropout_repro_finalize_running_also_runs_conservation() -> None:
    """W14-1: ``finalize_running_scenarios`` MUST invoke the conservation
    guard so a scenario requested before the executor crashed (and therefore
    never reaching ``record_execution_result``) still surfaces as a dropout.

    This pins the W7 §10.7 invariant for the close-of-monitoring path: if the
    runner exits mid-flight, ``ExtensionMonitor.stop()`` calls
    ``finalize_running_scenarios`` and the conservation guard catches the
    missing scenarios.
    """
    accountant, report = _build_accountant()
    report.requested_scenarios = ["coding_session", "debug_session"]
    accountant.record_scenario_event("start", "coding_session")
    accountant.record_scenario_event(
        "end", "coding_session", status="completed", metadata=None
    )
    report.monitoring_end = 5.0

    accountant.finalize_running_scenarios()

    skipped_by_name = {r.name: r for r in report.skipped_scenarios}
    assert "debug_session" in skipped_by_name
    assert skipped_by_name["debug_session"].reason_code == "unaccounted_dropout"


# ---------------------------------------------------------------------------
# W16-1 upstream emit-site instrumentation pin
# ---------------------------------------------------------------------------


def test_dispatch_outcome_none_emits_specific_reason_code() -> None:
    """W16-1: ``_normalize_execution_result`` MUST emit a specific
    ``dispatch_outcome_none`` reason for every requested scenario when the
    stimulus dispatcher returns ``None``.

    Pre-W16-1, the outcome=None branch built an empty
    ``AutomationExecutionResult`` with no ``skipped_scenarios`` entries; the
    downstream ``ScenarioAccountant._validate_scenario_conservation`` last-mile
    guard then back-filled each missing scenario with the generic
    ``unaccounted_dropout`` reason. That is what ``vec_stimulus_collapse``
    above pins at the accountant boundary. W16-1 closes the upstream half of
    the bug class so the dispatch normalizer itself records *why* the
    scenarios disappeared — production observers see ``dispatch_outcome_none``
    in ``skipped_scenarios`` rather than a downstream-only fallback.

    Production motivation: ``debug_session`` + ``refactor_workflow``
    deterministic dropouts observed in ``activation_report_*.json`` on
    2026-05-14 + 2026-05-15. See W14-1 / W16-1 trackers.
    """
    from executor.flows.playwright import stimulus as stimulus_module
    from executor.flows.playwright.entrypoint.dispatch import (
        _normalize_execution_result,
    )

    class _StubDeps:
        stimulus = stimulus_module

    deps = _StubDeps()
    requested = ["debug_session", "refactor_workflow", "coding_session"]

    result = _normalize_execution_result(
        None, deps=deps, requested_scenarios=requested
    )

    assert list(result.requested_scenarios) == requested
    assert list(result.executed_scenarios) == []
    assert list(result.failed_scenarios) == []
    assert list(result.extra_trigger_failures) == []

    skip_by_name = {item.name: item for item in result.skipped_scenarios}
    assert set(skip_by_name) == set(requested), (
        f"every requested scenario must surface; expected={sorted(requested)}, "
        f"got={sorted(skip_by_name)}"
    )
    for name in requested:
        assert skip_by_name[name].reason_code == "dispatch_outcome_none", (
            f"{name}: expected dispatch_outcome_none, got "
            f"{skip_by_name[name].reason_code!r}"
        )
        assert skip_by_name[name].detail, (
            f"{name}: detail must be populated for analyst readability"
        )


def test_dispatch_outcome_none_emits_nothing_when_no_requested_scenarios() -> None:
    """W16-1: with an empty ``requested_scenarios`` the normalizer's outcome=None
    branch MUST still return cleanly and MUST NOT fabricate phantom entries.

    Edge case for ``--skip-automation`` / demo / empty-payload modes that pass
    an empty list to the normalizer. The upstream instrumentation MUST behave
    as a no-op for those modes — fabricating a synthetic skip record for a
    scenario that was never requested would itself be a conservation violation.
    """
    from executor.flows.playwright import stimulus as stimulus_module
    from executor.flows.playwright.entrypoint.dispatch import (
        _normalize_execution_result,
    )

    class _StubDeps:
        stimulus = stimulus_module

    result = _normalize_execution_result(
        None, deps=_StubDeps(), requested_scenarios=[]
    )

    assert list(result.requested_scenarios) == []
    assert list(result.skipped_scenarios) == []
    assert list(result.executed_scenarios) == []
    assert list(result.failed_scenarios) == []
