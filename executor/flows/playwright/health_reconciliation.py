"""Helpers for capability reconciliation and coverage verification."""

from __future__ import annotations

import json
import re
from typing import Any

from health_runtime_facts import (
    attempt_contracts as _attempt_contracts,
)
from health_runtime_facts import (
    is_harness_attempt as _is_harness_attempt,
)
from health_summary import derive_verified_capabilities

_HARNESS_MARKER_RE = re.compile(r"\[extrace-harness\]\s+(?P<payload>\{.*\})")


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
) -> bool:
    attempt_id = str(getattr(attempt, "attempt_id", "")).strip()
    if not attempt_id:
        return False
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
            attempt, harness_traces
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
