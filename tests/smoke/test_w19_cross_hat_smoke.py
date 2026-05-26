"""W19-6-followup-2: cross-Hat smoke against the W19-X live-anchor shape.

This is the missing single-test that exercises both W19 acceptance tracks
simultaneously against a synthetic activation-report shape mirroring the
live anchor ``activation_report_ms-python.python-2026.5.2026052501-8247e05ec9ef.json``
(2/2 onDebug* attempts stamped, no scenario-level unaccounted_dropout,
stamped attempts free of the unconfirmed marker, while non-onDebug
unstamped attempts still drive the run-level reason).

The W19-1/W19-2 fixtures pin Hat-1 (executor muhasebe / unaccounted
dropout) in isolation, and the W19-4 / W19-5 tests pin Hat-2 (producer
+ consumer wire) in isolation. A future refactor could close one Hat
while silently reverting the other — this smoke fails the moment that
happens.
"""

from __future__ import annotations

import hashlib
import hmac
import json

from executor.flows.playwright.health.reconciliation import reconcile_event_attempts
from executor.flows.playwright.health.summary import build_automation_health
from executor.flows.playwright.monitor.records import EventAttemptRecord
from executor.flows.playwright.monitor.types import ActivationReport
from executor.flows.playwright.runtime_capture.events import ActivationEntry


_SECRET = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture


def _sign_payload(payload: dict[str, object], secret: str) -> str:
    canonical = json.dumps(
        {k: payload[k] for k in sorted(payload) if k != "nonce"},
        separators=(",", ":"),
        sort_keys=True,
    )
    return hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()


def _signed_complete_marker(family: str, activation_event: str) -> str:
    payload: dict[str, object] = {
        "kind": "stimulus",
        "phase": "complete",
        "attempt_id": "harness",
        "family": family,
        "activation_event": activation_event,
    }
    payload["nonce"] = _sign_payload(payload, _SECRET)
    return f"[extrace-harness] {json.dumps(payload)}\n"


def _on_debug_attempt(family: str, activation_event: str) -> EventAttemptRecord:
    return EventAttemptRecord(
        attempt_id="harness",
        declared_event=activation_event,
        activation_event=activation_event,
        event_family=family,
        executor_action="harness:run_current_stimulus",
        attempted_passes=["target_specific_activation"],
        capability_tags=["debug"],
        verification_contract=["activation_log_prefix", "target_runtime_delta"],
    )


def _unstamped_harness_attempt(
    family: str, activation_event: str
) -> EventAttemptRecord:
    # An attempt routed through harness:run_current_stimulus but with NO
    # marker in extension_host_output: reconcile cannot stamp it, the
    # consumer wire fires, and failure_reason_code lands at
    # ``harness_verification_unconfirmed``. This is what the W19-X live
    # anchor's 6 unstamped onTerminal / onLM attempts look like
    # pre-W19-5-live (W19-5 producer arm extension closes them on the
    # next live run; consumer wire still emits the unconfirmed reason
    # whenever stamping fails).
    return EventAttemptRecord(
        attempt_id=f"harness-{family}",
        declared_event=activation_event,
        activation_event=activation_event,
        event_family=family,
        executor_action="harness:run_current_stimulus",
        attempted_passes=["target_specific_activation"],
        capability_tags=["chat"],
        verification_contract=["activation_log_prefix", "automation_trace"],
    )


