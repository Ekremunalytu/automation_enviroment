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

import hashlib
import hmac
import json
from types import SimpleNamespace

import pytest

from executor.flows.playwright.health.reconciliation import (
    _mark_unverified_harness_attempt,
    reconcile_coverage_verification,
    reconcile_event_attempts,
)
from executor.flows.playwright.health.summary import build_automation_health
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


# ---------------------------------------------------------------------------
# W13-1 (Codex H6) — RED precursor tests for spoofable harness markers
#
# Goal: harness completion markers must carry an HMAC-SHA256 ``nonce`` field
# computed over a canonical payload using a per-container secret loaded by
# the Python orchestration before ``install_extension`` runs (see
# ``documents/active-work/W13-test-expansion-observability.md`` →
# Per-Item Detail → W13-1, Option C). Without it, a target extension can
# write the literal ``[extrace-harness] {phase:"complete"}`` string to
# stdout and forge ``automation_trace`` proof.
#
# These tests reference the future contract:
#   - ``ActivationReport.expected_harness_nonce: str`` (new field, sub-commit 3)
#   - ``_verify_harness_marker_signature(payload, expected_nonce)`` helper in
#     ``health/reconciliation.py`` (sub-commit 4)
#
# All three are skipped until sub-commit 4 lands the verifier; sub-commit 4
# removes the skip markers and the cases must pass GREEN. The ``test_local``
# baseline is unaffected by skipped cases (1452 → 1452 expected).
# ---------------------------------------------------------------------------


