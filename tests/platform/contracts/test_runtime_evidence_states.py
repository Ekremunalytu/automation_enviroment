"""W10-6 regression: contract invariant and executor runtime helper must
agree on which event_attempt status values count as "the harness saw
runtime evidence".

Pre-W10-6 the contract invariant counted only 3 states (attempted_only,
verified, failed) while the executor counted 5 (additionally including
activation_seen, target_log_seen). The resulting drift made the
contract invariant under-count attempts whose target extension
activated but did not fully verify. W10-6 fixes the drift by lifting a
shared ``RUNTIME_EVIDENCE_STATES`` constant into
``packages/analysis_contracts/report_invariants.py`` and importing it
from both helpers.
"""

from __future__ import annotations

from packages.analysis_contracts.report_invariants import (
    RUNTIME_EVIDENCE_STATES,
    _attempt_has_runtime_evidence,
)


_EXPECTED_STATES = frozenset(
    {
        "attempted_only",
        "activation_seen",
        "target_log_seen",
        "verified",
        "failed",
    }
)


def test_shared_constant_pins_the_5_state_set() -> None:
    assert RUNTIME_EVIDENCE_STATES == _EXPECTED_STATES


def test_contract_invariant_uses_shared_constant_for_status_check() -> None:
    """Each member of the shared set must register as runtime evidence."""
    for state in RUNTIME_EVIDENCE_STATES:
        assert _attempt_has_runtime_evidence({"status": state}), (
            f"contract invariant did not recognise status={state!r} as runtime evidence"
        )


def test_contract_invariant_rejects_non_evidence_statuses() -> None:
    for state in {"planned", "running", "blocked", "skipped", "unknown"}:
        assert not _attempt_has_runtime_evidence({"status": state}), (
            f"contract invariant unexpectedly accepted {state!r} as runtime evidence"
        )


def test_attempted_passes_alone_count_as_runtime_evidence() -> None:
    """Even if status is empty, a non-empty attempted_passes list still
    indicates the harness ran something — defensive against producers
    that forget to update status."""
    assert _attempt_has_runtime_evidence(
        {"status": "", "attempted_passes": ["workspace_bootstrap"]}
    )


def test_executor_helper_imports_the_same_constant() -> None:
    """Defends against a future refactor that re-introduces a local
    state set inside the executor helper."""
    from executor.flows.playwright import health_runtime_facts

    assert health_runtime_facts.RUNTIME_EVIDENCE_STATES is RUNTIME_EVIDENCE_STATES
