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

The first two cases were RED-then-GREEN in sub-commits 2-3. The last three
(signature-path priority, malformed-trace fail-closed, end-to-end attestation)
are post-close behavioral pins added after the architecture gate, locking
in interactions that the original two cases left implicit.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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


def test_production_handshake_required_rejects_unsigned_complete_marker_when_secret_empty() -> (
    None
):
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
    report.expected_harness_nonce = ""  # eager-consume failed
    report.harness_handshake_required = True  # production path

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "attempted_only"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"


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


def _sign_harness_payload(payload: dict[str, object], secret: str) -> str:
    """Mirror of ``tests/executor/test_playwright_health_reconciliation.py``
    ``_w13_1_sign``: HMAC-SHA256 over the canonical payload with the ``nonce``
    key excluded, sorted keys, no whitespace, UTF-8.
    """
    canonical = json.dumps(
        {k: v for k, v in payload.items() if k != "nonce"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()


def test_production_handshake_required_with_valid_signature_verifies_attempt() -> None:
    """Signature path wins over ``handshake_required=True``.

    When the eager-consume succeeded (``expected_nonce`` non-empty), the
    W13-12 fail-closed branch must not pre-empt the W13-1 signature check.
    Branch order in ``_attempt_has_harness_completion_trace`` is: (1) check
    nonce → if non-empty, verify signature; (2) only then fall through to
    the ``handshake_required`` fail-closed branch. A refactor that inverts
    this order would silently reject every genuine production handshake
    while leaving the existing two W13-12 cases GREEN (they both rely on
    empty nonce). This pin keeps the priority observable from behavior.
    """
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture
    payload: dict[str, object] = {
        "kind": "stimulus",
        "phase": "complete",
        "attempt_id": "harness",
        "family": "onLanguageModelTool",
        "activation_event": "onLanguageModelTool:test",
    }
    payload["nonce"] = _sign_harness_payload(payload, secret)

    report = _build_harness_attempt_report()
    report.extension_host_output = f"[extrace-harness] {json.dumps(payload)}\n"
    report.expected_harness_nonce = secret  # eager-consume succeeded
    report.harness_handshake_required = True  # production path

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "verified"
    assert attempts[0].failure_reason_code == ""


def test_production_handshake_required_rejects_malformed_complete_marker() -> None:
    """Malformed ``[extrace-harness]`` payload + production flag → fail-closed.

    ``_harness_trace_records_by_attempt`` silently skips unparseable
    payloads via ``except ValueError: continue``. With
    ``handshake_required=True`` and an empty nonce, the absence of any
    well-formed trace must route the attempt to ``attempted_only`` —
    not "verified by phase alone" via some other code path. A future
    refactor that changes the parser to coerce partial payloads into
    ``phase="complete"`` would silently bypass W13-12; this pin closes
    that drift surface.
    """
    report = _build_harness_attempt_report()
    report.extension_host_output = (
        '[extrace-harness] {"kind":"stimulus","phase":"complete",'
        '"attempt_id":"harness"'  # truncated — missing closing brace + comma
    )
    report.expected_harness_nonce = ""  # eager-consume failed
    report.harness_handshake_required = True  # production path

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "attempted_only"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"


def test_setup_monitor_stamps_harness_handshake_required_on_real_report(
    tmp_path,
) -> None:
    """End-to-end attestation: ``setup_monitor`` stamps the real dataclass field.

    The 3-fact AST gate (``tests/architecture/test_setup_monitor_handshake_required.py``)
    pins that ``setup_monitor`` *contains* an assignment of literal ``True``
    to ``mon.report.harness_handshake_required``. That gate would still
    pass if a refactor renamed the dataclass field (e.g. to
    ``handshake_active``) — the assignment text matches but the dataclass
    no longer carries the new name, so the field reverts to its
    ``False`` default and the fail-closed branch never fires. This
    behavioral test calls ``setup_monitor`` with a real ``ActivationReport``
    and asserts the stamp lands on the actual attribute, not a stray
    ``MagicMock`` slot.
    """
    from executor.flows.playwright.entrypoint.dispatch import setup_monitor

    real_report = ActivationReport(target_extension_id="publisher.tool")
    monitor_instance = MagicMock()
    monitor_instance.report = real_report

    deps = SimpleNamespace(
        monitor=SimpleNamespace(
            ExtensionMonitor=MagicMock(return_value=monitor_instance),
        ),
        automation=SimpleNamespace(set_scenario_event_reporter=MagicMock()),
    )
    args = SimpleNamespace(
        monitor=True,
        report_path=str(tmp_path / "report.json"),
        target_extension_id="publisher.tool",
        triggers="",
    )

    with patch(
        "executor.flows.playwright.entrypoint.dispatch.load_harness_python_secret",
        return_value="",
    ):
        setup_monitor(
            page=MagicMock(),
            args=args,
            trigger_payload=None,
            bait_files_created=[],
            deps=deps,
        )

    # Even when load_harness_python_secret returns "" (eager-consume miss),
    # setup_monitor MUST stamp harness_handshake_required=True so the
    # fail-closed branch at reconciliation time still fires.
    assert real_report.harness_handshake_required is True
    assert real_report.expected_harness_nonce == ""