def _w13_1_canonical_payload(payload: dict[str, object]) -> bytes:
    """HMAC input shape (frozen by sub-commit 4 design decision).

    Sorted keys, no whitespace, UTF-8. The ``nonce`` key itself is excluded so
    callers compute HMAC over the unsigned envelope and append the signature.
    """
    return json.dumps(
        {k: v for k, v in payload.items() if k != "nonce"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _w13_1_sign(payload: dict[str, object], secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        _w13_1_canonical_payload(payload),
        hashlib.sha256,
    ).hexdigest()


def test_reconcile_w13_1_rejects_forged_complete_marker_without_nonce() -> None:
    """A ``[extrace-harness] {phase:"complete"}`` line lacking ``nonce`` is rejected.

    Today's behaviour (pre-W13-1): the line satisfies ``automation_trace`` and
    flips the attempt to ``verified``. Post-W13-1: missing ``nonce`` →
    ``_verify_harness_marker_signature`` returns False → harness completion
    trace not counted → attempt routes through
    ``_mark_unverified_harness_attempt`` and surfaces
    ``harness_verification_unconfirmed``.
    """
    report = ActivationReport(
        activated=[
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onLanguageModelTool:test",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        # Note: ``expected_harness_nonce`` is the future field added in
        # sub-commit 3; without it on the report, the verifier defaults to
        # rejecting unsigned markers (fail-closed).
        extension_host_output=(
            '[extrace-harness] {"kind":"stimulus","phase":"complete",'
            '"attempt_id":"harness","family":"onLanguageModelTool",'
            '"activation_event":"onLanguageModelTool:test"}\n'
        ),
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
    # Sub-commit 3 will add this field to ActivationReport.
    report.expected_harness_nonce = "secret-loaded-from-results-handshake"  # type: ignore[attr-defined]

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "attempted_only"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"


def test_reconcile_w13_1_rejects_forged_complete_marker_with_invalid_nonce() -> None:
    """A marker with a syntactically present but cryptographically invalid nonce is rejected."""
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture, simulates orchestration handshake
    payload = {
        "kind": "stimulus",
        "phase": "complete",
        "attempt_id": "harness",
        "family": "onLanguageModelTool",
        "activation_event": "onLanguageModelTool:test",
        # Forged nonce: 64-hex-char string but not the actual HMAC over the
        # payload. Target extension can produce arbitrary hex strings.
        "nonce": "0" * 64,
    }
    report = ActivationReport(
        activated=[
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onLanguageModelTool:test",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        extension_host_output=f"[extrace-harness] {json.dumps(payload)}\n",
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
    report.expected_harness_nonce = secret  # type: ignore[attr-defined]

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "attempted_only"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"


def test_reconcile_w13_1_accepts_genuine_complete_marker_with_valid_nonce() -> None:
    """A marker carrying a correct HMAC under the orchestration secret verifies the attempt.

    Regression baseline for the genuine path: same canonical payload format
    as the rejection cases above, plus a valid signature → status flips to
    ``verified`` (matches today's behaviour for the no-nonce path; W13-1
    preserves it under the auth gate).
    """
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture, simulates orchestration handshake
    payload: dict[str, object] = {
        "kind": "stimulus",
        "phase": "complete",
        "attempt_id": "harness",
        "family": "onLanguageModelTool",
        "activation_event": "onLanguageModelTool:test",
    }
    payload["nonce"] = _w13_1_sign(payload, secret)

    report = ActivationReport(
        activated=[
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event="onLanguageModelTool:test",
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        extension_host_output=f"[extrace-harness] {json.dumps(payload)}\n",
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
    report.expected_harness_nonce = secret  # type: ignore[attr-defined]

    attempts = reconcile_event_attempts(report)

    assert attempts[0].status == "verified"
    assert attempts[0].failure_reason_code == ""


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


# ---------------------------------------------------------------------------
# W13-11 — load_harness_python_secret env-priority unit cases
# ---------------------------------------------------------------------------
#
# Codex F1 close-pass for W13-1 H6. Production paths receive the per-launch
# HMAC secret via ``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE``, populated on the
# host by ``executor.host.consume_harness_python_secret_eager`` before the
# analyzed VSIX is admitted. The legacy file branch is preserved as a
# fallback for unit-test paths that construct ``ActivationReport`` directly
# without going through host-side eager-consume.
#
# These cases pin the three states (env present, env absent + file present,
# both absent) plus the defense-in-depth invariant that the file is unlinked
# even when env wins — so a stale file from a crashed eager-consume cannot
# leak into the next launch cycle.


def test_load_harness_python_secret_prefers_env_var_over_file(
    tmp_path,
    monkeypatch,
) -> None:
    """Env var wins over file; file is still unlinked (defense-in-depth)."""
    from executor.flows.playwright.health.security import (
        load_harness_python_secret,
    )

    monkeypatch.setenv(
        "EXECUTOR_HARNESS_PYTHON_SECRET_VALUE",
        "env-value-hex-string",
    )
    secret_path = tmp_path / "_extrace_harness_python_secret"
    secret_path.write_text(
        "file-value-hex-string",
        encoding="utf-8",
    )

    secret = load_harness_python_secret(path=secret_path)

    assert secret == "env-value-hex-string", (  # noqa: S105 — test fixture
        "env var must take precedence over the legacy file — this is the "
        "W13-11 invariant that lets host-side eager-consume bypass the "
        "container-internal /results read."
    )
    assert not secret_path.exists(), (
        "even when env wins, load_harness_python_secret must still unlink "
        "the legacy file so a stale file from a crashed eager-consume "
        "cannot persist into the next launch cycle (defense-in-depth)."
    )


def test_load_harness_python_secret_legacy_file_when_env_absent(
    tmp_path,
    monkeypatch,
) -> None:
    """Env unset + file present → file value read and unlinked (legacy path)."""
    from executor.flows.playwright.health.security import (
        load_harness_python_secret,
    )

    monkeypatch.delenv("EXECUTOR_HARNESS_PYTHON_SECRET_VALUE", raising=False)
    secret_path = tmp_path / "_extrace_harness_python_secret"
    secret_path.write_text(
        "file-value-hex-string",
        encoding="utf-8",
    )

    secret = load_harness_python_secret(path=secret_path)

    assert secret == "file-value-hex-string", (  # noqa: S105 — test fixture
        "with no env var the legacy file path must remain functional — "
        "this is what keeps the existing test surface (W13-1 unit cases) "
        "GREEN and provides the fail-soft fallback for production edge "
        "cases (consume crashed mid-run, etc.)."
    )
    assert not secret_path.exists(), "legacy path also unlinks after read."


def test_load_harness_python_secret_empty_when_both_absent(
    tmp_path,
    monkeypatch,
) -> None:
    """Env unset + file absent → empty string (W13-12 fail-closed enforcement point)."""
    from executor.flows.playwright.health.security import (
        load_harness_python_secret,
    )

    monkeypatch.delenv("EXECUTOR_HARNESS_PYTHON_SECRET_VALUE", raising=False)
    # No file written; tmp_path is empty.
    secret_path = tmp_path / "_extrace_harness_python_secret"

    secret = load_harness_python_secret(path=secret_path)

    assert secret == "", (
        "with no env and no file the secret is empty — production paths "
        "must NOT reach this state once W13-12 lands fail-closed enforcement "
        "(empty expected_nonce + handshake_required=True → no harness "
        "completion trace can satisfy automation_trace). Pre-W13-12 the "
        "empty branch falls back to phase-only acceptance (spoofable). "
        "W13-11 reaches this state only via worst-case pre-W13-11 "
        "status quo (no eager-consume, no launch_vscode.sh)."
    )


# ---------------------------------------------------------------------------
# W19-4 — onDebug* nonce confirmation + consumer wire
#
# Producer wire (Half A): ``reconcile_event_attempts`` stamps
# ``confirmation_source = "harness_nonce"`` on onDebug* attempts whose
# harness completion HMAC verified, using the existing
# ``_attempt_has_harness_completion_trace`` boolean as the unique join
# point.
#
# Consumer wire (Half B): ``_mark_unverified_harness_attempt`` gates the
# ``failure_reason_code = "harness_verification_unconfirmed"`` set on the
# attempt already carrying a non-"none" ``confirmation_source`` — so a
# stamped attempt no longer triggers the run-level
# ``harness_verification_unconfirmed_present`` reason emission at
# ``build_automation_health``.
#
# Tests reuse the ``_w13_1_sign`` / ``_w13_1_canonical_payload`` helpers
# above; the fixture shapes mirror the W13-1 GREEN/RED cases with the
# event family swapped to ``onDebug*``.
# ---------------------------------------------------------------------------


_W19_4_ONDEBUG_FAMILIES = (
    "onDebug",
    "onDebugResolve",
    "onDebugInitialConfigurations",
    "onDebugDynamicConfigurations",
    "onDebugAdapterProtocolTracker",
)

_W19_4_NON_ONDEBUG_FAMILIES = (
    # W19-5 widened the stamp scope to onTerminalShellIntegration +
    # onLanguageModelTool (with "log_record"), so this scope-discipline
    # parametrize narrows to onCommand only. onCommand is *intentionally
    # never stamped* via either branch — its dispatch goes through the
    # planner's command:auto / scenario:coding_session executor_action
    # paths and never carries the automation_trace contract. A future
    # widening of the stamp scope to onCommand would require an explicit
    # design conversation.
    ("onCommand", "onCommand:bar"),
)


def _w19_4_signed_complete_payload(
    family: str, activation_event: str, secret: str
) -> dict[str, object]:
    payload: dict[str, object] = {
        "kind": "stimulus",
        "phase": "complete",
        "attempt_id": "harness",
        "family": family,
        "activation_event": activation_event,
    }
    payload["nonce"] = _w13_1_sign(payload, secret)
    return payload


def _w19_4_build_onDebug_report(  # noqa: N802 — "onDebug" preserves the VS Code event-family name
    family: str,
    secret: str,
    *,
    extension_host_output: str | None = None,
    activated: list[ActivationEntry] | None = None,
    verification_contract: list[str] | None = None,
) -> ActivationReport:
    if extension_host_output is None:
        payload = _w19_4_signed_complete_payload(family, family, secret)
        extension_host_output = f"[extrace-harness] {json.dumps(payload)}\n"
    if activated is None:
        activated = [
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event=family,
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ]
    contracts = verification_contract or [
        "activation_log_prefix",
        "target_runtime_delta",
    ]
    report = ActivationReport(
        activated=activated,
        target_extension_id="publisher.tool",
        extension_host_output=extension_host_output,
        event_attempts=[
            EventAttemptRecord(
                attempt_id="harness",
                declared_event=family,
                activation_event=family,
                event_family=family,
                executor_action="harness:run_current_stimulus",
                attempted_passes=["target_specific_activation"],
                capability_tags=["debug"],
                verification_contract=contracts,
            )
        ],
    )
    report.expected_harness_nonce = secret  # type: ignore[attr-defined]
    return report


def test_w19_4_stamps_harness_nonce_on_verified_onDebug_attempt() -> None:  # noqa: N802 — "onDebug" preserves the VS Code event-family name
    """Producer GREEN path: verified HMAC complete marker on onDebug stamps."""
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture
    report = _w19_4_build_onDebug_report("onDebug", secret)

    attempts = reconcile_event_attempts(report)

    assert attempts[0].confirmation_source == "harness_nonce"
    # Verified path reached via activation_log_prefix exact-match on the
    # activated entry — Half A stamps independent of verified vs attempted_only.
    assert attempts[0].status == "verified"


@pytest.mark.parametrize("family", _W19_4_ONDEBUG_FAMILIES)
def test_w19_4_stamps_harness_nonce_for_all_five_onDebug_variants(family: str) -> None:  # noqa: N802 — "onDebug" preserves the VS Code event-family name
    """Prefix-match invariant: all five OFFICIAL_EVENT_REGISTRY onDebug* variants stamp."""
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture
    report = _w19_4_build_onDebug_report(family, secret)

    attempts = reconcile_event_attempts(report)

    assert attempts[0].confirmation_source == "harness_nonce", (
        f"{family} should stamp confirmation_source=harness_nonce"
    )


def test_w19_4_does_not_stamp_on_forged_nonce_for_onDebug() -> None:  # noqa: N802 — "onDebug" preserves the VS Code event-family name
    """Producer fail-closed: forged HMAC nonce leaves confirmation_source at 'none'."""
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture
    forged_payload = {
        "kind": "stimulus",
        "phase": "complete",
        "attempt_id": "harness",
        "family": "onDebug",
        "activation_event": "onDebug",
        "nonce": "0" * 64,  # forged: 64-hex-char string but not the actual HMAC
    }
    report = _w19_4_build_onDebug_report(
        "onDebug",
        secret,
        extension_host_output=f"[extrace-harness] {json.dumps(forged_payload)}\n",
        activated=[],  # also exclude target activation so attempt stays unverified
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].confirmation_source == "none"
    assert attempts[0].status == "attempted_only"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"


def test_w19_4_does_not_stamp_when_no_marker_present_for_onDebug() -> None:  # noqa: N802 — "onDebug" preserves the VS Code event-family name
    """Producer fail-closed: missing harness marker leaves confirmation_source at 'none'."""
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture
    report = _w19_4_build_onDebug_report(
        "onDebug",
        secret,
        extension_host_output="",
        activated=[],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].confirmation_source == "none"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"


@pytest.mark.parametrize(
    "family,activation_event",
    _W19_4_NON_ONDEBUG_FAMILIES,
)
def test_w19_4_does_not_stamp_on_non_onDebug_families(  # noqa: N802 — "onDebug" preserves the VS Code event-family name
    family: str, activation_event: str
) -> None:
    """Scope discipline: verified HMAC on out-of-scope families leaves confirmation_source at 'none'.

    Post-W19-5 the parametrize set narrows to ``onCommand`` (W19-5 widened
    the stamp scope to onTerminalShellIntegration + onLanguageModelTool
    with the ``"log_record"`` label — see the W19-5 block below). A
    future widening to ``onCommand`` would require an explicit design
    conversation.
    """
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture
    payload = _w19_4_signed_complete_payload(family, activation_event, secret)
    report = ActivationReport(
        activated=[
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event=activation_event,
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ],
        target_extension_id="publisher.tool",
        extension_host_output=f"[extrace-harness] {json.dumps(payload)}\n",
        event_attempts=[
            EventAttemptRecord(
                attempt_id="harness",
                declared_event=activation_event,
                activation_event=activation_event,
                event_family=family,
                executor_action="harness:run_current_stimulus",
                attempted_passes=["target_specific_activation"],
                capability_tags=["chat"],
                verification_contract=["activation_log_prefix", "automation_trace"],
            )
        ],
    )
    report.expected_harness_nonce = secret  # type: ignore[attr-defined]

    attempts = reconcile_event_attempts(report)

    assert attempts[0].confirmation_source == "none", (
        f"{family} is out of W19-4 scope and must stay at confirmation_source='none'"
    )


def test_w19_4_mark_unverified_skips_failure_reason_code_when_confirmation_source_stamped() -> (
    None
):
    """Consumer wire unit: stamped attempts skip the run-level reason set.

    Direct unit call on ``_mark_unverified_harness_attempt`` — the function
    still moves the attempt to the ``attempted_only`` terminal state and
    writes evidence, but no longer flags it as
    ``harness_verification_unconfirmed`` because the stamp already records
    confirmed harness evidence.
    """
    attempt = EventAttemptRecord(
        attempt_id="harness",
        declared_event="onDebug",
        activation_event="onDebug",
        event_family="onDebug",
        executor_action="harness:run_current_stimulus",
        confirmation_source="harness_nonce",
    )

    _mark_unverified_harness_attempt(attempt, execution_closed=True)

    assert attempt.status == "attempted_only"
    assert attempt.verification_status == "attempted_only"
    assert attempt.failure_reason_code == ""
    assert any("harness_trace:harness" in str(item) for item in attempt.evidence)


def test_w19_4_mark_unverified_sets_failure_reason_code_when_confirmation_source_is_none() -> (
    None
):
    """Consumer wire existing-behavior preservation: unstamped attempts still flag the reason."""
    attempt = EventAttemptRecord(
        attempt_id="harness",
        declared_event="onDebug",
        activation_event="onDebug",
        event_family="onDebug",
        executor_action="harness:run_current_stimulus",
        confirmation_source="none",
    )

    _mark_unverified_harness_attempt(attempt, execution_closed=True)

    assert attempt.status == "attempted_only"
    assert attempt.failure_reason_code == "harness_verification_unconfirmed"


def _w19_4_unstamped_attempt(family: str, activation_event: str) -> EventAttemptRecord:
    return EventAttemptRecord(
        attempt_id=f"harness-{family}",
        declared_event=activation_event,
        activation_event=activation_event,
        event_family=family,
        executor_action="harness:run_current_stimulus",
        confirmation_source="none",
        failure_reason_code="harness_verification_unconfirmed",
        status="attempted_only",
        verification_status="attempted_only",
    )


def _w19_4_stamped_attempt() -> EventAttemptRecord:
    return EventAttemptRecord(
        attempt_id="harness-onDebug",
        declared_event="onDebug",
        activation_event="onDebug",
        event_family="onDebug",
        executor_action="harness:run_current_stimulus",
        confirmation_source="harness_nonce",
        failure_reason_code="",  # Half B suppressed the unconfirmed flag
        status="attempted_only",
        verification_status="attempted_only",
    )


def _w19_4_run_reasons(event_attempts: list[EventAttemptRecord]) -> list[str]:
    # ``build_automation_health`` emits many run-level reasons (missing
    # target stream, no activation log, etc.) that are irrelevant here —
    # tests below assert only on the presence/absence of
    # ``harness_verification_unconfirmed_present``, which is driven
    # exclusively by per-attempt ``failure_reason_code`` values.
    report = ActivationReport(
        target_extension_id="publisher.tool",
        extension_host_output="dummy output",
        event_attempts=event_attempts,
    )
    health = build_automation_health(
        report,
        extension_host_log_found=True,
        extension_host_log_present=True,
    )
    return list(health.get("reasons", []))


def test_w19_4_harness_verification_unconfirmed_present_drops_only_when_all_unconfirmed_attempts_stamp_single_stamped() -> (
    None
):
    """End-to-end orthogonality 1/3: single stamped attempt → reason NOT emitted."""
    reasons = _w19_4_run_reasons([_w19_4_stamped_attempt()])

    assert "harness_verification_unconfirmed_present" not in reasons


def test_w19_4_harness_verification_unconfirmed_present_drops_only_when_all_unconfirmed_attempts_stamp_single_unstamped() -> (
    None
):
    """End-to-end orthogonality 2/3: single unstamped attempt → reason emitted.

    Uses ``onCommand`` because W19-5 widened the producer arm to stamp
    onLanguageModelTool / onTerminalShellIntegration — the previous
    ``onLanguageModelTool`` choice would now stamp and silently invert
    the test premise.
    """
    reasons = _w19_4_run_reasons(
        [_w19_4_unstamped_attempt("onCommand", "onCommand:bar")]
    )

    assert "harness_verification_unconfirmed_present" in reasons


def test_w19_4_harness_verification_unconfirmed_present_drops_only_when_all_unconfirmed_attempts_stamp_mixed() -> (
    None
):
    """End-to-end orthogonality 3/3: mixed (stamped + unstamped non-onDebug) → reason still emitted.

    Pins that the consumer wire is per-attempt — an unstamped attempt
    elsewhere in the run still carries
    ``failure_reason_code='harness_verification_unconfirmed'`` and still
    drives the run-level reason. W19-5 closed onTerminalShellIntegration
    + onLanguageModelTool families, so the unstamped half here uses
    ``onCommand`` — its dispatch path never carries the
    automation_trace contract that would route through the harness
    stamp pipeline. A target extension whose declared events fall
    entirely outside the W19-4/W19-5 stamped scope keeps the original
    diagnostic shape.
    """
    reasons = _w19_4_run_reasons(
        [
            _w19_4_stamped_attempt(),
            _w19_4_unstamped_attempt("onCommand", "onCommand:bar"),
        ]
    )

    assert "harness_verification_unconfirmed_present" in reasons


# ---------------------------------------------------------------------------
# W19-5 — onTerminalShellIntegration + onLanguageModelTool log_record stamp
#
# Hat-2 closure. Markers for these families ride the same HMAC-signed
# runCurrentStimulus pipeline used by onDebug* (planner routes onLM
# directly through harness:run_current_stimulus; onTerminalShellIntegration
# arrives via the OFFICIAL_EVENT_REGISTRY harness_fallback path because
# its verification_contract carries automation_trace). The W19-5
# producer-arm extension stamps these families with
# ``confirmation_source = "log_record"`` — distinct from onDebug's
# ``"harness_nonce"`` label to reflect the local-only confirmation
# surface (these families lack the activation_log_exact contract that
# justifies harness_nonce's stronger label semantically). The
# run-level reason ``harness_verification_unconfirmed_present`` gates
# on ``confirmation_source != "none"`` regardless of label, so the
# diagnostic distinction is the only behavioral difference between
# harness_nonce and log_record today.
# ---------------------------------------------------------------------------


_W19_5_ONLM_VARIANTS = (
    "onLanguageModelTool",
    "onLanguageModelTool:configurePythonEnvironment",
    "onLanguageModelTool:createVirtualEnvironment",
    "onLanguageModelTool:getPythonEnvironmentDetails",
    "onLanguageModelTool:installPythonPackages",
)


def _w19_5_build_log_record_report(
    family: str,
    activation_event: str,
    secret: str,
    *,
    extension_host_output: str | None = None,
    activated: list[ActivationEntry] | None = None,
) -> ActivationReport:
    if extension_host_output is None:
        payload = _w19_4_signed_complete_payload(family, activation_event, secret)
        extension_host_output = f"[extrace-harness] {json.dumps(payload)}\n"
    if activated is None:
        activated = [
            ActivationEntry(
                extension_id="publisher.tool",
                activation_event=activation_event,
                timestamp="2026-01-01 10:00:00.000",
                source="log",
            )
        ]
    capability_tag = (
        "chat" if family.startswith("onLanguageModelTool") else "terminal_tasks"
    )
    report = ActivationReport(
        activated=activated,
        target_extension_id="publisher.tool",
        extension_host_output=extension_host_output,
        event_attempts=[
            EventAttemptRecord(
                attempt_id="harness",
                declared_event=activation_event,
                activation_event=activation_event,
                event_family=family,
                executor_action="harness:run_current_stimulus",
                attempted_passes=["target_specific_activation"],
                capability_tags=[capability_tag],
                verification_contract=["activation_log_prefix", "automation_trace"],
            )
        ],
    )
    report.expected_harness_nonce = secret  # type: ignore[attr-defined]
    return report


def test_w19_5_stamps_log_record_on_terminal_shell_integration() -> None:
    """Producer GREEN path: verified HMAC marker on onTerminalShellIntegration stamps log_record."""
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture
    report = _w19_5_build_log_record_report(
        "onTerminalShellIntegration", "onTerminalShellIntegration", secret
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].confirmation_source == "log_record"


@pytest.mark.parametrize("activation_event", _W19_5_ONLM_VARIANTS)
def test_w19_5_stamps_log_record_for_all_language_model_tool_variants(
    activation_event: str,
) -> None:
    """Prefix-match invariant: bare onLanguageModelTool + onLanguageModelTool:<tool> variants stamp."""
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture
    report = _w19_5_build_log_record_report(
        "onLanguageModelTool", activation_event, secret
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].confirmation_source == "log_record", (
        f"{activation_event} should stamp confirmation_source=log_record"
    )


def test_w19_5_does_not_stamp_on_forged_nonce_for_language_model_tool() -> None:
    """Producer fail-closed: forged HMAC nonce leaves confirmation_source at 'none'."""
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture
    forged_payload = {
        "kind": "stimulus",
        "phase": "complete",
        "attempt_id": "harness",
        "family": "onLanguageModelTool",
        "activation_event": "onLanguageModelTool:foo",
        "nonce": "0" * 64,
    }
    report = _w19_5_build_log_record_report(
        "onLanguageModelTool",
        "onLanguageModelTool:foo",
        secret,
        extension_host_output=f"[extrace-harness] {json.dumps(forged_payload)}\n",
        activated=[],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].confirmation_source == "none"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"


def test_w19_5_does_not_stamp_when_no_marker_present_for_terminal_or_lm() -> None:
    """Producer fail-closed: missing harness marker leaves confirmation_source at 'none'."""
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture
    report = _w19_5_build_log_record_report(
        "onTerminalShellIntegration",
        "onTerminalShellIntegration",
        secret,
        extension_host_output="",
        activated=[],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].confirmation_source == "none"
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"


# W19-6-followup-2: malformed log_record rejection. The existing
# ``test_w19_5_does_not_stamp_on_forged_nonce_for_language_model_tool``
# covers a *well-formed-but-wrong* nonce; this parametrized test pins the
# fail-closed behavior for *malformed* markers (missing nonce field,
# truncated nonce, invalid JSON after the harness prefix). A producer-side
# regression that loosened the nonce-shape gate would surface here.
@pytest.mark.parametrize(
    "malform_kind,extension_host_output",
    [
        (
            "missing_nonce_field",
            (
                "[extrace-harness] "
                + json.dumps(
                    {
                        "kind": "stimulus",
                        "phase": "complete",
                        "attempt_id": "harness",
                        "family": "onLanguageModelTool",
                        "activation_event": "onLanguageModelTool:foo",
                    }
                )
                + "\n"
            ),
        ),
        (
            "truncated_nonce",
            (
                "[extrace-harness] "
                + json.dumps(
                    {
                        "kind": "stimulus",
                        "phase": "complete",
                        "attempt_id": "harness",
                        "family": "onLanguageModelTool",
                        "activation_event": "onLanguageModelTool:foo",
                        "nonce": "abc",
                    }
                )
                + "\n"
            ),
        ),
        (
            "bad_json_after_prefix",
            "[extrace-harness] {not-valid-json}\n",
        ),
    ],
)
def test_w19_5_rejects_malformed_log_record_stamp(
    malform_kind: str, extension_host_output: str
) -> None:
    """Producer fail-closed: malformed harness markers stay at confirmation_source='none'."""
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture
    report = _w19_5_build_log_record_report(
        "onLanguageModelTool",
        "onLanguageModelTool:foo",
        secret,
        extension_host_output=extension_host_output,
        activated=[],
    )

    attempts = reconcile_event_attempts(report)

    assert attempts[0].confirmation_source == "none", (
        f"{malform_kind} should leave confirmation_source at 'none'"
    )
    assert attempts[0].failure_reason_code == "harness_verification_unconfirmed"


def test_w19_5_does_not_clobber_harness_nonce_stamp_on_on_debug() -> None:
    """Scope discipline: verified HMAC on onDebug stays harness_nonce, not log_record.

    The W19-5 elif branch must come *after* (not before) the W19-4
    onDebug branch — a future refactor that flips the order would
    silently demote onDebug's stronger confirmation strength.
    """
    secret = "secret-loaded-from-results-handshake"  # noqa: S105 — test fixture
    report = _w19_4_build_onDebug_report("onDebug", secret)

    attempts = reconcile_event_attempts(report)

    assert attempts[0].confirmation_source == "harness_nonce"


def test_w19_5_consumer_skips_failure_reason_code_when_log_record_stamped() -> None:
    """Consumer wire integration: stamped log_record attempts skip the unverified marker."""
    attempt = EventAttemptRecord(
        attempt_id="harness",
        declared_event="onLanguageModelTool",
        activation_event="onLanguageModelTool:foo",
        event_family="onLanguageModelTool",
        executor_action="harness:run_current_stimulus",
        confirmation_source="log_record",
    )

    _mark_unverified_harness_attempt(attempt, execution_closed=True)

    assert attempt.status == "attempted_only"
    assert attempt.verification_status == "attempted_only"
    assert attempt.failure_reason_code == ""
    assert any("harness_trace:harness" in str(item) for item in attempt.evidence)


def test_w19_5_consumer_sets_failure_reason_code_when_log_record_stays_none() -> None:
    """Consumer wire existing-behavior preservation: unstamped attempts still flag the reason."""
    attempt = EventAttemptRecord(
        attempt_id="harness",
        declared_event="onLanguageModelTool",
        activation_event="onLanguageModelTool:foo",
        event_family="onLanguageModelTool",
        executor_action="harness:run_current_stimulus",
        confirmation_source="none",
    )

    _mark_unverified_harness_attempt(attempt, execution_closed=True)

    assert attempt.status == "attempted_only"
    assert attempt.failure_reason_code == "harness_verification_unconfirmed"
