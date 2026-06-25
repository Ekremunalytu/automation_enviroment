"""Helpers for report summaries and serialization."""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from executor.runtime_fingerprint import executor_fingerprint
from packages.analysis_contracts import redact_secrets
from packages.analysis_contracts.contracts import (
    ACTIVATION_REPORT_SCHEMA_VERSION,
)
from packages.analysis_contracts.contracts import (
    ActivationReport as _ContractActivationReport,
)


class ReportContractError(RuntimeError):
    """Raised when the generated activation report violates the API contract.

    The executor catches drift between its in-memory dataclasses and the
    authoritative Pydantic contract in ``packages.analysis_contracts`` at the
    serialization boundary. Failing here means a misshapen report never gets
    written to disk and the analysis job fails loudly rather than silently
    producing a payload the API will reject.
    """


_EXECUTION_MODES = {
    "layered_passes",
    "selected_scenarios",
    "single_scenario",
    "all_scenarios",
    "skip_automation",
}

_SCENARIO_ZERO_REASON = (
    "No automation scenario was required for this non-executable fixture."
)


def _resolve_trigger_execution_mode(report: Any) -> str:
    explicit_mode = str(getattr(report, "trigger_execution_mode", "")).strip()
    if explicit_mode in _EXECUTION_MODES:
        return explicit_mode

    stimulus_passes = getattr(report, "stimulus_passes", []) or []
    if getattr(report, "trigger_plan_requested", False) and stimulus_passes:
        finalized: set[str] = set()
        for item in stimulus_passes:
            if hasattr(item, "status"):
                finalized.add(str(getattr(item, "status", "")).strip())
            elif isinstance(item, dict):
                finalized.add(str(item.get("status", "")).strip())
        if finalized & {"completed", "failed", "running"}:
            return "layered_passes"

    requested_scenarios = list(getattr(report, "requested_scenarios", []) or [])
    if getattr(report, "trigger_plan_requested", False) and requested_scenarios:
        return "selected_scenarios"

    scenarios_run = list(getattr(report, "scenarios_run", []) or [])
    if len(scenarios_run) == 1:
        return "single_scenario"
    return "all_scenarios"


def _run_quality_reasons(report: Any) -> list[str]:
    if _resolve_trigger_execution_mode(report) == "skip_automation":
        return [_SCENARIO_ZERO_REASON]
    reasons = getattr(report, "run_quality_reasons", [])
    return [str(reason) for reason in reasons if str(reason).strip()]


def _scenario_trace_names(report: Any) -> list[str]:
    traces = getattr(report, "scenario_traces", []) or []
    names = [
        str(trace.name) for trace in traces if str(getattr(trace, "name", "")).strip()
    ]
    if names:
        return names
    return [
        str(name)
        for name in getattr(report, "scenarios_run", []) or []
        if str(name).strip()
    ]


def _failed_scenario_names(report: Any) -> list[str]:
    traces = getattr(report, "scenario_traces", []) or []
    failed = [
        str(trace.name)
        for trace in traces
        if str(getattr(trace, "name", "")).strip()
        and str(getattr(trace, "status", "")).strip() == "failed"
    ]
    if failed or traces:
        return failed
    return [
        str(name)
        for name in getattr(report, "failed_scenarios", []) or []
        if str(name).strip()
    ]


def _skipped_scenario_records(report: Any) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in getattr(report, "skipped_scenarios", []) or []:
        name = str(getattr(item, "name", "")).strip()
        reason_code = str(getattr(item, "reason_code", "")).strip()
        detail = str(getattr(item, "detail", "")).strip()
        if not name or not reason_code or name in seen:
            continue
        seen.add(name)
        records.append(
            {
                "name": name,
                "reason_code": reason_code,
                "detail": detail,
            }
        )
    return records


def _skipped_scenario_names(report: Any) -> list[str]:
    return [
        str(item.get("name", "")).strip()
        for item in _skipped_scenario_records(report)
        if str(item.get("name", "")).strip()
    ]


