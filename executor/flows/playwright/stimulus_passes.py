"""Pass orchestration for layered stimulus plans."""

from __future__ import annotations

from typing import Any

import automation
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page
from stimulus_attempts import (
    action_for_pass,
    dedupe_execution_key,
    deduped_result_details,
    execute_attempt,
    failure_reason_code_for_exception,
    method_for_pass,
)
from stimulus_prerequisites import materialize_prerequisite, trigger_item_as_dict
from stimulus_types import (
    AttemptExecutionRecord,
    AutomationExecutionResult,
    SkippedScenarioRecord,
)


def run_stimulus_plan(
    page: Page,
    payload: Any,
    *,
    monitor: Any | None = None,
) -> AutomationExecutionResult:
    """Execute the compiled layered plan pass-by-pass."""
    result = AutomationExecutionResult(
        requested_scenarios=_ordered_names(
            getattr(payload, "selected_scenarios", []) or []
        )
    )
    covered_scenarios: list[str] = []
    scenario_reasons: dict[str, tuple[str, str]] = {}
    attempts_by_id = {
        attempt_id: attempt
        for raw_attempt in getattr(payload, "event_attempts", []) or []
        for attempt in [trigger_item_as_dict(raw_attempt)]
        if attempt is not None
        for attempt_id in [str(attempt.get("attempt_id", "")).strip()]
        if attempt_id
    }

    for raw_pass_data in getattr(payload, "stimulus_passes", []) or []:
        pass_data = trigger_item_as_dict(raw_pass_data)
        if pass_data is None:
            continue
        stage_id = str(pass_data.get("pass_id", "")).strip()
        if not stage_id:
            continue
        label = str(pass_data.get("label", stage_id))
        order = int(pass_data.get("order", 0) or 0)
        if monitor is not None:
            monitor.record_stimulus_pass_event(
                "start",
                stage_id,
                label=label,
                order=order,
                trigger_method="layered_deep",
            )

        pass_failed = False
        blocked_attempts: dict[str, tuple[str, str]] = {}
        execution_records: dict[str, AttemptExecutionRecord] = {}
        for prerequisite in prerequisites_for_pass(pass_data, payload):
            result_data = materialize_prerequisite(
                prerequisite,
                payload=payload,
                attempts_by_id=attempts_by_id,
                monitor=monitor,
            )
            if result_data.status != "completed":
                for attempt_id in prerequisite.get("attempt_ids", []) or []:
                    blocked_attempts[str(attempt_id)] = (
                        result_data.reason_code or "prerequisite_blocked",
                        result_data.detail,
                    )

        if stage_id == "post_run_verification":
            if monitor is not None:
                monitor.record_stimulus_pass_event(
                    "end",
                    stage_id,
                    label=label,
                    order=order,
                    trigger_method="layered_deep",
                    status="completed",
                )
            continue

        for attempt_id in pass_data.get("attempt_ids", []):
            attempt = attempts_by_id.get(str(attempt_id))
            if attempt is None:
                continue
            blocked_reason = blocked_attempts.get(str(attempt_id))
            if blocked_reason is not None:
                pass_failed = True
                _record_scenario_reason(
                    scenario_reasons,
                    _related_scenarios(attempt),
                    reason_code=blocked_reason[0],
                    detail=blocked_reason[1],
                )
                if monitor is not None:
                    monitor.record_event_attempt_end(
                        attempt["attempt_id"],
                        status="blocked",
                        blocked_reason_code=blocked_reason[0],
                        result_details=blocked_reason[1],
                    )
                continue

            unsupported_reason = _unsupported_surface_reason(attempt)
            if unsupported_reason is not None:
                pass_failed = True
                _record_scenario_reason(
                    scenario_reasons,
                    _related_scenarios(attempt),
                    reason_code=unsupported_reason[0],
                    detail=unsupported_reason[1],
                )
                if monitor is not None:
                    monitor.record_event_attempt_end(
                        attempt["attempt_id"],
                        status="blocked",
                        pass_name=stage_id,
                        blocked_reason_code=unsupported_reason[0],
                        result_details=unsupported_reason[1],
                    )
                continue

            action = action_for_pass(stage_id, attempt)
            trigger_method = method_for_pass(stage_id, attempt)
            unknown_reason = _unknown_scenario_reason(action)
            if unknown_reason is not None:
                pass_failed = True
                _record_scenario_reason(
                    scenario_reasons,
                    [unknown_reason[2]],
                    reason_code=unknown_reason[0],
                    detail=unknown_reason[1],
                )
                if monitor is not None:
                    monitor.record_event_attempt_end(
                        attempt["attempt_id"],
                        status="blocked",
                        pass_name=stage_id,
                        trigger_method_used=trigger_method,
                        blocked_reason_code=unknown_reason[0],
                        result_details=unknown_reason[1],
                    )
                continue
            if monitor is not None:
                monitor.record_event_attempt_start(
                    attempt["attempt_id"], pass_name=stage_id
                )
            execution_key = dedupe_execution_key(stage_id, attempt, action)
            prior_execution = (
                execution_records.get(execution_key) if execution_key else None
            )
            if prior_execution is not None:
                if prior_execution.status in {"attempted_only", "failed"}:
                    _record_scenario_coverage(covered_scenarios, attempt)
                if prior_execution.status == "failed":
                    pass_failed = True
                if monitor is not None:
                    monitor.record_event_attempt_end(
                        attempt["attempt_id"],
                        status=prior_execution.status,
                        pass_name=stage_id,
                        trigger_method_used=trigger_method,
                        result_details=deduped_result_details(
                            stage_id, action, prior_execution
                        ),
                        failure_reason_code=prior_execution.failure_reason_code,
                    )
                continue

            try:
                execute_attempt(
                    page,
                    payload,
                    attempt,
                    action=action,
                    trigger_method=trigger_method,
                    result=result,
                    monitor=monitor,
                )
                if execution_key:
                    execution_records[execution_key] = AttemptExecutionRecord(
                        status="attempted_only"
                    )
                _record_scenario_coverage(covered_scenarios, attempt)
                if monitor is not None:
                    monitor.record_event_attempt_end(
                        attempt["attempt_id"],
                        status="attempted_only",
                        pass_name=stage_id,
                        trigger_method_used=trigger_method,
                    )
            except (OSError, PlaywrightError, RuntimeError, ValueError) as exc:
                pass_failed = True
                result.extra_trigger_failures.append(
                    f"{attempt['attempt_id']}:{action}"
                )
                failure_reason_code = failure_reason_code_for_exception(exc)
                if execution_key:
                    execution_records[execution_key] = AttemptExecutionRecord(
                        status="failed",
                        result_details=str(exc),
                        failure_reason_code=failure_reason_code,
                    )
                _record_scenario_coverage(covered_scenarios, attempt)
                if monitor is not None:
                    monitor.record_event_attempt_end(
                        attempt["attempt_id"],
                        status="failed",
                        pass_name=stage_id,
                        trigger_method_used=trigger_method,
                        result_details=str(exc),
                        failure_reason_code=failure_reason_code,
                    )

        if monitor is not None:
            monitor.record_stimulus_pass_event(
                "end",
                stage_id,
                label=label,
                order=order,
                trigger_method="layered_deep",
                status="failed" if pass_failed else "completed",
            )

    executed_names = set(result.executed_scenarios) | set(covered_scenarios)
    requested_attempt_scenarios = {
        scenario_name
        for attempt in attempts_by_id.values()
        for scenario_name in _related_scenarios(attempt)
    }
    for scenario_name in result.requested_scenarios:
        if scenario_name in executed_names:
            continue
        reason_code, detail = scenario_reasons.get(
            scenario_name,
            (
                "not_executed",
                (
                    "Scenario was selected but no layered attempt produced runtime "
                    "coverage."
                    if scenario_name in requested_attempt_scenarios
                    else "Scenario was selected but the layered plan contained no "
                    "matching attempt."
                ),
            ),
        )
        result.skipped_scenarios.append(
            SkippedScenarioRecord(
                name=scenario_name,
                reason_code=reason_code,
                detail=detail,
            )
        )

    return result


