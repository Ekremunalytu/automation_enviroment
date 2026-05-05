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
    # Only the (name, reason_code)-complete skip survives the filter.
    assert len(report.skipped_scenarios) == 1
    assert isinstance(report.skipped_scenarios[0], SkippedScenarioRecord)
    assert report.skipped_scenarios[0].name == "s3"
    assert report.extra_trigger_failures == ["lock_busy"]
    # Note: ``failed_scenarios`` is re-derived from ``scenario_traces``
    # by ``_synchronize_scenario_truth``; with no traces in this fixture
    # the list ends up empty even though the result reported "s1" as
    # failed. Pinned by ``test_record_failed_scenarios_with_no_traces…``
    # above; this assertion stays loose to that contract.
    assert report.failed_scenarios == []


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