def build_summary(
    report: Any,
    *,
    run_quality: str,
    automation_health: dict[str, Any],
    log_health: dict[str, Any],
    attribution_summary: dict[str, Any],
    risk_summary: dict[str, Any],
) -> dict[str, Any]:
    unique_ids = getattr(report, "activated_ids", set()) | getattr(
        report, "runtime_ids", set()
    )
    execution_mode = _resolve_trigger_execution_mode(report)
    scenarios_run = _scenario_trace_names(report)
    failed_scenarios = _failed_scenario_names(report)
    skipped_scenarios = _skipped_scenario_names(report)
    trigger_plan_applied = bool(
        getattr(report, "trigger_plan_applied", False)
    ) or not bool(getattr(report, "trigger_plan_requested", False))
    if execution_mode == "skip_automation":
        trigger_plan_applied = False
    return {
        "total_activated": len(getattr(report, "activated", [])),
        "unique_extensions": len(unique_ids),
        "unique_event_extensions": len(getattr(report, "activated_ids", set())),
        "running_extensions": len(getattr(report, "running_extensions", [])),
        "monitoring_duration_s": round(getattr(report, "duration_s", 0.0), 1),
        "monitoring_started_at": getattr(report, "monitoring_start", 0.0),
        "monitoring_ended_at": getattr(report, "monitoring_end", 0.0),
        "extension_ids": sorted(unique_ids),
        "scenarios_run": scenarios_run,
        "failed_scenarios": failed_scenarios,
        "skipped_scenarios": skipped_scenarios,
        "network_events": len(getattr(report, "network_events", [])),
        "network_hosts": len(getattr(report, "network_hosts", set())),
        "file_events": len(getattr(report, "file_events", [])),
        "sensitive_file_events": len(getattr(report, "sensitive_file_events", [])),
        "target_file_events": len(getattr(report, "target_file_events", [])),
        "target_network_events": len(getattr(report, "target_network_events", [])),
        "attempted_capabilities": getattr(
            report, "runtime_official_attempted_capabilities", []
        ),
        "verified_capabilities": getattr(report, "official_verified_capabilities", []),
        "official_attempted_capabilities": getattr(
            report,
            "runtime_official_attempted_capabilities",
            [],
        ),
        "official_verified_capabilities": getattr(
            report,
            "official_verified_capabilities",
            [],
        ),
        "heuristic_attempted_capabilities": getattr(
            report,
            "runtime_heuristic_attempted_capabilities",
            [],
        ),
        "heuristic_verified_capabilities": getattr(
            report,
            "supported_heuristic_verified_capabilities",
            [],
        ),
        "ui_blocker_count": len(getattr(report, "ui_blocker_entries", [])),
        "target_extension_expected": getattr(report, "target_extension_id", ""),
        "target_extension_observed": getattr(
            report, "target_extension_observed", False
        ),
        "official_event_coverage": getattr(report, "official_event_coverage", {}),
        "heuristic_workflow_coverage": getattr(
            report,
            "heuristic_workflow_coverage",
            {},
        ),
        "trigger_execution_mode": execution_mode,
        "trigger_plan_applied": trigger_plan_applied,
        "verification_gap": getattr(report, "verification_gap", 0),
        "heuristic_verification_gap": getattr(report, "heuristic_verification_gap", 0),
        "run_quality": run_quality,
        "automation_health": automation_health,
        "log_health": log_health,
        "attribution_summary": attribution_summary,
        "risk_summary": risk_summary,
        "signal_summary": getattr(report, "signal_summary", {}),
    }


def _expand_window_for_orphaned_pem(raw_lines: list[str], start: int) -> int:
    """Walk ``start`` backwards to include the ``BEGIN PRIVATE KEY``
    marker if the first PEM marker inside the retained tail is an
    ``END`` without a preceding ``BEGIN``. Without this, the
    ``private_key`` regex in ``packages.analysis_contracts.evidence``
    (a multi-line ``BEGIN…END`` span) cannot collapse the orphaned
    body and raw key bytes would persist. Idempotent when the tail
    window is well-formed.
    """
    if start <= 0:
        return 0
    in_pem = False
    for i in range(start, len(raw_lines)):
        line = raw_lines[i]
        if "-----BEGIN" in line and "PRIVATE KEY-----" in line:
            in_pem = True
        elif "-----END" in line and "PRIVATE KEY-----" in line:
            if not in_pem:
                for j in range(start - 1, -1, -1):
                    candidate = raw_lines[j]
                    if "-----BEGIN" in candidate and "PRIVATE KEY-----" in candidate:
                        return j
                return start
            in_pem = False
    return start