_SUPPORTED_EVENT_FAMILIES = {
    "workspaceContains",
    "onLanguage",
    "onCommand",
    "onDebugInitialConfigurations",
    "onDebugResolve",
    "onTaskType",
    "onUri",
    "onCustomEditor",
    "onWalkthrough",
    "onLanguageModelTool",
    "onTerminalShellIntegration",
}


def _ordered_names(raw_names: list[Any]) -> list[str]:
    names: list[str] = []
    for raw_name in raw_names:
        name = str(raw_name).strip()
        if name and name not in names:
            names.append(name)
    return names


def _related_scenarios(attempt: dict[str, Any]) -> list[str]:
    names = _ordered_names(attempt.get("legacy_scenarios", []) or [])
    action = str(attempt.get("executor_action", "")).strip()
    if action.startswith("scenario:"):
        names = _ordered_names([action.split(":", maxsplit=1)[1], *names])
    backfill_action = str(attempt.get("backfill_executor_action", "")).strip()
    if backfill_action.startswith("scenario:"):
        names = _ordered_names([*names, backfill_action.split(":", maxsplit=1)[1]])
    return names


def _record_scenario_reason(
    reasons: dict[str, tuple[str, str]],
    scenario_names: list[str],
    *,
    reason_code: str,
    detail: str,
) -> None:
    for scenario_name in scenario_names:
        if scenario_name and scenario_name not in reasons:
            reasons[scenario_name] = (reason_code, detail)


def _record_scenario_coverage(
    covered_scenarios: list[str],
    attempt: dict[str, Any],
) -> None:
    for scenario_name in _related_scenarios(attempt):
        if scenario_name and scenario_name not in covered_scenarios:
            covered_scenarios.append(scenario_name)


def _unsupported_surface_reason(
    attempt: dict[str, Any],
) -> tuple[str, str] | None:
    event_family = str(attempt.get("event_family", "")).strip()
    if not event_family or event_family in _SUPPORTED_EVENT_FAMILIES:
        return None
    return (
        "unsupported_activation_surface",
        f"Activation family {event_family!r} is not supported by the executor.",
    )


def _unknown_scenario_reason(
    action: str,
) -> tuple[str, str, str] | None:
    if not action.startswith("scenario:"):
        return None
    scenario_name = action.split(":", maxsplit=1)[1].strip()
    if scenario_name in set(automation.list_scenarios()):
        return None
    return (
        "unknown_scenario",
        f"Scenario {scenario_name!r} is not registered in the executor.",
        scenario_name,
    )


def prerequisites_for_pass(
    pass_data: dict[str, Any], payload: Any
) -> list[dict[str, Any]]:
    lookup = {
        str(item.get("prerequisite_id", "")): item
        for item in getattr(payload, "prerequisite_results", []) or []
        for item in [trigger_item_as_dict(item)]
        if item is not None
    }
    by_key = {
        str(item.get("key", "")): item
        for item in getattr(payload, "prerequisite_results", []) or []
        for item in [trigger_item_as_dict(item)]
        if item is not None
    }
    items: list[dict[str, Any]] = []
    for raw_key in pass_data.get("prerequisite_keys", []):
        key = str(raw_key).strip()
        if not key:
            continue
        if key in lookup:
            items.append(lookup[key])
        elif key in by_key:
            items.append(by_key[key])
    return items
