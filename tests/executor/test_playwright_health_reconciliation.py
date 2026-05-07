"""Direct-module tests for ``health_reconciliation``.

[FOLLOWUP w11-precursor-tests] safety net before the W11 ``monitor_lifecycle``
split. Imports the module by its real path (not via the ``monitor`` facade) so
the public reconciliation contract is pinned independently of the facade
re-exports that the W11 refactor will rearrange. Existing tests under
``test_playwright_monitor_attribution.py`` exercise the same functions via the
facade — these direct tests guard against the public API drifting when the
facade moves into the new ``ScenarioAccountant`` / ``ReportAssembler`` split.

Scope: the two public entry points
- ``reconcile_event_attempts(report) -> list[EventAttemptRecord]``
- ``reconcile_coverage_verification(report) -> tuple[summary, matrix, tracks]``

The W10-6 ``RUNTIME_EVIDENCE_STATES`` frozenset
(``attempted_only``, ``activation_seen``, ``target_log_seen``, ``verified``,
``failed``) is asserted here as a structural contract — every transition that
lands an attempt in one of these states is pinned by at least one test.
"""

from __future__ import annotations

from types import SimpleNamespace

from executor.flows.playwright.health.reconciliation import (
    reconcile_coverage_verification,
    reconcile_event_attempts,
)
from executor.flows.playwright.monitor.records import EventAttemptRecord, LogStreamEntry
from executor.flows.playwright.monitor.types import ActivationReport
from executor.flows.playwright.runtime_capture.events import (
    ActivationEntry,
    OutputSignalEvent,
)


# ---------------------------------------------------------------------------
# reconcile_event_attempts — state machine pin tests
# ---------------------------------------------------------------------------


def test_reconcile_event_attempts_empty_input_returns_empty_list() -> None:
    report = ActivationReport(target_extension_id="publisher.tool")
    assert reconcile_event_attempts(report) == []


