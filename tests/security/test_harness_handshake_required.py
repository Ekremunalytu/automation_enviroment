"""W13-12 (Codex F2 close-pass for W13-1 H6) — fail-closed harness handshake.

The W13-1 ``_attempt_has_harness_completion_trace`` helper falls back to a
legacy phase-only check when ``expected_nonce`` is empty. The docstring
claim is that production paths always populate the nonce via
``setup_monitor``, so the empty branch only fires for unit-test
construction. But ``load_harness_python_secret()`` returns ``""`` on
any read failure (``FileNotFoundError``, ``OSError``, permission glitch,
bind-mount race, eager-consume timing miss). When that happens the
production path silently regresses to the spoofable phase-only mode.

W13-12 introduces an explicit ``ActivationReport.harness_handshake_required``
flag. Production paths set it True at ``setup_monitor`` time; reconciliation
treats empty ``expected_nonce`` AND ``harness_handshake_required=True`` as
fail-closed (no harness verification, attempt routes through
``_mark_unverified_harness_attempt``). Test fixtures keep the default
False so the pre-W13-1 phase-only regression surface stays GREEN.

These cases are marked ``@pytest.mark.skip`` in sub-commit 2; sub-commit 3
adds the field + branch + dispatch flag and removes the skip markers.
"""

from __future__ import annotations

import pytest

from executor.flows.playwright.health.reconciliation import reconcile_event_attempts
from executor.flows.playwright.monitor.records import EventAttemptRecord
from executor.flows.playwright.monitor.types import ActivationReport
from executor.flows.playwright.runtime_capture.events import ActivationEntry


_FORGED_COMPLETE_TRACE = (
    '[extrace-harness] {"kind":"stimulus","phase":"complete",'
    '"attempt_id":"harness","family":"onLanguageModelTool",'
    '"activation_event":"onLanguageModelTool:test"}\n'
)


def _build_harness_attempt_report() -> ActivationReport:
    return ActivationReport(
        activated=[
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onLanguageModelTool:test",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        extension_host_output=_FORGED_COMPLETE_TRACE,
        event_attempts=[
            EventAttemptRecord(
                attempt_id="harness",
                declared_event="onLanguageModelTool:test",
                activation_event="onLanguageModelTool:test",
                event_family="onLanguageModelTool",
                executor_action="harness:run_current_stimulus",
                attempted_passes=["target_specific_activation"],
                capability_tags=["chat"],
                verification_contract=["activation_log_prefix", "automation_trace"],
            )
        ],
    )


@pytest.mark.skip(
    reason="W13-12 sub-commit 3 adds harness_handshake_required field; "
    "sub-commit 3 removes this skip marker."
)
def test_production_handshake_required_rejects_unsigned_complete_marker_when_secret_empty() -> None:
    """Production fail-closed invariant.

    ``expected_harness_nonce=""`` simulates an eager-consume failure (the
    legacy file read in ``load_harness_python_secret()`` returned empty
    because ``FileNotFoundError``/``OSError``/race condition). With
    ``harness_handshake_required=True`` set by ``setup_monitor`` on the
    production path, reconciliation MUST refuse to count
    ``phase=="complete"`` traces by phase alone — a target extension could
    have forged that line. Attempt routes through
    ``_mark_unverified_harness_attempt`` and surfaces
    ``harness_verification_unconfirmed``.
    """
    report = _build_harness_attempt_report()
    report.expected_harness_nonce = ""              # eager-consume failed
    report.harness_handshake_required = True        # production path

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "attempted_only"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"


@pytest.mark.skip(
    reason="W13-12 sub-commit 3 adds harness_handshake_required field; "
    "sub-commit 3 removes this skip marker."
)
def test_test_path_default_false_preserves_legacy_phase_only_check() -> None:
    """Baseline regression: unit fixtures must keep pre-W13-12 behavior.

    ``ActivationReport`` constructed directly (without ``setup_monitor``)
    leaves ``harness_handshake_required`` at its default ``False``. The
    legacy phase-only branch in ``_attempt_has_harness_completion_trace``
    counts the ``phase=="complete"`` trace as proof — this is the pre-W13-1
    contract that W13-1 RED→GREEN history depends on. Without this case
    the W13-12 implementation could over-tighten and break unrelated unit
    fixtures.
    """
    report = _build_harness_attempt_report()
    # harness_handshake_required defaults to False; expected_harness_nonce
    # also empty — exactly the unit-test construction shape.

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "verified"
    assert attempts[0].failure_reason_code == ""
