"""Helpers for report summaries and serialization."""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

_EXECUTION_MODES = {
    "layered_passes",
    "selected_scenarios",
    "single_scenario",
    "all_scenarios",
}


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
    reasons = getattr(report, "run_quality_reasons", [])
    return [str(reason) for reason in reasons if str(reason).strip()]


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
    return {
        "total_activated": len(getattr(report, "activated", [])),
        "unique_extensions": len(unique_ids),
        "unique_event_extensions": len(getattr(report, "activated_ids", set())),
        "running_extensions": len(getattr(report, "running_extensions", [])),
        "monitoring_duration_s": round(getattr(report, "duration_s", 0.0), 1),
        "monitoring_started_at": getattr(report, "monitoring_start", 0.0),
        "monitoring_ended_at": getattr(report, "monitoring_end", 0.0),
        "extension_ids": sorted(unique_ids),
        "scenarios_run": getattr(report, "scenarios_run", []),
        "failed_scenarios": getattr(report, "failed_scenarios", []),
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
        "trigger_plan_applied": bool(getattr(report, "trigger_plan_applied", False))
        or not bool(getattr(report, "trigger_plan_requested", False)),
        "verification_gap": getattr(report, "verification_gap", 0),
        "heuristic_verification_gap": getattr(report, "heuristic_verification_gap", 0),
        "run_quality": run_quality,
        "automation_health": automation_health,
        "log_health": log_health,
        "attribution_summary": attribution_summary,
        "risk_summary": risk_summary,
        "verdict": getattr(report, "verdict", {}),
    }


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
    eh_lines = str(getattr(report, "extension_host_output", "")).splitlines()
    if len(eh_lines) > 500:
        eh_text = "\n".join(eh_lines[-500:])
    else:
        eh_text = str(getattr(report, "extension_host_output", ""))
    execution_mode = _resolve_trigger_execution_mode(report)

    return {
        "report_version": getattr(report, "report_version", 2),
        "target_extension_expected": getattr(report, "target_extension_id", ""),
        "target_extension_observed": getattr(
            report, "target_extension_observed", False
        ),
        "trigger_plan_requested": bool(
            getattr(report, "trigger_plan_requested", False)
        ),
        "trigger_plan_loaded": bool(getattr(report, "trigger_plan_loaded", False)),
        "trigger_plan_applied": bool(getattr(report, "trigger_plan_applied", False))
        or not bool(getattr(report, "trigger_plan_requested", False)),
        "trigger_plan_path": getattr(report, "trigger_plan_path", ""),
        "trigger_execution_mode": execution_mode,
        "requested_scenarios": getattr(report, "requested_scenarios", []),
        "failed_scenarios": getattr(report, "failed_scenarios", []),
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
        "verdict": getattr(report, "verdict", {}),
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
        "extension_host_output_lines": str(
            getattr(report, "extension_host_output", "")
        ).count("\n"),
        "extension_host_output": eh_text,
        "log_file": getattr(report, "log_file_path", ""),
    }


def save_report_payload(
    path: str | Path,
    data: dict[str, Any],
    *,
    announce: bool = True,
    logger: Any | None = None,
) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(data, indent=2, ensure_ascii=False)
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
