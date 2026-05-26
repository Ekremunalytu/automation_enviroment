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
from typing import Any, ClassVar

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

    result = _normalize_execution_result(None, deps=deps, requested_scenarios=requested)

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

    result = _normalize_execution_result(None, deps=_StubDeps(), requested_scenarios=[])

    assert list(result.requested_scenarios) == []
    assert list(result.skipped_scenarios) == []
    assert list(result.executed_scenarios) == []
    assert list(result.failed_scenarios) == []


# ---------------------------------------------------------------------------
# W19-2 upstream emit-site instrumentation pin
# ---------------------------------------------------------------------------


def test_layered_attempts_coverage_emits_specific_reason_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """W19-2: ``run_stimulus_plan`` MUST emit a specific
    ``covered_via_layered_attempts`` reason for every scenario whose
    declared activation events were attempted through the layered plan
    (i.e. ``_record_scenario_coverage`` added them to
    ``covered_scenarios``) but whose handler was NOT directly invoked
    under this execution mode (``executor_action`` is ``extra:`` /
    ``command:`` / etc. — anything other than ``scenario:`` which would
    route through ``attempts._emit_scenario_with_optional_coverage``
    and append to ``result.executed_scenarios``).

    Pre-W19-2, ``passes.py`` unioned ``executed_scenarios`` U
    ``covered_scenarios`` into a single ``executed_names`` skip-set;
    covered-only scenarios were excluded from the reconciliation loop
    entirely, so they appeared in neither ``scenarios_run`` (the
    accountant re-derives that from ``scenario_traces``, which records
    handler invocations only) nor ``skipped_scenarios``. The last-mile
    ``ScenarioAccountant._validate_scenario_conservation`` guard then
    back-filled each missing scenario with the generic
    ``unaccounted_dropout`` reason. ``vec_ms_python_python`` above
    pins that downstream-fallback shape at the accountant boundary;
    this test pins the W19-2 upstream-classification fix directly so
    production observers see ``covered_via_layered_attempts`` in
    ``skipped_scenarios`` rather than a downstream-only fallback.

    Production motivation: ``debug_session`` + ``refactor_workflow``
    deterministic dropouts observed in live analyze API runs against
    ``ms-python.python`` (Codex live-run reference 2026-05-21 @
    ``992ad028f3df``; three byte-identical post-W18-2 confirmations).
    See W19 tracker and §17 W19 plan.
    """
    from executor.flows.playwright.stimulus import passes as passes_module

    # Stub execute_attempt to a no-op so the test does not need a
    # real Playwright Page. The function is bound into the
    # passes module namespace via `from .attempts import ...`,
    # so setattr on passes_module rebinds the local name.
    def _stub_execute_attempt(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(passes_module, "execute_attempt", _stub_execute_attempt)

    class _Payload:
        # Three requested scenarios; the first two have layered
        # attempts wired in below (covered-only), the third has no
        # attempt at all (must hit the existing not_executed branch
        # so the test simultaneously pins that branch as a guard
        # against accidental reason_code drift).
        selected_scenarios: ClassVar[list[str]] = [
            "debug_session",
            "refactor_workflow",
            "coding_session",
        ]
        event_attempts: ClassVar[list[dict[str, Any]]] = [
            {
                "attempt_id": "att-debug-1",
                "executor_action": "extra:debug_lifecycle",
                "event_family": "onDebugInitialConfigurations",
                "legacy_scenarios": ["debug_session"],
            },
            {
                "attempt_id": "att-refactor-1",
                "executor_action": "command:auto",
                "event_family": "onCommand",
                "legacy_scenarios": ["refactor_workflow"],
            },
        ]
        stimulus_passes: ClassVar[list[dict[str, Any]]] = [
            {
                "pass_id": "ui_first_user_session",
                "order": 1,
                "label": "UI first user session",
                "attempt_ids": ["att-debug-1", "att-refactor-1"],
                "prerequisite_keys": [],
            },
        ]
        prerequisite_results: ClassVar[list[dict[str, Any]]] = []

    result = passes_module.run_stimulus_plan(
        page=None, payload=_Payload(), monitor=None
    )

    assert list(result.requested_scenarios) == [
        "debug_session",
        "refactor_workflow",
        "coding_session",
    ]
    # No handler was directly invoked under this execution mode.
    assert list(result.executed_scenarios) == []
    assert list(result.failed_scenarios) == []

    skip_by_name = {item.name: item for item in result.skipped_scenarios}
    assert set(skip_by_name) == {
        "debug_session",
        "refactor_workflow",
        "coding_session",
    }, f"every requested scenario must surface; got={sorted(skip_by_name)}"

    for name in ("debug_session", "refactor_workflow"):
        assert skip_by_name[name].reason_code == "covered_via_layered_attempts", (
            f"{name}: expected covered_via_layered_attempts, got "
            f"{skip_by_name[name].reason_code!r}"
        )
        assert skip_by_name[name].detail, (
            f"{name}: detail must be populated for analyst readability"
        )

    # The third scenario had no attempt wired in — it must still hit
    # the existing not_executed branch so the W19-2 fix does not
    # accidentally regress healthy classification.
    assert skip_by_name["coding_session"].reason_code == "not_executed", (
        f"coding_session: expected not_executed (guard), got "
        f"{skip_by_name['coding_session'].reason_code!r}"
    )


def test_layered_attempts_coverage_pre_recorded_reason_wins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """W19-2: when an upstream attempt for a covered-only scenario
    recorded a specific reason via ``_record_scenario_reason``
    (e.g. ``unsupported_activation_surface``) before a later attempt
    in the same plan added the scenario to ``covered_scenarios``, the
    reconciliation MUST preserve that earlier reason rather than
    overwriting it with the generic ``covered_via_layered_attempts``
    default emitted by W19-2.

    Guards the ``scenario_reasons.get(scenario_name, (...))`` default
    semantics in the new covered_only branch: the default is a
    fallback, not a replacement. ``_record_scenario_reason`` is
    first-write-wins (line 316-317), so an early unsupported-surface
    attempt locks in the reason; a later successful attempt still
    adds the scenario to ``covered_scenarios`` (so the covered_only
    branch is exercised) but the dict-default lookup MUST yield the
    earlier reason.
    """
    from executor.flows.playwright.stimulus import passes as passes_module

    def _stub_execute_attempt(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(passes_module, "execute_attempt", _stub_execute_attempt)

    class _Payload:
        selected_scenarios: ClassVar[list[str]] = ["debug_session"]
        event_attempts: ClassVar[list[dict[str, Any]]] = [
            {
                # Attempt 1: unsupported event family → records
                # 'unsupported_activation_surface' for debug_session
                # via ``_record_scenario_reason`` (first-write-wins).
                "attempt_id": "att-unsupported",
                "executor_action": "extra:debug_lifecycle",
                "event_family": "onSomethingUnsupportedByExecutor",
                "legacy_scenarios": ["debug_session"],
            },
            {
                # Attempt 2: supported family + non-scenario action →
                # ``execute_attempt`` runs (no-op stubbed) →
                # ``_record_scenario_coverage`` adds debug_session
                # to ``covered_scenarios`` so the covered_only branch
                # fires in reconciliation.
                "attempt_id": "att-covered",
                "executor_action": "extra:debug_lifecycle",
                "event_family": "onDebugInitialConfigurations",
                "legacy_scenarios": ["debug_session"],
            },
        ]
        stimulus_passes: ClassVar[list[dict[str, Any]]] = [
            {
                "pass_id": "ui_first_user_session",
                "order": 1,
                "label": "UI first user session",
                "attempt_ids": ["att-unsupported", "att-covered"],
                "prerequisite_keys": [],
            },
        ]
        prerequisite_results: ClassVar[list[dict[str, Any]]] = []

    result = passes_module.run_stimulus_plan(
        page=None, payload=_Payload(), monitor=None
    )

    skip_by_name = {item.name: item for item in result.skipped_scenarios}
    assert "debug_session" in skip_by_name
    # Pre-recorded reason MUST win over the W19-2 covered_only default.
    assert (
        skip_by_name["debug_session"].reason_code == "unsupported_activation_surface"
    ), (
        "covered_only branch must respect prior scenario_reasons entry; got "
        f"{skip_by_name['debug_session'].reason_code!r}"
    )
