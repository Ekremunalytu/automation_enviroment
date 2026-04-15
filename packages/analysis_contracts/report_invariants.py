"""Helpers for validating exported activation-report invariants."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def scenario_trace_names(payload: Mapping[str, Any]) -> list[str]:
    traces = _mapping_list(payload.get("scenario_traces"))
    return [
        str(item.get("name", "")).strip()
        for item in traces
        if str(item.get("name", "")).strip()
    ]


def _failed_trace_names(payload: Mapping[str, Any]) -> list[str]:
    traces = _mapping_list(payload.get("scenario_traces"))
    return [
        str(item.get("name", "")).strip()
        for item in traces
        if str(item.get("name", "")).strip()
        and str(item.get("status", "")).strip() == "failed"
    ]


def _attempt_mappings(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return _mapping_list(payload.get("event_attempts"))


def _pass_mappings(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return _mapping_list(payload.get("stimulus_passes"))


def _scenario_action_name(attempt: Mapping[str, Any]) -> str:
    action = str(attempt.get("executor_action", "")).strip()
    if not action.startswith("scenario:"):
        return ""
    return action.split(":", maxsplit=1)[1].strip()


def _attempt_has_runtime_evidence(attempt: Mapping[str, Any]) -> bool:
    status = str(attempt.get("status", "")).strip()
    attempted_passes = _string_list(attempt.get("attempted_passes"))
    return bool(attempted_passes or status in {"attempted_only", "verified", "failed"})


def activation_report_invariant_issues(payload: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    summary = payload.get("summary")
    summary_scenarios: list[str] = []
    summary_failed_scenarios: list[str] = []
    if isinstance(summary, Mapping):
        summary_scenarios = _string_list(summary.get("scenarios_run"))
        summary_failed_scenarios = _string_list(summary.get("failed_scenarios"))

    trace_names = scenario_trace_names(payload)
    failed_trace_names = _failed_trace_names(payload)
    if trace_names and summary_scenarios != trace_names:
        issues.append(
            "summary.scenarios_run does not match the ordered scenario_traces ledger."
        )
    if failed_trace_names != summary_failed_scenarios:
        issues.append("summary.failed_scenarios does not match failed scenario_traces.")
    if failed_trace_names != _string_list(payload.get("failed_scenarios")):
        issues.append("failed_scenarios does not match failed scenario_traces.")

    trigger_execution_mode = str(payload.get("trigger_execution_mode", "")).strip()
    if (
        isinstance(summary, Mapping)
        and str(summary.get("trigger_execution_mode", "")).strip()
        and str(summary.get("trigger_execution_mode", "")).strip()
        != trigger_execution_mode
    ):
        issues.append(
            "summary.trigger_execution_mode does not match the top-level "
            "trigger_execution_mode."
        )

    if trigger_execution_mode == "layered_passes":
        stimulus_passes = _pass_mappings(payload)
        if not stimulus_passes:
            issues.append(
                "layered_passes reports must include non-empty stimulus_passes."
            )

        event_attempts = _attempt_mappings(payload)
        if not event_attempts:
            issues.append(
                "layered_passes reports must include non-empty event_attempts."
            )

        official_event_coverage = payload.get("official_event_coverage")
        if (
            not isinstance(official_event_coverage, Mapping)
            or not official_event_coverage
        ):
            issues.append(
                "layered_passes reports must include populated official_event_coverage."
            )

        attempt_ids = {
            str(item.get("attempt_id", "")).strip()
            for item in event_attempts
            if str(item.get("attempt_id", "")).strip()
        }
        pass_ids = {
            str(item.get("pass_id", "")).strip()
            for item in stimulus_passes
            if str(item.get("pass_id", "")).strip()
        }
        missing_pass_attempt_refs = sorted(
            {
                str(attempt_id).strip()
                for item in stimulus_passes
                for attempt_id in _string_list(item.get("attempt_ids"))
                if str(attempt_id).strip()
                and str(attempt_id).strip() not in attempt_ids
            }
        )
        if missing_pass_attempt_refs:
            issues.append(
                "stimulus_passes reference unknown event_attempt ids: "
                + ", ".join(missing_pass_attempt_refs)
            )

        missing_attempt_pass_refs = sorted(
            {
                pass_id
                for item in event_attempts
                for pass_id in _string_list(item.get("attempted_passes"))
                if pass_id not in pass_ids
            }
        )
        if missing_attempt_pass_refs:
            issues.append(
                "event_attempts reference unknown stimulus_pass ids: "
                + ", ".join(missing_attempt_pass_refs)
            )

        scenario_trace_set = set(trace_names)
        missing_runtime_scenarios = sorted(
            {
                scenario_name
                for item in event_attempts
                for scenario_name in [_scenario_action_name(item)]
                if scenario_name
                and _attempt_has_runtime_evidence(item)
                and scenario_name not in scenario_trace_set
            }
        )
        if missing_runtime_scenarios:
            issues.append(
                "scenario-style event_attempts have runtime evidence but no matching "
                "scenario_traces: " + ", ".join(missing_runtime_scenarios)
            )

    return issues