def build_report_data(
    report: Any,
    *,
    evidence_events: list[Any],
    evidence_links: list[Any],
    risk_signals: list[Any],
    risk_summary: dict[str, Any],
    run_quality: str,
    automation_health: dict[str, Any],
    log_health: dict[str, Any],
    attribution_summary: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    # Tail window first, redaction second. Computing the cap on the
    # raw line stream — not on the post-redaction stream — defeats a
    # ``fake-PEM tail-inflation`` attack: an extension that wraps
    # thousands of attacker-controlled ``console.log`` lines in
    # ``-----BEGIN/END PRIVATE KEY-----`` markers would otherwise see
    # the redaction collapse the span to a single token, slip the
    # 500-line cap, and leak older log lines that lived BEFORE the
    # original tail window. (Codex review #3, 2026-05-05.)
    #
    # The orphaned-PEM body bug — body lines retained in the tail
    # while their ``BEGIN`` marker falls outside it, leaving the
    # ``private_key`` BEGIN/END span unmatched — is closed by walking
    # the window start back to include the originating ``BEGIN``
    # before redaction runs. Single-line secret classes (``aws`` /
    # ``bearer`` / ``db_url`` / ``api_key``) do not change line count
    # so they are unaffected by either layer.
    raw_eh = str(getattr(report, "extension_host_output", ""))
    raw_lines = raw_eh.splitlines()
    if len(raw_lines) > 500:
        start = _expand_window_for_orphaned_pem(raw_lines, len(raw_lines) - 500)
        # Reattach the trailing newline (``splitlines()`` drops it) so
        # the truncated branch round-trips the same trailing-byte form
        # the short-input branch already preserves.
        window = "\n".join(raw_lines[start:])
        if raw_eh.endswith("\n"):
            window += "\n"
        eh_text = redact_secrets(window)
    else:
        eh_text = redact_secrets(raw_eh)
    execution_mode = _resolve_trigger_execution_mode(report)
    failed_scenarios = _failed_scenario_names(report)
    skipped_scenarios = _skipped_scenario_records(report)
    trigger_plan_applied = bool(
        getattr(report, "trigger_plan_applied", False)
    ) or not bool(getattr(report, "trigger_plan_requested", False))
    if execution_mode == "skip_automation":
        trigger_plan_applied = False

    return {
        "schema_version": ACTIVATION_REPORT_SCHEMA_VERSION,
        "report_version": getattr(report, "report_version", 2),
        "target_extension_expected": getattr(report, "target_extension_id", ""),
        # W16-3: analyst-facing top-level alias (same string value as
        # ``target_extension_expected``; downstream readers had been
        # blocked on the absence of this canonical name).
        "target_extension_id": getattr(report, "target_extension_id", ""),
        "target_extension_observed": getattr(
            report, "target_extension_observed", False
        ),
        # W16-3: top-level field sync drift closeout — surface the
        # in-memory ``ActivationReport`` scalars that
        # ``MonitorRuntime.start()``/``.stop()`` stamp on entry/exit and
        # that ``dispatch.setup_monitor`` flips True for any monitored
        # run. Pre-W16-3 these were dropped at the strict-forbid
        # contract validation seam (no slot on
        # ``packages/analysis_contracts/contracts.ActivationReport``),
        # so downstream analyzers reading the top-level fields saw them
        # as missing/null even with evidence present.
        "monitoring_start": float(getattr(report, "monitoring_start", 0.0) or 0.0),
        "monitoring_end": float(getattr(report, "monitoring_end", 0.0) or 0.0),
        "scenarios_run": list(getattr(report, "scenarios_run", []) or []),
        "harness_handshake_required": bool(
            getattr(report, "harness_handshake_required", False)
        ),
        "trigger_plan_requested": bool(
            getattr(report, "trigger_plan_requested", False)
        ),
        "trigger_plan_loaded": bool(getattr(report, "trigger_plan_loaded", False)),
        "trigger_plan_applied": trigger_plan_applied,
        "trigger_plan_path": getattr(report, "trigger_plan_path", ""),
        "trigger_execution_mode": execution_mode,
        "requested_scenarios": getattr(report, "requested_scenarios", []),
        "failed_scenarios": failed_scenarios,
        "skipped_scenarios": skipped_scenarios,
        "extra_trigger_failures": getattr(report, "extra_trigger_failures", []),
        "verification_gap": getattr(report, "verification_gap", 0),
        "heuristic_verification_gap": getattr(report, "heuristic_verification_gap", 0),
        "run_quality": run_quality,
        "run_quality_reasons": _run_quality_reasons(report),
        "automation_health": automation_health,
        "log_health": log_health,
        "attribution_summary": attribution_summary,
        "risk_signals": [asdict(signal) for signal in risk_signals],
        "risk_summary": risk_summary,
        "signal_summary": getattr(report, "signal_summary", {}),
        "summary": summary,
        "attempted_capabilities": getattr(
            report, "runtime_official_attempted_capabilities", []
        ),
        "verified_capabilities": getattr(report, "official_verified_capabilities", []),
        "official_attempted_capabilities": getattr(
            report,
            "runtime_official_attempted_capabilities",
            [],
        ),
        "official_verified_capabilities": getattr(
            report,
            "official_verified_capabilities",
            [],
        ),
        "heuristic_attempted_capabilities": getattr(
            report,
            "runtime_heuristic_attempted_capabilities",
            [],
        ),
        "heuristic_verified_capabilities": getattr(
            report,
            "supported_heuristic_verified_capabilities",
            [],
        ),
        "network_capture_error": getattr(report, "network_capture_error", ""),
        "file_capture_error": getattr(report, "file_capture_error", ""),
        "file_capture_diagnostics": getattr(report, "file_capture_diagnostics", {}),
        "activated": [asdict(e) for e in getattr(report, "activated", [])],
        "running_extensions": [
            asdict(e) for e in getattr(report, "running_extensions", [])
        ],
        "network_events": [asdict(e) for e in getattr(report, "network_events", [])],
        "file_events": [asdict(e) for e in getattr(report, "file_events", [])],
        "process_events": [asdict(e) for e in getattr(report, "process_events", [])],
        "output_signal_events": [
            asdict(e) for e in getattr(report, "output_signal_events", [])
        ],
        "scenario_traces": [asdict(e) for e in getattr(report, "scenario_traces", [])],
        "stimulus_passes": [asdict(e) for e in getattr(report, "stimulus_passes", [])],
        "prerequisite_results": [
            asdict(e) for e in getattr(report, "prerequisite_results", [])
        ],
        "event_attempts": [asdict(e) for e in getattr(report, "event_attempts", [])],
        "evidence_events": [asdict(e) for e in evidence_events],
        "evidence_links": [asdict(e) for e in evidence_links],
        "network_summary": getattr(report, "network_summary", {}),
        "file_summary": getattr(report, "file_summary", {}),
        "coverage_summary": getattr(report, "coverage_summary", {}),
        "coverage_matrix": getattr(report, "coverage_matrix", []),
        "coverage_tracks": getattr(report, "coverage_tracks", {}),
        "official_event_coverage": getattr(report, "official_event_coverage", {}),
        "heuristic_workflow_coverage": getattr(
            report,
            "heuristic_workflow_coverage",
            {},
        ),
        "log_streams": {
            stream: [asdict(entry) for entry in entries]
            for stream, entries in getattr(report, "log_streams", {}).items()
        },
        "extension_host_output_lines": raw_eh.count("\n"),
        "extension_host_output": eh_text,
        "log_file": getattr(report, "log_file_path", ""),
        # W11-3: producer-set fields surface here so the disk write
        # carries the runtime values. The contract defaults survive when
        # callers (e.g. report-only ingest) skip the producer setters.
        "activation_discovery_strategy_outcomes": dict(
            getattr(report, "activation_discovery_strategy_outcomes", {})
        ),
        "runner_exit_code": getattr(report, "runner_exit_code", None),
        "runner_status": getattr(report, "runner_status", "unknown"),
        # W14-5 sub-commit 3 ([FOLLOWUP codex-automation-5]): executor
        # build fingerprint at automation output boundary. Cached after
        # first resolve; subsequent writes during the same process
        # lifetime return the cached dict without re-running `git`.
        "executor_fingerprint": executor_fingerprint(),
        # W26 / Stream 3 (B5): the analyzed .vsix SHA-256 threaded in via
        # ``--vsix-sha256`` and carried on the in-memory report. Stamped here so
        # the dynamic report on disk is bound to the exact bytes scanned.
        "vsix_sha256": getattr(report, "vsix_sha256", ""),
    }


def _validate_report_against_contract(
    data: dict[str, Any],
) -> _ContractActivationReport:
    try:
        return _ContractActivationReport.model_validate(data)
    except ValidationError as err:
        first = err.errors()[0]
        loc = ".".join(str(part) for part in first.get("loc", ()))
        msg = first.get("msg", "invalid")
        raise ReportContractError(
            f"Activation report failed contract validation at {loc or '<root>'}: {msg}"
        ) from err


def save_report_payload(
    path: str | Path,
    data: dict[str, Any],
    *,
    announce: bool = True,
    logger: Any | None = None,
) -> Path:
    # W10-FIXUP-1: persist the parsed-and-dumped payload, not the caller's
    # input dict. The before-validators on ActivationReport (schema_version
    # injection, legacy verdict migration) only mutate the parsed model;
    # writing the original dict would leak those gaps to disk.
    parsed = _validate_report_against_contract(data)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        parsed.model_dump(mode="json"), indent=2, ensure_ascii=False
    )
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=out.parent,
        prefix=f".{out.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(serialized)
        temp_out = Path(handle.name)
    temp_out.replace(out)
    if announce and logger is not None:
        logger(f"Report saved to {out}")
    return out