def test_w19_cross_hat_invariants_on_synthetic_live_anchor_shape() -> None:
    """W19 must-pass acceptance bar: Hat-1 dropout closed + Hat-2 stamping fired together.

    Asserts the four W19-X live-anchor invariants in one execution:

    - **Hat-2 producer (Half A)**: every onDebug* attempt is stamped with
      ``confirmation_source="harness_nonce"`` after reconciliation.
    - **Hat-2 consumer wire**: stamped attempts have empty
      ``failure_reason_code`` (the unconfirmed marker is suppressed).
    - **Hat-2 consumer wire (negative half)**: unstamped non-onDebug
      attempts still carry ``harness_verification_unconfirmed`` so the
      run-level reason continues to drive when stamping doesn't reach all
      families (matches the W19-X live anchor's 6 unstamped onTerminal /
      onLM attempts pre-W19-5-live).
    - **Hat-1**: no ``*dropout*`` reason appears at the run level. The
      W19-X live anchor showed
      ``automation_health.reasons == ["skipped_scenarios_present",
      "verification_gap_present", "official_unresolved_present",
      "harness_verification_unconfirmed_present"]`` — notably no
      dropout-flavored reason.
    """
    on_debug_families = (
        ("onDebug", "onDebug:python"),
        ("onDebugResolve", "onDebugResolve"),
    )
    extension_host_output = "".join(
        _signed_complete_marker(family, activation_event)
        for family, activation_event in on_debug_families
    )
    activated = [
        ActivationEntry(
            extension_id="publisher.tool",
            activation_event=activation_event,
            timestamp="2026-05-26 12:00:00.000",
            source="log",
        )
        for _, activation_event in on_debug_families
    ]
    report = ActivationReport(
        activated=activated,
        target_extension_id="publisher.tool",
        extension_host_output=extension_host_output,
        event_attempts=[
            _on_debug_attempt(family, activation_event)
            for family, activation_event in on_debug_families
        ]
        + [
            _unstamped_harness_attempt("onLanguageModelTool", "onLanguageModelTool:foo")
        ],
    )
    report.expected_harness_nonce = _SECRET  # type: ignore[attr-defined]

    reconciled = reconcile_event_attempts(report)
    report.event_attempts = list(reconciled)

    # Hat-2 producer: both onDebug attempts stamped harness_nonce.
    debug_attempts = [
        attempt for attempt in reconciled if attempt.event_family.startswith("onDebug")
    ]
    assert len(debug_attempts) == 2, (
        f"expected 2 onDebug attempts in the synthetic shape, got "
        f"{len(debug_attempts)}: {[a.event_family for a in debug_attempts]}"
    )
    for attempt in debug_attempts:
        assert attempt.confirmation_source == "harness_nonce", (
            f"{attempt.event_family} did not stamp harness_nonce — "
            f"W19-4 producer arm regression?"
        )

    # Hat-2 consumer wire: stamped attempts free of the unconfirmed marker.
    for attempt in debug_attempts:
        assert attempt.failure_reason_code != "harness_verification_unconfirmed", (
            f"{attempt.event_family} carries harness_verification_unconfirmed "
            f"despite being stamped — W19-4 consumer-wire gate regression?"
        )

    # Negative half: unstamped onLanguageModelTool (no marker emitted)
    # routes through harness:run_current_stimulus and so the consumer
    # wire fires — ``failure_reason_code`` lands at
    # ``harness_verification_unconfirmed``.
    lm_attempts = [
        attempt
        for attempt in reconciled
        if attempt.event_family == "onLanguageModelTool"
    ]
    assert len(lm_attempts) == 1
    assert lm_attempts[0].confirmation_source == "none"
    assert lm_attempts[0].failure_reason_code == "harness_verification_unconfirmed"

    # Hat-1: no *dropout* reason at the run level. The synthetic report
    # has no scenarios that would emit dropout reasons; this assertion
    # pins that we don't acquire one accidentally.
    health = build_automation_health(
        report,
        extension_host_log_found=True,
        extension_host_log_present=True,
    )
    reasons = list(health.get("reasons", []))
    assert not any("dropout" in reason for reason in reasons), (
        f"Hat-1 regression: a *dropout* reason surfaced in automation_health: {reasons}"
    )

    # Sanity: the run-level reason still emits for the unstamped onCommand
    # half, confirming we built a meaningful mixed shape (a fully-stamped
    # report would silently drop this reason and the test would still pass
    # without exercising the gate).
    assert "harness_verification_unconfirmed_present" in reasons, (
        f"unstamped onCommand half should still drive the unconfirmed reason; "
        f"reasons={reasons}"
    )