def test_reconcile_event_attempts_preserves_failed_status() -> None:
    """Already-failed attempts skip the state-machine and surface verification_status=failed."""
    report = ActivationReport(
        target_extension_id="publisher.tool",
        event_attempts=[
            EventAttemptRecord(
                attempt_id="failure-case",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                status="failed",
                failure_reason_code="executor_error",
            )
        ],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "failed"
    assert attempts[0].verification_status == "failed"
    # Reconciliation must not overwrite the original failure reason code.
    assert attempts[0].failure_reason_code == "executor_error"


def test_reconcile_event_attempts_preserves_blocked_status() -> None:
    report = ActivationReport(
        target_extension_id="publisher.tool",
        event_attempts=[
            EventAttemptRecord(
                attempt_id="blocked-case",
                declared_event="onUri",
                activation_event="onUri",
                event_family="onUri",
                status="blocked",
                blocked_reason_code="missing_uri_target",
            )
        ],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "blocked"
    assert attempts[0].verification_status == "blocked"


def test_reconcile_event_attempts_no_contract_with_activation_match_marks_verified() -> (
    None
):
    """The legacy no-contract path: any target activation match is enough to verify."""
    report = ActivationReport(
        activated=[
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:run",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            EventAttemptRecord(
                attempt_id="legacy-verified",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["commands"],
                # verification_contract intentionally empty to take the legacy path.
            )
        ],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "verified"
    assert attempts[0].verification_status == "verified"


def test_reconcile_event_attempts_activation_log_exact_contract_verifies_with_matching_event() -> (
    None
):
    """``activation_log_exact`` requires an exact activation_event match."""
    report = ActivationReport(
        activated=[
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:tool.run",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            EventAttemptRecord(
                attempt_id="exact-contract",
                declared_event="onCommand:tool.run",
                activation_event="onCommand:tool.run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["commands"],
                verification_contract=["activation_log_exact"],
            )
        ],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "verified"
    assert "onCommand:tool.run" in attempts[0].evidence


def test_reconcile_event_attempts_activation_seen_when_target_activates_without_log_or_runtime() -> (
    None
):
    """W10-6 frozenset: ``activation_seen`` intermediate state.

    Pin: target activated for this event, but neither a target-owned log entry
    nor a runtime capability tag intersection is present, and the attempt is
    not a harness attempt. Must land at ``activation_seen``.
    """
    report = ActivationReport(
        activated=[
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:run",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            EventAttemptRecord(
                attempt_id="activation-seen-case",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["chat"],
                verification_contract=["target_runtime_delta"],
            )
        ],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "activation_seen"
    assert attempts[0].verification_status == "activation_seen"
    # Failure-reason field is cleared on the upgrade path.
    assert attempts[0].failure_reason_code == ""


def test_reconcile_event_attempts_target_log_seen_when_target_log_entry_present() -> (
    None
):
    """W10-6 frozenset: ``target_log_seen`` is stronger than ``activation_seen``.

    Adds a non-activation, target-attributed log entry; the upgrade path must
    promote the attempt past ``activation_seen``.
    """
    report = ActivationReport(
        activated=[
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:run",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        log_entries=[
            LogStreamEntry(
                timestamp="2026-01-01 10:00:00.100",
                stream="target_extension_host",
                kind="info",
                message="Tool registered successfully",
                extension_id="publisher.tool",
                is_target_extension=True,
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            EventAttemptRecord(
                attempt_id="log-seen-case",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["chat"],
                verification_contract=["target_runtime_delta"],
            )
        ],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "target_log_seen"
    assert any("Tool registered successfully" in item for item in attempts[0].evidence)


def test_reconcile_event_attempts_target_log_seen_via_output_signal_event() -> None:
    """ADR 0006 §5: target-owned Output channel writes count as ``target_log_seen`` evidence.

    Activation entry is mirrored into ``log_streams`` automatically (kind=activation,
    excluded by the helper). Adding an ``OutputSignalEvent`` with
    ``is_target_extension_event=True`` is the second evidence channel.
    """
    report = ActivationReport(
        activated=[
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:run",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        output_signal_events=[
            OutputSignalEvent(
                timestamp="2026-01-01 10:00:00.200",
                channel="Tool Diagnostics",
                text="ran tool.run successfully",
                extension_id="publisher.tool",
                is_target_extension_event=True,
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            EventAttemptRecord(
                attempt_id="output-signal-case",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["chat"],
                verification_contract=["target_runtime_delta"],
            )
        ],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "target_log_seen"
    assert any("output_channel" in item for item in attempts[0].evidence)


def test_reconcile_event_attempts_harness_attempt_without_completion_trace_unverified() -> (
    None
):
    """Harness attempts route through ``_mark_unverified_harness_attempt``.

    No ``[extrace-harness]`` completion JSON line in extension_host_output and
    no attempted_passes → result_details signals ``could not be confirmed``.
    """
    report = ActivationReport(
        target_extension_id="publisher.tool",
        event_attempts=[
            EventAttemptRecord(
                attempt_id="harness-unconfirmed",
                declared_event="onLanguageModelTool:test",
                activation_event="onLanguageModelTool:test",
                event_family="onLanguageModelTool",
                executor_action="harness:run_current_stimulus",
                attempted_passes=["target_specific_activation"],
                capability_tags=["chat"],
            )
        ],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "attempted_only"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"


def test_reconcile_event_attempts_falls_back_to_attempted_only_for_non_harness_no_evidence() -> (
    None
):
    """No target activation, no harness, but ``attempted_passes`` present → ``attempted_only``."""
    report = ActivationReport(
        target_extension_id="publisher.tool",
        event_attempts=[
            EventAttemptRecord(
                attempt_id="plain-attempt",
                declared_event="onLanguage:python",
                activation_event="onLanguage:python",
                event_family="onLanguage",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["languages_editor"],
            )
        ],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "attempted_only"
    assert attempts[0].verification_status == "attempted_only"


def test_reconcile_event_attempts_falls_back_to_failed_when_no_evidence_at_all() -> (
    None
):
    """Without attempted_passes, harness completion, or blocked_reason_code, the attempt fails."""
    report = ActivationReport(
        target_extension_id="publisher.tool",
        event_attempts=[
            EventAttemptRecord(
                attempt_id="dead-attempt",
                declared_event="onLanguage:python",
                activation_event="onLanguage:python",
                event_family="onLanguage",
                # No attempted_passes, no harness, no blocked_reason_code.
            )
        ],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "failed"
    assert attempts[0].verification_status == "failed"


def test_reconcile_event_attempts_returns_terminal_states_in_w10_6_frozenset() -> None:
    """Structural guard for the W10-6 ``RUNTIME_EVIDENCE_STATES`` contract.

    Every status reconcile_event_attempts assigns must remain inside
    ``{attempted_only, activation_seen, target_log_seen, verified, failed,
    blocked}`` (the running/planned states are entry conditions, never
    terminal). This pin keeps the W11 split honest.
    """
    allowed = {
        "attempted_only",
        "activation_seen",
        "target_log_seen",
        "verified",
        "failed",
        "blocked",
    }
    report = ActivationReport(
        activated=[
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onCommand:run",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        event_attempts=[
            EventAttemptRecord(
                attempt_id="a",
                declared_event="onCommand:run",
                activation_event="onCommand:run",
                event_family="onCommand",
                attempted_passes=["ui_first_user_session"],
                capability_tags=["chat"],
                verification_contract=["target_runtime_delta"],
            ),
            EventAttemptRecord(
                attempt_id="b",
                declared_event="onLanguage:python",
                activation_event="onLanguage:python",
                event_family="onLanguage",
                # Plain attempted-only fallback.
                attempted_passes=["ui_first_user_session"],
            ),
            EventAttemptRecord(
                attempt_id="c",
                declared_event="onUri",
                activation_event="onUri",
                event_family="onUri",
                status="blocked",
                blocked_reason_code="missing_uri_target",
            ),
        ],
    )

    attempts = reconcile_event_attempts(report)

    assert {a.status for a in attempts} <= allowed


# ---------------------------------------------------------------------------
# reconcile_coverage_verification — track summary + matrix shape pin
# ---------------------------------------------------------------------------


def test_reconcile_coverage_verification_empty_report_returns_zeroed_summary() -> None:
    report = ActivationReport(target_extension_id="publisher.tool")

    summary, matrix, tracks = reconcile_coverage_verification(report)

    assert summary["attempted"] == 0
    assert summary["verified"] == 0
    assert summary["attempted_capabilities"] == []
    assert summary["verified_capabilities"] == []
    assert matrix == []
    assert set(tracks.keys()) == {"official", "heuristic"}
    assert tracks["official"]["source"] == "official_activation_track"
    assert tracks["heuristic"]["source"] == "heuristic_workflow_track"


def test_reconcile_coverage_verification_marks_supported_verified_capability() -> None:
    # ``reconcile_coverage_verification`` reads everything via ``getattr``, so a
    # ``SimpleNamespace`` lets us pin the exact ``official_*`` capability sets
    # without relying on the property derivers in ``ActivationReport``.
    report = SimpleNamespace(
        target_extension_id="publisher.tool",
        coverage_tracks={
            "official": {
                "summary": {},
                "matrix": [
                    {"capability": "commands", "support_status": "covered"},
                    {"capability": "languages", "support_status": "covered"},
                    {"capability": "rare_cap", "support_status": "not_covered"},
                ],
            }
        },
        official_attempted_capabilities=["commands", "languages", "rare_cap"],
        official_verified_capabilities=["commands"],
        heuristic_attempted_capabilities=[],
        heuristic_verified_capabilities=[],
    )

    summary, matrix, _tracks = reconcile_coverage_verification(report)
    matrix_by_cap = {entry["capability"]: entry for entry in matrix}

    assert matrix_by_cap["commands"]["verification_status"] == "verified"
    assert matrix_by_cap["commands"]["verified"] is True
    assert matrix_by_cap["languages"]["verification_status"] == "attempted_only"
    assert matrix_by_cap["languages"]["verified"] is False
    # ``rare_cap`` is not covered → drops out of attempted/verified counts AND
    # its row stays at ``not_attempted`` regardless of the input lists.
    assert matrix_by_cap["rare_cap"]["verification_status"] == "not_attempted"
    assert matrix_by_cap["rare_cap"]["attempted"] is False
    assert matrix_by_cap["rare_cap"]["verified"] is False
    # Counts reflect the post-filter capabilities, not the raw input.
    assert summary["attempted"] == 2
    assert summary["verified"] == 1
    assert summary["attempted_capabilities"] == ["commands", "languages"]
    assert summary["verified_capabilities"] == ["commands"]


def test_reconcile_coverage_verification_falls_back_to_top_level_summary_and_matrix() -> (
    None
):
    """When ``coverage_tracks.official`` is missing, fall back to ``coverage_summary`` + ``coverage_matrix``."""
    report = SimpleNamespace(
        target_extension_id="publisher.tool",
        coverage_tracks={},
        coverage_summary={"label": "fallback"},
        coverage_matrix=[{"capability": "commands", "support_status": "covered"}],
        official_attempted_capabilities=["commands"],
        official_verified_capabilities=["commands"],
        heuristic_attempted_capabilities=[],
        heuristic_verified_capabilities=[],
    )

    summary, matrix, _tracks = reconcile_coverage_verification(report)

    assert matrix[0]["verification_status"] == "verified"
    # Top-level summary fields propagate through.
    assert summary["label"] == "fallback"
    assert summary["attempted"] == 1
    assert summary["verified"] == 1
