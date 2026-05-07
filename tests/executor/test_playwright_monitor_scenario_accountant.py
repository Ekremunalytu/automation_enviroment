"""Direct unit tests for ``ScenarioAccountant`` (W11-4).

These tests pin the scenario / event-attempt accounting collaborator
extracted from ``ExtensionMonitor`` in W11-4. They import at the real
module path
(``executor.flows.playwright.monitor_scenario_accountant``)
rather than through the ``monitor`` facade so that the W12 directory
reshuffle cannot silently regress this surface.

Cross-module callbacks (``record_automation_event``, ``persist``) are
stubbed with simple recorders so each test asserts that the accountant
calls the right collaborator at the right point in the lifecycle.
``emit_intermediate_state_events`` (the W11-4 producer signal) is
exercised against a real ``ActivationReport`` whose
``event_attempts[*].verification_status`` has been hand-set to the
post-reconcile literal — the test does not re-exercise
``reconcile_event_attempts`` (that has its own test module).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from executor.flows.playwright.monitor_records import (
    EventAttemptRecord,
    LogStreamEntry,
    ScenarioTrace,
    SkippedScenarioRecord,
)
from executor.flows.playwright.monitor_scenario_accountant import ScenarioAccountant
from executor.flows.playwright.monitor_types import ActivationReport
from executor.flows.playwright.runtime_capture.events import ActivationEntry


class _Recorder:
    """Bundle of accountant callbacks with call recorders."""

    def __init__(self) -> None:
        self.persist_calls: list[bool] = []
        self.automation_events: list[tuple[str, str, dict[str, Any]]] = []

    def persist(self, force: bool) -> None:
        self.persist_calls.append(force)

    def record_automation_event(
        self,
        kind: str,
        message: str,
        status: str = "",
        scenario_name: str = "",
        activation_event: str = "",
    ) -> None:
        self.automation_events.append(
            (
                kind,
                message,
                {
                    "status": status,
                    "scenario_name": scenario_name,
                    "activation_event": activation_event,
                },
            )
        )


def _build_accountant(
    *,
    target_extension_id: str = "publisher.tool",
) -> tuple[ScenarioAccountant, ActivationReport, _Recorder]:
    report = ActivationReport(target_extension_id=target_extension_id)
    rec = _Recorder()
    accountant = ScenarioAccountant(
        report=report,
        record_automation_event=rec.record_automation_event,
        persist=rec.persist,
    )
    return accountant, report, rec


# ---------------------------------------------------------------------------
# Init invariants
# ---------------------------------------------------------------------------


def test_init_holds_report_by_reference() -> None:
    accountant, report, _rec = _build_accountant()
    assert accountant._report is report


def test_init_starts_with_empty_active_scenarios_dict() -> None:
    accountant, _report, _rec = _build_accountant()
    assert accountant._active_scenarios == {}


def test_init_starts_with_empty_emitted_intermediate_attempts_set() -> None:
    accountant, _report, _rec = _build_accountant()
    assert accountant._emitted_intermediate_state_attempts == set()


# ---------------------------------------------------------------------------
# Trigger-plan + execution-result intake
# ---------------------------------------------------------------------------


def test_mark_trigger_plan_applied_sets_flag_and_persists() -> None:
    accountant, report, rec = _build_accountant()

    accountant.mark_trigger_plan_applied(
        scenarios=["scenario_a", "scenario_b"],
        trigger_path="/tmp/trigger.json",  # noqa: S108 — never opened, just shape pin
    )

    assert report.trigger_plan_applied is True
    assert report.requested_scenarios == ["scenario_a", "scenario_b"]
    assert report.trigger_plan_path == "/tmp/trigger.json"  # noqa: S108
    assert rec.persist_calls == [False]


def test_mark_trigger_plan_applied_without_scenarios_keeps_existing_list() -> None:
    accountant, report, _rec = _build_accountant()
    report.requested_scenarios = ["pre_existing"]

    accountant.mark_trigger_plan_applied()

    # Empty/None scenarios list leaves the existing requested_scenarios
    # alone; only an explicit non-empty list overwrites.
    assert report.requested_scenarios == ["pre_existing"]


def test_mark_trigger_plan_missing_marks_requested_but_not_loaded() -> None:
    accountant, report, rec = _build_accountant()

    accountant.mark_trigger_plan_missing("/tmp/missing.json")  # noqa: S108

    assert report.trigger_plan_requested is True
    assert report.trigger_plan_loaded is False
    assert report.trigger_plan_path == "/tmp/missing.json"  # noqa: S108
    assert rec.persist_calls == [False]


def test_record_failed_scenarios_synchronizes_from_scenario_traces() -> None:
    """``record_failed_scenarios`` first writes the deduped+sorted input,
    then re-derives from ``scenario_traces`` via
    ``_synchronize_scenario_truth``. The trace-driven derivation is the
    final truth, so a call with no matching traces yields ``[]`` while a
    call backed by traces yields the trace-name list. This pins the
    behavior preserved bit-for-bit from the pre-W11-4 lifecycle."""

    accountant, report, _rec = _build_accountant()
    report.scenario_traces = [
        ScenarioTrace(name="a", started_at=0.0, status="failed"),
        ScenarioTrace(name="b", started_at=0.0, status="failed"),
        ScenarioTrace(name="c", started_at=0.0, status="completed"),
    ]

    accountant.record_failed_scenarios(["b", "a", "b", "c", "a"])

    # Synchronization pulls the two traces with status=="failed";
    # whatever the caller passed (dedupes-and-sorts to ["a", "b", "c"])
    # is overwritten because the truth lives on traces.
    assert report.failed_scenarios == ["a", "b"]


def test_record_failed_scenarios_with_no_traces_ends_up_empty() -> None:
    """Pin the fall-out of the trace-driven sync semantics: a call
    without any backing ``scenario_traces`` lands as ``[]``, not as
    the deduped+sorted input. Catches drift if a future change
    short-circuits ``_synchronize_scenario_truth`` here."""

    accountant, report, _rec = _build_accountant()

    accountant.record_failed_scenarios(["a", "b"])

    assert report.failed_scenarios == []


def test_record_execution_result_pulls_all_four_lists() -> None:
    @dataclass
    class _Skip:
        name: str
        reason_code: str
        detail: str

    @dataclass
    class _ExecResult:
        requested_scenarios: list[str]
        skipped_scenarios: list[_Skip]
        extra_trigger_failures: list[str]
        failed_scenarios: list[str]

    result = _ExecResult(
        requested_scenarios=["s1", "  ", "s2"],
        skipped_scenarios=[
            _Skip(name="s3", reason_code="precondition_unmet", detail=""),
            _Skip(name="", reason_code="ignored", detail=""),  # filtered (no name)
            _Skip(name="s4", reason_code="", detail=""),  # filtered (no reason_code)
        ],
        extra_trigger_failures=["lock_busy", ""],
        failed_scenarios=["s1"],
    )

    accountant, report, _rec = _build_accountant()
    accountant.record_execution_result(result)

    assert report.requested_scenarios == ["s1", "s2"]
    # The (name, reason_code)-complete skip from the input survives the
    # filter; the conservation guard then appends ``s1`` and ``s2`` as
    # ``unaccounted_dropout`` records because they are in
    # ``requested_scenarios`` but missing from ``scenarios_run`` (no
    # traces) and ``failed_scenarios`` (re-derived to ``[]`` here). The
    # conservation behavior is pinned in dedicated tests below; this
    # assertion shape only documents the post-condition shape.
    assert len(report.skipped_scenarios) == 3
    assert all(
        isinstance(record, SkippedScenarioRecord) for record in report.skipped_scenarios
    )
    by_name = {record.name: record for record in report.skipped_scenarios}
    assert by_name["s3"].reason_code == "precondition_unmet"
    assert by_name["s1"].reason_code == "unaccounted_dropout"
    assert by_name["s2"].reason_code == "unaccounted_dropout"
    assert report.extra_trigger_failures == ["lock_busy"]
    # Note: ``failed_scenarios`` is re-derived from ``scenario_traces``
    # by ``_synchronize_scenario_truth``; with no traces in this fixture
    # the list ends up empty even though the result reported "s1" as
    # failed. Pinned by ``test_record_failed_scenarios_with_no_traces…``
    # above; this assertion stays loose to that contract.
    assert report.failed_scenarios == []


# ---------------------------------------------------------------------------
# Scenario-dropout honesty (W7 §10.7 conservation invariant)
# ---------------------------------------------------------------------------


def _make_exec_result(
    *,
    requested: list[str],
    skipped: list[tuple[str, str, str]] | None = None,
    failed: list[str] | None = None,
) -> Any:
    """Shape-only stand-in for ``AutomationExecutionResult``.

    Only carries the four fields ``record_execution_result`` reads;
    keeping it inline avoids importing the executor's runtime dataclass
    just for shape replication.
    """

    @dataclass
    class _Skip:
        name: str
        reason_code: str
        detail: str

    @dataclass
    class _ExecResult:
        requested_scenarios: list[str]
        skipped_scenarios: list[_Skip]
        extra_trigger_failures: list[str]
        failed_scenarios: list[str]

    return _ExecResult(
        requested_scenarios=list(requested),
        skipped_scenarios=[_Skip(*entry) for entry in skipped or []],
        extra_trigger_failures=[],
        failed_scenarios=list(failed or []),
    )


def test_record_execution_result_appends_unaccounted_dropouts_as_skipped() -> None:
    """Reproduces the live ms-python.python regression: 5 requested,
    3 ran, 0 explicitly skipped/failed → 2 silent dropouts. The
    conservation guard must surface the 2 missing scenarios as
    ``skipped_scenarios`` records with reason ``unaccounted_dropout``
    so the W7 §10.7 honesty invariant holds end-to-end.
    """
    accountant, report, _rec = _build_accountant()
    report.scenario_traces = [
        ScenarioTrace(name="coding_session", started_at=0.0, status="completed"),
        ScenarioTrace(name="project_exploration", started_at=0.0, status="completed"),
        ScenarioTrace(name="terminal_usage", started_at=0.0, status="completed"),
    ]

    accountant.record_execution_result(
        _make_exec_result(
            requested=[
                "coding_session",
                "project_exploration",
                "debug_session",
                "terminal_usage",
                "refactor_workflow",
            ],
        )
    )

    by_name = {record.name: record for record in report.skipped_scenarios}
    assert set(by_name) == {"debug_session", "refactor_workflow"}
    assert by_name["debug_session"].reason_code == "unaccounted_dropout"
    assert by_name["refactor_workflow"].reason_code == "unaccounted_dropout"
    # Conservation invariant: every requested scenario lands in exactly
    # one of the three accounting buckets.
    accounted = (
        set(report.scenarios_run)
        | set(report.failed_scenarios)
        | {record.name for record in report.skipped_scenarios}
    )
    assert set(report.requested_scenarios) == accounted


def test_record_execution_result_conservation_no_op_when_all_accounted() -> None:
    """If every requested scenario is already in run/failed/skipped, the
    conservation guard must not append synthetic records — happy-path
    no-op so a healthy run stays clean.
    """
    accountant, report, _rec = _build_accountant()
    report.scenario_traces = [
        ScenarioTrace(name="coding_session", started_at=0.0, status="completed"),
    ]

    accountant.record_execution_result(
        _make_exec_result(
            requested=["coding_session", "debug_session"],
            skipped=[("debug_session", "precondition_unmet", "no debug capability")],
        )
    )

    assert len(report.skipped_scenarios) == 1
    assert report.skipped_scenarios[0].name == "debug_session"
    assert report.skipped_scenarios[0].reason_code == "precondition_unmet"


def test_record_execution_result_conservation_is_idempotent() -> None:
    """Two consecutive ``record_execution_result`` calls with the same
    dropout state must not double-append ``unaccounted_dropout`` records
    — the second call sees the missing scenarios already in
    ``skipped_scenarios`` (they fold into ``accounted``) and writes
    nothing further.
    """
    accountant, report, _rec = _build_accountant()
    report.scenario_traces = [
        ScenarioTrace(name="coding_session", started_at=0.0, status="completed"),
    ]
    payload = _make_exec_result(
        requested=["coding_session", "debug_session"],
    )

    accountant.record_execution_result(payload)
    first_pass = len(report.skipped_scenarios)
    accountant.record_execution_result(payload)
    second_pass = len(report.skipped_scenarios)

    assert first_pass == 1
    assert second_pass == 1
    assert report.skipped_scenarios[0].name == "debug_session"
    assert report.skipped_scenarios[0].reason_code == "unaccounted_dropout"


def test_finalize_running_scenarios_invokes_conservation_guard() -> None:
    """Conservation must fire from ``finalize_running_scenarios`` too —
    that is the canonical close-of-monitoring hook. If a scenario was
    requested but never reached ``record_execution_result`` (e.g., the
    executor crashed mid-run), the finalize-time guard still surfaces
    it as ``unaccounted_dropout``.
    """
    accountant, report, _rec = _build_accountant()
    report.requested_scenarios = ["coding_session", "debug_session"]
    accountant.record_scenario_event("start", "coding_session")
    accountant.record_scenario_event("end", "coding_session", status="completed")
    report.monitoring_end = 5.0

    accountant.finalize_running_scenarios()

    by_name = {record.name: record for record in report.skipped_scenarios}
    assert "debug_session" in by_name
    assert by_name["debug_session"].reason_code == "unaccounted_dropout"


# ---------------------------------------------------------------------------
# Event-attempt mutations
# ---------------------------------------------------------------------------


def _seed_attempt(
    report: ActivationReport, attempt_id: str = "a1", **overrides: Any
) -> EventAttemptRecord:
    base: dict[str, Any] = {
        "attempt_id": attempt_id,
        "declared_event": "onCommand:do",
        "activation_event": "onCommand:do",
        "event_family": "onCommand",
    }
    base.update(overrides)
    attempt = EventAttemptRecord(**base)
    report.event_attempts.append(attempt)
    return attempt


def test_record_event_attempt_start_marks_running_and_records_event() -> None:
    accountant, report, rec = _build_accountant()
    _seed_attempt(report)

    accountant.record_event_attempt_start("a1", pass_name="bootstrap")  # noqa: S106 — stimulus pass id, not a password

    assert report.event_attempts[0].status == "running"
    assert report.event_attempts[0].attempted_passes == ["bootstrap"]
    kinds = [k for k, _msg, _meta in rec.automation_events]
    assert kinds == ["event_attempt"]
    assert rec.automation_events[0][2]["status"] == "running"


def test_record_event_attempt_start_no_op_for_unknown_id() -> None:
    accountant, report, rec = _build_accountant()
    _seed_attempt(report)

    accountant.record_event_attempt_start("missing")

    assert report.event_attempts[0].status == "planned"
    assert rec.automation_events == []


def test_record_event_attempt_end_failed_drives_verification_status_to_failed() -> None:
    """W11-3-era contract pin: producer-reported failed runs straight to
    the terminal ``verification_status="failed"``. W11-4 *intentionally*
    preserves this mapping — the upgrade-past-failed/blocked work is
    layered on top via ``emit_intermediate_state_events`` (post-
    reconcile vocabulary), not by demoting failed status here."""

    accountant, report, _rec = _build_accountant()
    _seed_attempt(report)

    accountant.record_event_attempt_end(
        "a1",
        status="failed",
        failure_reason_code="trigger_failure",
    )

    assert report.event_attempts[0].status == "failed"
    assert report.event_attempts[0].verification_status == "failed"
    assert report.event_attempts[0].failure_reason_code == "trigger_failure"


def test_record_event_attempt_end_blocked_drives_verification_status_to_blocked() -> (
    None
):
    accountant, report, _rec = _build_accountant()
    _seed_attempt(report)

    accountant.record_event_attempt_end(
        "a1",
        status="blocked",
        blocked_reason_code="ui_blocker_dialog",
    )

    assert report.event_attempts[0].status == "blocked"
    assert report.event_attempts[0].verification_status == "blocked"
    assert report.event_attempts[0].blocked_reason_code == "ui_blocker_dialog"


def test_record_event_attempt_end_verified_promotes_to_verified() -> None:
    accountant, report, _rec = _build_accountant()
    _seed_attempt(report)

    accountant.record_event_attempt_end("a1", status="verified")

    assert report.event_attempts[0].status == "verified"
    assert report.event_attempts[0].verification_status == "verified"


def test_record_event_attempt_end_no_op_for_unknown_id() -> None:
    accountant, report, rec = _build_accountant()
    _seed_attempt(report)

    accountant.record_event_attempt_end("missing", status="failed")

    assert report.event_attempts[0].status == "planned"
    assert rec.automation_events == []


# ---------------------------------------------------------------------------
# Scenario lifecycle
# ---------------------------------------------------------------------------


def test_record_scenario_event_start_then_end_pairs_a_single_trace() -> None:
    accountant, report, _rec = _build_accountant()

    accountant.record_scenario_event("start", "explore")
    accountant.record_scenario_event("end", "explore", "completed")

    assert len(report.scenario_traces) == 1
    trace = report.scenario_traces[0]
    assert isinstance(trace, ScenarioTrace)
    assert trace.name == "explore"
    assert trace.status == "completed"
    assert trace.ended_at >= trace.started_at
    assert accountant._active_scenarios == {}


def test_record_scenario_event_failed_carries_reason_and_truncates_error() -> None:
    accountant, report, _rec = _build_accountant()

    accountant.record_scenario_event("start", "crashing")
    accountant.record_scenario_event(
        "end",
        "crashing",
        "failed",
        metadata={"failure_reason_code": "fatal_ui_crash", "error": "x" * 1200},
    )

    trace = report.scenario_traces[0]
    assert trace.status == "failed"
    assert trace.failure_reason_code == "fatal_ui_crash"
    assert len(trace.error_detail) == 500
    # Synchronization derived `failed_scenarios` from the trace.
    assert report.failed_scenarios == ["crashing"]


def test_record_scenario_event_unstarted_end_creates_a_trace() -> None:
    """End-without-start is tolerated: a trace is created so the scenario
    still shows up in `scenarios_run`. Pin the lenient producer behavior
    so callers (e.g. the runner that recovers from a crashed scenario)
    do not silently drop the post-mortem trace."""

    accountant, report, _rec = _build_accountant()

    accountant.record_scenario_event("end", "orphan", "completed")

    assert [trace.name for trace in report.scenario_traces] == ["orphan"]
    assert report.scenarios_run == ["orphan"]


def test_record_scenario_event_appends_log_stream_entry_with_scenario_name() -> None:
    accountant, report, _rec = _build_accountant()

    accountant.record_scenario_event("start", "explore")

    automation_entries = [
        entry for entry in report.log_entries if entry.stream == "automation"
    ]
    assert len(automation_entries) == 1
    entry = automation_entries[0]
    assert isinstance(entry, LogStreamEntry)
    assert entry.kind == "scenario"
    assert entry.scenario_name == "explore"
    assert entry.status == "running"


def test_finalize_running_scenarios_completes_open_traces() -> None:
    accountant, report, _rec = _build_accountant()
    accountant.record_scenario_event("start", "still_running")
    report.monitoring_end = report.scenario_traces[0].started_at + 5.0

    accountant.finalize_running_scenarios()

    trace = report.scenario_traces[0]
    assert trace.status == "completed"
    assert trace.ended_at == report.monitoring_end
    assert accountant._active_scenarios == {}
    # Idempotent — second call must not mutate further.
    accountant.finalize_running_scenarios()
    assert accountant._active_scenarios == {}


def test_synchronize_scenario_truth_derives_run_and_failed_lists() -> None:
    accountant, report, _rec = _build_accountant()
    report.scenario_traces = [
        ScenarioTrace(name="s1", started_at=0.0, status="completed"),
        ScenarioTrace(name="s2", started_at=0.0, status="failed"),
        ScenarioTrace(
            name=" ", started_at=0.0, status="failed"
        ),  # filtered (whitespace)
    ]

    accountant._synchronize_scenario_truth()

    assert report.scenarios_run == ["s1", "s2"]
    assert report.failed_scenarios == ["s2"]


# ---------------------------------------------------------------------------
# Activation-window log derivation
# ---------------------------------------------------------------------------


def test_append_activation_log_entries_mirrors_target_to_target_stream() -> None:
    accountant, report, _rec = _build_accountant()
    report.monitoring_start = 0.0
    report.activated.append(
        ActivationEntry(
            extension_id="publisher.tool",
            activation_event="onCommand:run",
            timestamp="2026-01-01 10:00:00.500",
            source="log",
            success=True,
        )
    )

    accountant.append_activation_log_entries()

    # Exactly one new log entry in the target_extension_host stream.
    target_entries = [
        entry for entry in report.log_entries if entry.stream == "target_extension_host"
    ]
    assert len(target_entries) == 1
    assert target_entries[0].extension_id == "publisher.tool"
    assert target_entries[0].is_target_extension is True
    assert target_entries[0].activation_event == "onCommand:run"


def test_append_activation_log_entries_routes_non_target_to_other_stream() -> None:
    accountant, report, _rec = _build_accountant()
    report.monitoring_start = 0.0
    report.activated.append(
        ActivationEntry(
            extension_id="other.publisher",
            activation_event="onStartupFinished",
            timestamp="2026-01-01 10:00:00.100",
            source="log",
            success=True,
        )
    )

    accountant.append_activation_log_entries()

    other_entries = [
        entry for entry in report.log_entries if entry.stream == "other_extension_host"
    ]
    assert len(other_entries) == 1
    assert other_entries[0].is_target_extension is False


def test_append_activation_log_entries_is_idempotent() -> None:
    accountant, report, _rec = _build_accountant()
    report.monitoring_start = 0.0
    report.activated.append(
        ActivationEntry(
            extension_id="publisher.tool",
            activation_event="onCommand:run",
            timestamp="2026-01-01 10:00:00.500",
            source="log",
            success=True,
        )
    )

    accountant.append_activation_log_entries()
    first_count = len(report.log_entries)
    accountant.append_activation_log_entries()
    second_count = len(report.log_entries)

    assert first_count == second_count


# ---------------------------------------------------------------------------
# W11-4 producer signal: emit_intermediate_state_events
# ---------------------------------------------------------------------------


def test_emit_intermediate_state_events_emits_for_activation_seen() -> None:
    accountant, report, rec = _build_accountant()
    attempt = _seed_attempt(report)
    attempt.verification_status = "activation_seen"

    accountant.emit_intermediate_state_events()

    kinds = [k for k, _msg, _meta in rec.automation_events]
    assert kinds == ["event_attempt"]
    assert rec.automation_events[0][2]["status"] == "activation_seen"
    assert "Target activation observed" in rec.automation_events[0][1]


def test_emit_intermediate_state_events_emits_for_target_log_seen() -> None:
    accountant, report, rec = _build_accountant()
    attempt = _seed_attempt(report)
    attempt.verification_status = "target_log_seen"

    accountant.emit_intermediate_state_events()

    kinds = [k for k, _msg, _meta in rec.automation_events]
    assert kinds == ["event_attempt"]
    assert rec.automation_events[0][2]["status"] == "target_log_seen"
    assert "target-owned log evidence" in rec.automation_events[0][1]


def test_emit_intermediate_state_events_skips_terminal_states() -> None:
    """Verified / failed / blocked / attempted_only attempts must NOT
    emit an intermediate-state event — those have their own producer
    code path (``record_event_attempt_end``) and double-emitting would
    pollute the timeline."""

    accountant, report, rec = _build_accountant()
    for index, status in enumerate(
        ["verified", "failed", "blocked", "attempted_only", "not_attempted"]
    ):
        attempt = _seed_attempt(report, attempt_id=f"a{index}")
        attempt.verification_status = status

    accountant.emit_intermediate_state_events()

    assert rec.automation_events == []


def test_emit_intermediate_state_events_is_idempotent_per_attempt() -> None:
    """Repeated invocations (e.g. a second ``stop()`` call in tests) must
    not double-log the same attempt."""

    accountant, report, rec = _build_accountant()
    attempt = _seed_attempt(report)
    attempt.verification_status = "activation_seen"

    accountant.emit_intermediate_state_events()
    accountant.emit_intermediate_state_events()
    accountant.emit_intermediate_state_events()

    assert len(rec.automation_events) == 1


def test_emit_intermediate_state_events_skips_attempts_with_blank_id() -> None:
    accountant, report, rec = _build_accountant()
    attempt = _seed_attempt(report, attempt_id="   ")
    attempt.verification_status = "activation_seen"

    accountant.emit_intermediate_state_events()

    assert rec.automation_events == []


def test_emit_intermediate_state_events_emits_per_promoted_attempt() -> None:
    accountant, report, rec = _build_accountant()
    a1 = _seed_attempt(report, attempt_id="a1")
    a1.verification_status = "activation_seen"
    a2 = _seed_attempt(report, attempt_id="a2")
    a2.verification_status = "target_log_seen"
    a3 = _seed_attempt(report, attempt_id="a3")
    a3.verification_status = "verified"  # filtered

    accountant.emit_intermediate_state_events()

    statuses = [meta["status"] for _k, _msg, meta in rec.automation_events]
    assert sorted(statuses) == ["activation_seen", "target_log_seen"]


def test_emit_intermediate_state_events_carries_activation_event_metadata() -> None:
    """Pin that the emission carries the source attempt's
    ``activation_event`` on the log entry's metadata, so downstream
    timeline filters can attribute the intermediate-state event to the
    same activation as the attempt itself."""

    accountant, report, rec = _build_accountant()
    attempt = _seed_attempt(report, attempt_id="a1")
    attempt.activation_event = "onCommand:python.run"
    attempt.verification_status = "activation_seen"

    accountant.emit_intermediate_state_events()

    assert len(rec.automation_events) == 1
    _kind, _msg, meta = rec.automation_events[0]
    assert meta["activation_event"] == "onCommand:python.run"


# ---------------------------------------------------------------------------
# W11-4 end-to-end: real reconciler -> emission chain
# ---------------------------------------------------------------------------


def test_emit_intermediate_state_events_fires_after_real_reconciliation() -> None:
    """End-to-end pin: drive the full producer signal chain through the
    real ``reconcile_event_attempts`` (rather than hand-setting
    ``verification_status``) and verify the automation timeline picks
    up the resulting promotion.

    Setup mirrors the reconciler's intermediate-state condition: the
    attempt declares a ``target_runtime_delta`` contract (so the
    reconciler refuses the no-contract / activation-only shortcut at
    line 336-347 and falls into the contract-driven branch), but has
    no ``attempted_passes`` + no ``capability_tags`` so
    ``runtime_capability_evidence`` stays empty and
    ``target_reaction_closed`` never flips True. The reconciler
    therefore skips ``_mark_attempt_verified``, drops to line 397,
    sees ``exact_matches`` non-empty, and promotes to
    ``activation_seen``. ``emit_intermediate_state_events`` then
    surfaces one automation log entry. This is the missing positive
    integration pin that the W11-3-baseline live scan run profile
    (with this target's trigger plan and capability evidence) does
    not exercise on its own.
    """

    from executor.flows.playwright.health_reconciliation import (
        reconcile_event_attempts,
    )

    accountant, report, rec = _build_accountant()
    report.activated.append(
        ActivationEntry(
            extension_id="publisher.tool",
            activation_event="onCommand:publisher.tool.run",
            timestamp="2026-01-01 10:00:00.500",
            source="log",
            success=True,
        )
    )
    attempt = _seed_attempt(
        report,
        attempt_id="a1",
        activation_event="onCommand:publisher.tool.run",
        event_family="onCommand",
    )
    # Force the contract-driven branch: target_runtime_delta declares
    # target_reaction_required without execution_required, but with
    # empty attempted_passes/capability_tags target_reaction_closed
    # stays False (line 371-377), so the attempt cannot reach
    # _mark_attempt_verified and instead falls into the
    # intermediate-state block at line 397.
    attempt.verification_contract = ["target_runtime_delta"]
    attempt.attempted_passes = []
    attempt.capability_tags = []

    reconcile_event_attempts(report)

    # Reconciler promoted the attempt to activation_seen.
    assert attempt.verification_status == "activation_seen"

    # No emission yet — accountant.emit_intermediate_state_events has
    # not been called. Rely on the runtime stop() ordering invariant
    # (refresh_derived_state -> emit_intermediate_state_events) for
    # the real chain.
    assert rec.automation_events == []

    accountant.emit_intermediate_state_events()

    assert len(rec.automation_events) == 1
    _kind, msg, meta = rec.automation_events[0]
    assert meta["status"] == "activation_seen"
    assert meta["activation_event"] == "onCommand:publisher.tool.run"
    assert "Target activation observed" in msg


# ---------------------------------------------------------------------------
# W11-5: stimulus passes + prerequisites (moved from ExtensionMonitor facade)
# ---------------------------------------------------------------------------


def test_record_stimulus_pass_event_start_creates_running_trace() -> None:
    accountant, report, rec = _build_accountant()

    accountant.record_stimulus_pass_event(
        "start",
        "p1",
        label="Pass One",
        order=1,
        trigger_method="command",
    )

    assert len(report.stimulus_passes) == 1
    trace = report.stimulus_passes[0]
    assert trace.pass_id == "p1"  # noqa: S105
    assert trace.label == "Pass One"
    assert trace.order == 1
    assert trace.status == "running"
    assert trace.trigger_method == "command"
    assert len(rec.automation_events) == 1
    kind, _msg, meta = rec.automation_events[0]
    assert kind == "stimulus_pass"
    assert meta["status"] == "running"


def test_record_stimulus_pass_event_end_updates_existing_trace() -> None:
    accountant, report, rec = _build_accountant()
    accountant.record_stimulus_pass_event("start", "p1", label="Pass", order=1)
    rec.automation_events.clear()

    accountant.record_stimulus_pass_event("end", "p1", status="completed")

    assert len(report.stimulus_passes) == 1
    trace = report.stimulus_passes[0]
    assert trace.status == "completed"
    assert trace.ended_at > 0.0
    assert len(rec.automation_events) == 1
    assert rec.automation_events[0][2]["status"] == "completed"


def test_record_stimulus_pass_event_end_without_prior_start_synthesizes_trace() -> None:
    accountant, report, rec = _build_accountant()

    accountant.record_stimulus_pass_event(
        "end",
        "ghost",
        label="Ghost Pass",
        status="failed",
        trigger_method="hotkey",
    )

    assert len(report.stimulus_passes) == 1
    trace = report.stimulus_passes[0]
    assert trace.pass_id == "ghost"  # noqa: S105
    assert trace.label == "Ghost Pass"
    assert trace.status == "failed"
    assert trace.trigger_method == "hotkey"
    assert trace.started_at == trace.ended_at
    assert len(rec.automation_events) == 1


def test_record_prerequisite_result_creates_record_and_emits_event() -> None:
    accountant, report, rec = _build_accountant()

    accountant.record_prerequisite_result(
        "ext.installed",
        status="completed",
        detail="ms-python.python is present",
        reason_code="ok",
        resolved_targets={"extension_id": "ms-python.python"},
    )

    assert len(report.prerequisite_results) == 1
    result = report.prerequisite_results[0]
    assert result.prerequisite_id == "ext.installed"
    assert result.status == "completed"
    assert result.detail == "ms-python.python is present"
    assert result.reason_code == "ok"
    assert result.resolved_targets == {"extension_id": "ms-python.python"}
    assert len(rec.automation_events) == 1
    assert rec.automation_events[0][0] == "prerequisite"
    assert rec.automation_events[0][2]["status"] == "completed"


def test_record_prerequisite_result_updates_existing_record() -> None:
    accountant, report, rec = _build_accountant()
    accountant.record_prerequisite_result("ext.installed", status="running")
    rec.automation_events.clear()

    accountant.record_prerequisite_result(
        "ext.installed",
        status="failed",
        reason_code="missing",
    )

    assert len(report.prerequisite_results) == 1
    result = report.prerequisite_results[0]
    assert result.status == "failed"
    assert result.reason_code == "missing"


# ---------------------------------------------------------------------------
# W11-5: verify_target_reaction (moved from ExtensionMonitor facade)
# ---------------------------------------------------------------------------


def _patch_target_log_count(monkeypatch, count: int) -> None:
    from executor.flows.playwright import monitor_scenario_accountant as accountant_mod

    monkeypatch.setattr(
        accountant_mod,
        "resolve_monitor_api",
        lambda: type(
            "Api",
            (),
            {"parse_all_exthost_logs": staticmethod(lambda **_: [])},
        )(),
    )
    monkeypatch.setattr(
        accountant_mod,
        "_count_target_activations",
        lambda _entries, _target: count,
    )


def test_verify_target_reaction_marks_capability_verified_when_activation_seen(
    monkeypatch,
) -> None:
    accountant, report, rec = _build_accountant()
    report.attempted_capabilities = ["network"]
    _patch_target_log_count(monkeypatch, count=1)

    verified = accountant.verify_target_reaction(
        {"target_activations": 0},
        {},
        capability="network",
        trigger_label="trigger.run",
    )

    assert verified is True
    assert "network" in report.verified_capabilities
    assert len(rec.automation_events) == 1
    assert rec.automation_events[0][0] == "command_verification"
    assert rec.automation_events[0][2]["status"] == "completed"


def test_verify_target_reaction_returns_false_when_no_evidence(monkeypatch) -> None:
    accountant, report, rec = _build_accountant()
    _patch_target_log_count(monkeypatch, count=0)

    verified = accountant.verify_target_reaction(
        {"target_activations": 0},
        {},
        capability="network",
        trigger_label="trigger.run",
    )

    assert verified is False
    assert report.verified_capabilities == []
    assert rec.automation_events[0][2]["status"] == "failed"


def test_verify_target_reaction_appends_ui_blocker_note_when_blocked_and_unverified(
    monkeypatch,
) -> None:
    accountant, report, _rec = _build_accountant()
    report.log_entries.append(
        LogStreamEntry(
            timestamp="",
            rel_time_s=0.0,
            stream="ui_blockers",
            kind="ui_blocker",
            message="modal blocked",
        )
    )
    _patch_target_log_count(monkeypatch, count=0)
    rec_capture: list[str] = []
    accountant._record_automation_event = (  # type: ignore[assignment]
        lambda kind, message, **_: rec_capture.append(message)
    )

    accountant.verify_target_reaction(
        {"ui_blockers": 0, "target_activations": 0},
        {},
        capability="network",
        trigger_label="trigger.run",
    )

    assert any("UI blocker" in m for m in rec_capture)


def test_verify_target_reaction_marks_heuristic_capability_when_attempted(
    monkeypatch,
) -> None:
    accountant, report, _rec = _build_accountant()
    report.heuristic_attempted_capabilities = ["fs"]
    _patch_target_log_count(monkeypatch, count=1)

    verified = accountant.verify_target_reaction(
        {"target_activations": 0},
        {},
        capability="fs",
        trigger_label="trigger.run",
    )

    assert verified is True
    assert "fs" in report.heuristic_verified_capabilities


def test_verify_target_reaction_returns_true_when_new_target_file_event_observed(
    monkeypatch,
) -> None:
    """W11-5: file/network activity post-baseline counts as verification
    even when the exthost log shows no fresh activation. Guards the
    ``new_activity`` branch of ``verify_target_reaction``."""
    from executor.flows.playwright.runtime_capture.events import FileEvent

    accountant, report, _rec = _build_accountant()
    report.attempted_capabilities = ["fs"]
    _patch_target_log_count(monkeypatch, count=0)
    report.file_events.append(
        FileEvent(
            path="/tmp/x",  # noqa: S108
            operation="created",
            related_extension_id="publisher.tool",
            is_target_extension_event=True,
        )
    )

    verified = accountant.verify_target_reaction(
        {"target_activations": 0, "target_file_events": 0},
        {},
        capability="fs",
        trigger_label="trigger.run",
    )

    assert verified is True
    assert "fs" in report.verified_capabilities


def test_record_stimulus_pass_event_start_of_existing_trace_resets_started_at(
    monkeypatch,
) -> None:
    """W11-5: re-issuing ``start`` for an existing pass id refreshes the
    metadata (started_at, status, optional label/order/trigger_method)
    without creating a duplicate trace. Guards the in-place update path."""

    accountant, report, _rec = _build_accountant()
    accountant.record_stimulus_pass_event("start", "p1", label="Old", order=1)
    first_started_at = report.stimulus_passes[0].started_at

    accountant.record_stimulus_pass_event(
        "start",
        "p1",
        label="New",
        order=2,
        trigger_method="hotkey",
    )

    assert len(report.stimulus_passes) == 1
    trace = report.stimulus_passes[0]
    assert trace.label == "New"
    assert trace.order == 2
    assert trace.trigger_method == "hotkey"
    assert trace.status == "running"
    assert trace.started_at >= first_started_at


def test_verify_target_reaction_treats_success_signal_as_verified(monkeypatch) -> None:
    accountant, _report, _rec = _build_accountant()
    _patch_target_log_count(monkeypatch, count=0)

    verified = accountant.verify_target_reaction(
        {"target_activations": 0},
        {},
        capability="cap",
        trigger_label="trigger.run",
        success_signal=True,
    )

    assert verified is True
