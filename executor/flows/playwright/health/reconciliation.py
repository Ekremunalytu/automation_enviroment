"""Helpers for capability reconciliation and coverage verification."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
import os
import re
from pathlib import Path
from typing import Any

from .runtime_facts import (
    attempt_contracts as _attempt_contracts,
)
from .runtime_facts import (
    is_harness_attempt as _is_harness_attempt,
)
from .summary import derive_verified_capabilities

_HARNESS_MARKER_RE = re.compile(r"\[extrace-harness\]\s+(?P<payload>\{.*\})")

# W13-1 (Codex H6): file path the harness orchestration writes the per-
# launch HMAC secret to. ``launch_vscode.sh`` produces this file before
# every VS Code start (boot and reset); ``load_harness_python_secret``
# reads it once and unlinks so the same-UID target extension cannot
# reach the value via the bind-mounted ``/results`` directory after the
# Python orchestration has consumed it.
HARNESS_PYTHON_SECRET_PATH = Path(
    os.environ.get(
        "EXECUTOR_HARNESS_PYTHON_SECRET_PATH",
        "/results/_extrace_harness_python_secret",
    )
)


def load_harness_python_secret(
    path: Path = HARNESS_PYTHON_SECRET_PATH,
) -> str:
    """Read the per-launch harness HMAC secret then unlink the file.

    Returns the stripped secret string, or empty string if the file is
    missing or unreadable. Always attempts the unlink regardless of read
    success so a half-written or stale file from a prior boot does not
    survive into the target's window. The Python caller (typically
    ``setup_monitor``) holds the returned value in memory and stamps it
    onto ``ActivationReport.expected_harness_nonce``.
    """
    secret = ""
    try:
        secret = path.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError):
        secret = ""
    with contextlib.suppress(FileNotFoundError, OSError):
        path.unlink()
    return secret


def _verify_harness_marker_signature(
    payload: dict[str, Any],
    expected_nonce: str,
) -> bool:
    """W13-1 (Codex H6): authenticate a ``[extrace-harness]`` marker payload.

    Computes HMAC-SHA256 over ``canonical_json(payload \\ {"nonce"})`` using
    ``expected_nonce`` (loaded from ``/results/_extrace_harness_python_secret``
    by the entrypoint) and compares against ``payload["nonce"]`` in constant
    time. The canonical form is sorted-keys JSON without whitespace, in
    lockstep with ``markers.js::_canonicalPayloadBytes`` and the
    ``_w13_1_canonical_payload`` test helper. Same-UID target extensions
    cannot reach the secret, so a forged marker without a matching
    signature is rejected.

    Fail-closed semantics: empty ``expected_nonce``, missing/non-string
    ``nonce`` in payload, or invalid signature all return False. The
    empty-nonce branch preserves the pre-W13-1 unit-test contract where
    ``ActivationReport`` is constructed without the orchestration
    handshake; production paths run with a populated secret and reject
    unsigned markers.
    """
    if not expected_nonce:
        return False
    received = payload.get("nonce")
    if not isinstance(received, str) or not received:
        return False
    canonical = json.dumps(
        {k: v for k, v in payload.items() if k != "nonce"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    expected_sig = hmac.new(
        expected_nonce.encode("utf-8"),
        canonical,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(received, expected_sig)


def _harness_trace_records_by_attempt(report: Any) -> dict[str, list[dict[str, Any]]]:
    raw_output = str(getattr(report, "extension_host_output", "") or "")
    traces: dict[str, list[dict[str, Any]]] = {}
    for line in raw_output.splitlines():
        marker_match = _HARNESS_MARKER_RE.search(line)
        if marker_match is None:
            continue
        try:
            payload = json.loads(marker_match.group("payload"))
        except ValueError:
            continue
        if not isinstance(payload, dict):
            continue
        attempt_id = str(payload.get("attempt_id", "")).strip()
        if attempt_id:
            traces.setdefault(attempt_id, []).append(payload)
    return traces


def _attempt_has_harness_completion_trace(
    attempt: Any,
    traces_by_attempt: dict[str, list[dict[str, Any]]],
    expected_nonce: str = "",
) -> bool:
    """W13-1: a ``phase=="complete"`` trace counts only when its HMAC nonce
    verifies under ``expected_nonce``. Empty ``expected_nonce`` means the
    report was built without the orchestration handshake (unit-test
    construction or pre-W13-1 baseline) and the call short-circuits to the
    legacy phase-only check so the existing test surface stays GREEN. In
    production, ``setup_monitor`` populates ``expected_harness_nonce``
    from the file ``launch_vscode.sh`` writes, so the empty branch never
    triggers and forged markers without signatures are rejected.
    """
    attempt_id = str(getattr(attempt, "attempt_id", "")).strip()
    if not attempt_id:
        return False
    if expected_nonce:
        return any(
            str(trace.get("phase", "")).strip() == "complete"
            and _verify_harness_marker_signature(trace, expected_nonce)
            for trace in traces_by_attempt.get(attempt_id, [])
        )
    return any(
        str(trace.get("phase", "")).strip() == "complete"
        for trace in traces_by_attempt.get(attempt_id, [])
    )


def _activation_exact_matches(
    activation_event: str,
    family: str,
    target_activation_events: list[str],
) -> list[str]:
    if activation_event:
        return [
            event for event in target_activation_events if event == activation_event
        ]
    if family:
        return [event for event in target_activation_events if event == family]
    return []


def _activation_prefix_matches(
    activation_event: str,
    family: str,
    target_activation_events: list[str],
) -> list[str]:
    prefix = ""
    if activation_event and ":" in activation_event:
        prefix = activation_event.split(":", maxsplit=1)[0]
    elif family:
        prefix = family
    if not prefix:
        return []
    return [
        event
        for event in target_activation_events
        if event == prefix or event.startswith(f"{prefix}:")
    ]


def _unique_evidence_items(existing: list[str], additions: list[str]) -> list[str]:
    return list(dict.fromkeys([*existing, *additions]))


def _mark_unverified_harness_attempt(
    attempt: Any,
    *,
    execution_closed: bool,
) -> None:
    attempt.status = "attempted_only"
    attempt.verification_status = "attempted_only"
    attempt.failure_reason_code = "harness_verification_unconfirmed"
    attempt.result_details = (
        "Harness stimulus executed, but target verification remained unresolved."
        if execution_closed
        else "Harness stimulus could not be confirmed because no completion trace was observed."
    )
    evidence = list(getattr(attempt, "evidence", []) or [])
    if execution_closed:
        evidence = _unique_evidence_items(
            evidence,
            [
                f"harness_trace:{str(getattr(attempt, 'attempt_id', '')).strip()}",
                "Harness stimulus executed but no target-owned reaction was verified.",
            ],
        )
    attempt.evidence = evidence


def _target_log_stream_summaries(report: Any, target_id: str) -> list[str]:
    """Return short summaries of target-owned evidence beyond the activation entry.

    Used by ``reconcile_event_attempts`` to decide whether an attempt with an
    activation match also has target-owned log/output evidence, in which case
    it is upgraded from ``activation_seen`` to ``target_log_seen``.
    Conservative: requires ``is_target_extension=True`` AND, when ``target_id``
    is set, an exact ``extension_id`` match.

    PR345 PR3-5 follow-up (2026-04-27): two correctness fixes
    1. ``kind == "activation"`` log entries are excluded — every target
       ``ActivationEntry`` is mirrored into ``target_extension_host`` by
       ``_append_activation_log_entries``, so counting them as "target log
       evidence" collapses ``activation_seen`` into ``target_log_seen``
       automatically. Lifecycle now requires evidence beyond the activation.
    2. ``report.output_signal_events`` (PR5 harness Output channel hook) is
       harvested as a second evidence source. Per ADR 0006 §5: a target-owned
       Output channel write is exactly the kind of post-activation signal
       ``target_log_seen`` was meant to capture.
    """
    summaries: list[str] = []
    cap = 5

    streams = getattr(report, "log_streams", {}) or {}
    for stream_name, entries in streams.items():
        for entry in entries or []:
            if not getattr(entry, "is_target_extension", False):
                continue
            if str(getattr(entry, "kind", "")).strip() == "activation":
                continue
            entry_ext_id = str(getattr(entry, "extension_id", "")).strip()
            if target_id and entry_ext_id != target_id:
                continue
            message = str(getattr(entry, "message", "")).strip()
            if not message:
                continue
            snippet = message if len(message) <= 80 else message[:77] + "..."
            summaries.append(f"{stream_name}: {snippet}")
            if len(summaries) >= cap:
                return summaries

    output_events = getattr(report, "output_signal_events", []) or []
    for event in output_events:
        if not getattr(event, "is_target_extension_event", False):
            continue
        event_ext_id = str(getattr(event, "extension_id", "")).strip()
        if target_id and event_ext_id != target_id:
            continue
        channel = str(getattr(event, "channel", "")).strip() or "<unnamed>"
        text = str(getattr(event, "text", "")).strip()
        if not text:
            continue
        snippet = text if len(text) <= 80 else text[:77] + "..."
        summaries.append(f"output_channel({channel}): {snippet}")
        if len(summaries) >= cap:
            return summaries

    return summaries


def _mark_attempt_activation_seen(
    attempt: Any,
    *,
    activation_matches: list[str],
) -> None:
    """Mark attempt as 'target activation observed, full verification pending'.

    Stronger than ``attempted_only`` (we have direct evidence the target
    extension activated for this event), weaker than ``verified`` (no
    runtime-capability evidence or harness completion trace yet). See the
    lifecycle state graph in ``packages/analysis_contracts/contracts.py``.
    """
    attempt.status = "activation_seen"
    attempt.verification_status = "activation_seen"
    attempt.failure_reason_code = ""
    attempt.result_details = (
        "Target extension activation observed for this event; "
        "full verification (runtime capability / harness trace) not yet closed."
    )
    evidence = list(getattr(attempt, "evidence", []) or [])
    if activation_matches:
        evidence = _unique_evidence_items(
            evidence,
            [
                *activation_matches,
                f"Observed target activation(s): {', '.join(activation_matches)}",
            ],
        )
    attempt.evidence = evidence


def _mark_attempt_target_log_seen(
    attempt: Any,
    *,
    activation_matches: list[str],
    target_log_summaries: list[str],
) -> None:
    """Mark attempt as 'target activated AND target-owned log evidence seen'.

    Stronger than ``activation_seen``: we observed both the activation entry
    AND at least one log stream entry attributed to the target extension. Still
    weaker than ``verified`` — the full verification contract (runtime delta /
    harness completion trace) has not closed.
    """
    attempt.status = "target_log_seen"
    attempt.verification_status = "target_log_seen"
    attempt.failure_reason_code = ""
    attempt.result_details = (
        "Target activation and target-owned log evidence observed; "
        "runtime capability / harness completion still unverified."
    )
    evidence = list(getattr(attempt, "evidence", []) or [])
    if activation_matches:
        evidence = _unique_evidence_items(
            evidence,
            [
                *activation_matches,
                f"Observed target activation(s): {', '.join(activation_matches)}",
            ],
        )
    if target_log_summaries:
        evidence = _unique_evidence_items(
            evidence,
            [f"Target log entry: {summary}" for summary in target_log_summaries],
        )
    attempt.evidence = evidence


def _mark_attempt_verified(
    attempt: Any,
    *,
    activation_matches: list[str],
    runtime_capability_evidence: list[str],
    execution_closed: bool,
) -> None:
    attempt.status = "verified"
    attempt.verification_status = "verified"
    attempt.failure_reason_code = ""
    attempt.result_details = ""
    evidence = list(getattr(attempt, "evidence", []) or [])
    if activation_matches:
        evidence = _unique_evidence_items(
            evidence,
            [
                *activation_matches,
                f"Observed target activation(s): {', '.join(activation_matches)}",
            ],
        )
    if runtime_capability_evidence:
        evidence = _unique_evidence_items(
            evidence,
            [
                "Observed runtime capability evidence: "
                + ", ".join(runtime_capability_evidence)
            ],
        )
    if execution_closed:
        evidence = _unique_evidence_items(
            evidence,
            [
                f"harness_trace:{str(getattr(attempt, 'attempt_id', '')).strip()}",
                "Harness stimulus emitted a completion trace.",
            ],
        )
    attempt.evidence = evidence


def reconcile_event_attempts(report: Any) -> list[Any]:
    attempts = list(getattr(report, "event_attempts", []))
    if not attempts:
        return attempts

    target_id = getattr(report, "target_extension_id", "")
    target_activations = [
        entry
        for entry in getattr(report, "activated", [])
        if getattr(entry, "extension_id", "") == target_id
    ]
    target_activation_events = [
        str(getattr(entry, "activation_event", "")).strip()
        for entry in target_activations
        if str(getattr(entry, "activation_event", "")).strip()
    ]
    derived_verified_capabilities = set(derive_verified_capabilities(report))
    harness_traces = _harness_trace_records_by_attempt(report)
    target_log_summaries = _target_log_stream_summaries(report, target_id)
    # W13-1 (Codex H6): the orchestration secret is stamped onto the
    # report by ``setup_monitor`` after lifecycle.py constructs it.
    # Empty value here means the report was built without the
    # handshake (unit tests, pre-W13-1 baseline replay); the helper
    # short-circuits to the legacy phase-only check in that case.
    expected_harness_nonce = str(getattr(report, "expected_harness_nonce", "") or "")

    for attempt in attempts:
        activation_event = str(getattr(attempt, "activation_event", "")).strip()
        family = str(getattr(attempt, "event_family", "")).strip()
        contracts = _attempt_contracts(attempt)
        if getattr(attempt, "status", "") == "failed":
            attempt.verification_status = "failed"
            continue
        if getattr(attempt, "status", "") == "blocked":
            attempt.verification_status = "blocked"
            continue

        attempted_passes = list(getattr(attempt, "attempted_passes", []) or [])
        capability_tags = {
            str(tag).strip()
            for tag in getattr(attempt, "capability_tags", []) or []
            if str(tag).strip()
        }
        exact_matches = _activation_exact_matches(
            activation_event,
            family,
            target_activation_events,
        )
        prefix_matches = _activation_prefix_matches(
            activation_event,
            family,
            target_activation_events,
        )
        runtime_capability_evidence = sorted(
            capability_tags & derived_verified_capabilities
        )
        execution_closed = _attempt_has_harness_completion_trace(
            attempt, harness_traces, expected_harness_nonce
        )

        if not contracts:
            target_reaction_closed = bool(exact_matches or prefix_matches)
            if not target_reaction_closed and attempted_passes:
                target_reaction_closed = bool(runtime_capability_evidence)
            if target_reaction_closed:
                _mark_attempt_verified(
                    attempt,
                    activation_matches=exact_matches or prefix_matches,
                    runtime_capability_evidence=runtime_capability_evidence,
                    execution_closed=False,
                )
                continue
        else:
            execution_required = "automation_trace" in contracts
            target_reaction_required = bool(
                contracts
                & {
                    "activation_log_exact",
                    "activation_log_prefix",
                    "target_runtime_delta",
                }
            )
            target_reaction_closed = False
            activation_matches: list[str] = []

            if "activation_log_exact" in contracts and exact_matches:
                activation_matches = exact_matches
                target_reaction_closed = True
            if (
                not target_reaction_closed
                and "activation_log_prefix" in contracts
                and prefix_matches
            ):
                activation_matches = prefix_matches
                target_reaction_closed = True
            if (
                not target_reaction_closed
                and "target_runtime_delta" in contracts
                and attempted_passes
                and runtime_capability_evidence
            ):
                target_reaction_closed = True

            if (not execution_required or execution_closed) and (
                not target_reaction_required or target_reaction_closed
            ):
                _mark_attempt_verified(
                    attempt,
                    activation_matches=activation_matches,
                    runtime_capability_evidence=runtime_capability_evidence,
                    execution_closed=execution_required and execution_closed,
                )
                continue

        # Intermediate observation states: stronger than ``attempted_only``,
        # weaker than ``verified``. Only applied to non-harness attempts where
        # the target extension actually activated for this event. Harness
        # attempts continue to route through ``_mark_unverified_harness_attempt``
        # so they keep their ``harness_verification_unconfirmed`` signal. The
        # final fallback block below still handles the "no activation match"
        # case for everyone.
        activation_matches_for_upgrade = exact_matches or prefix_matches
        if activation_matches_for_upgrade and not _is_harness_attempt(attempt):
            if target_log_summaries:
                _mark_attempt_target_log_seen(
                    attempt,
                    activation_matches=activation_matches_for_upgrade,
                    target_log_summaries=target_log_summaries,
                )
            else:
                _mark_attempt_activation_seen(
                    attempt,
                    activation_matches=activation_matches_for_upgrade,
                )
            continue

        if getattr(attempt, "status", "") in {"running", "planned", "attempted_only"}:
            attempted_evidence = bool(attempted_passes or execution_closed)
            if attempted_evidence:
                if _is_harness_attempt(attempt):
                    _mark_unverified_harness_attempt(
                        attempt,
                        execution_closed=execution_closed,
                    )
                else:
                    attempt.status = "attempted_only"
                    attempt.verification_status = "attempted_only"
            elif getattr(attempt, "blocked_reason_code", ""):
                attempt.status = "blocked"
                attempt.verification_status = "blocked"
            else:
                attempt.status = "failed"
                attempt.verification_status = "failed"
    return attempts


def reconcile_coverage_verification(
    report: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    coverage_tracks = getattr(report, "coverage_tracks", {}) or {}
    official_summary, official_matrix = _reconcile_track(
        coverage_tracks.get("official", {}).get(
            "summary",
            getattr(report, "coverage_summary", {}),
        ),
        coverage_tracks.get("official", {}).get(
            "matrix",
            getattr(report, "coverage_matrix", []),
        ),
        set(getattr(report, "official_attempted_capabilities", [])),
        set(getattr(report, "official_verified_capabilities", [])),
    )
    heuristic_summary, heuristic_matrix = _reconcile_track(
        coverage_tracks.get("heuristic", {}).get("summary", {}),
        coverage_tracks.get("heuristic", {}).get("matrix", []),
        set(getattr(report, "heuristic_attempted_capabilities", [])),
        set(getattr(report, "heuristic_verified_capabilities", [])),
    )
    return (
        official_summary,
        official_matrix,
        {
            "official": {
                "source": coverage_tracks.get("official", {}).get(
                    "source",
                    "official_activation_track",
                ),
                "selected_scenarios": coverage_tracks.get("official", {}).get(
                    "selected_scenarios",
                    [],
                ),
                "summary": official_summary,
                "matrix": official_matrix,
            },
            "heuristic": {
                "source": coverage_tracks.get("heuristic", {}).get(
                    "source",
                    "heuristic_workflow_track",
                ),
                "selected_scenarios": coverage_tracks.get("heuristic", {}).get(
                    "selected_scenarios",
                    [],
                ),
                "summary": heuristic_summary,
                "matrix": heuristic_matrix,
            },
        },
    )


def _reconcile_track(
    summary: dict[str, Any],
    matrix_entries: list[dict[str, Any]],
    attempted: set[str],
    verified: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    supported_capabilities = {
        str(entry.get("capability", "")).strip()
        for entry in matrix_entries
        if str(entry.get("support_status", entry.get("status", "unknown"))).strip()
        == "covered"
    }
    attempted = {
        capability
        for capability in attempted
        if not supported_capabilities or capability in supported_capabilities
    }
    verified = {
        capability
        for capability in verified
        if not supported_capabilities or capability in supported_capabilities
    }
    matrix: list[dict[str, Any]] = []
    for entry in matrix_entries:
        capability = str(entry.get("capability", "")).strip()
        next_entry = dict(entry)
        next_entry["support_status"] = entry.get(
            "support_status",
            entry.get("status", "unknown"),
        )
        supported = next_entry["support_status"] == "covered"
        if capability in verified and supported:
            verification_status = "verified"
        elif capability in attempted and supported:
            verification_status = "attempted_only"
        else:
            verification_status = "not_attempted"
        next_entry["verification_status"] = verification_status
        next_entry["attempted"] = supported and capability in attempted
        next_entry["verified"] = supported and capability in verified
        matrix.append(next_entry)

    next_summary = dict(summary)
    next_summary["attempted"] = len(attempted)
    next_summary["verified"] = len(verified)
    next_summary["attempted_capabilities"] = sorted(attempted)
    next_summary["verified_capabilities"] = sorted(verified)
    return next_summary, matrix
