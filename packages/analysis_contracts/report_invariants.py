"""Helpers for validating exported activation-report invariants."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

# W10-6: shared status set declaring "the harness saw enough runtime
# evidence to count this attempt as exercised". Imported by both the
# contract invariant (_attempt_has_runtime_evidence below) and the
# executor's health_runtime_facts.attempt_has_runtime_evidence so the
# two helpers cannot drift again. ``activation_seen`` /
# ``target_log_seen`` are intermediate observation states emitted by
# reconcile_event_attempts when the target extension activated but full
# verification did not close — both are strictly stronger than
# ``attempted_only`` so they count as runtime evidence.
RUNTIME_EVIDENCE_STATES: frozenset[str] = frozenset(
    {
        "attempted_only",
        "activation_seen",
        "target_log_seen",
        "verified",
        "failed",
    }
)


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
    return bool(attempted_passes or status in RUNTIME_EVIDENCE_STATES)


def _attempt_related_scenarios(attempt: Mapping[str, Any]) -> list[str]:
    names = _string_list(attempt.get("legacy_scenarios"))
    for key in ("executor_action", "backfill_executor_action"):
        action = str(attempt.get(key, "")).strip()
        if not action.startswith("scenario:"):
            continue
        scenario_name = action.split(":", maxsplit=1)[1].strip()
        if scenario_name and scenario_name not in names:
            names.append(scenario_name)
    return names


def _layered_covered_scenario_names(payload: Mapping[str, Any]) -> list[str]:
    covered: list[str] = []
    for attempt in _attempt_mappings(payload):
        if not _attempt_has_runtime_evidence(attempt):
            continue
        for scenario_name in _attempt_related_scenarios(attempt):
            if scenario_name and scenario_name not in covered:
                covered.append(scenario_name)
    return covered


def _skipped_scenario_names(payload: Mapping[str, Any]) -> list[str]:
    skipped = _mapping_list(payload.get("skipped_scenarios"))
    return [
        str(item.get("name", "")).strip()
        for item in skipped
        if str(item.get("name", "")).strip()
    ]


def activation_report_invariant_issues(payload: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    summary = payload.get("summary")
    summary_scenarios: list[str] = []
    summary_failed_scenarios: list[str] = []
    summary_skipped_scenarios: list[str] = []
    if isinstance(summary, Mapping):
        summary_scenarios = _string_list(summary.get("scenarios_run"))
        summary_failed_scenarios = _string_list(summary.get("failed_scenarios"))
        summary_skipped_scenarios = _string_list(summary.get("skipped_scenarios"))

    trace_names = scenario_trace_names(payload)
    failed_trace_names = _failed_trace_names(payload)
    skipped_scenario_names = _skipped_scenario_names(payload)
    if trace_names and summary_scenarios != trace_names:
        issues.append(
            "summary.scenarios_run does not match the ordered scenario_traces ledger."
        )
    if failed_trace_names != summary_failed_scenarios:
        issues.append("summary.failed_scenarios does not match failed scenario_traces.")
    if skipped_scenario_names != summary_skipped_scenarios:
        issues.append(
            "summary.skipped_scenarios does not match top-level skipped_scenarios."
        )
    if failed_trace_names != _string_list(payload.get("failed_scenarios")):
        issues.append("failed_scenarios does not match failed scenario_traces.")

    trigger_execution_mode = str(payload.get("trigger_execution_mode", "")).strip()
    requested_scenarios = _string_list(payload.get("requested_scenarios"))
    if trigger_execution_mode == "layered_passes":
        layered_covered_scenarios = _layered_covered_scenario_names(payload)
        missing_requested_scenarios = [
            scenario_name
            for scenario_name in requested_scenarios
            if scenario_name
            and scenario_name
            not in {
                *trace_names,
                *skipped_scenario_names,
                *layered_covered_scenarios,
            }
        ]
        if missing_requested_scenarios:
            issues.append(
                "requested_scenarios are missing layered coverage records: "
                + ", ".join(missing_requested_scenarios)
            )
    elif requested_scenarios and requested_scenarios != [
        *trace_names,
        *skipped_scenario_names,
    ]:
        issues.append(
            "requested_scenarios does not match the ordered executed plus "
            "skipped scenario ledger."
        )

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


def _evidence_event_ids(activation_payload: Mapping[str, Any]) -> set[str]:
    event_ids: set[str] = set()
    for event in _mapping_list(activation_payload.get("evidence_events")):
        value = str(event.get("event_id", "")).strip()
        if value:
            event_ids.add(value)
    return event_ids


def detection_report_invariant_issues(
    detection_payload: Mapping[str, Any],
    activation_payload: Mapping[str, Any],
) -> list[str]:
    """Validate detection↔activation cross-references.

    Ensures every DetectionFinding.evidence points to an event that the
    activation report actually exposes, and every RuleExecutionRecord
    finding_id resolves to a finding carried in the same report.
    """

    issues: list[str] = []
    event_ids = _evidence_event_ids(activation_payload)

    findings = _mapping_list(detection_payload.get("findings"))
    finding_ids: set[str] = set()
    for finding in findings:
        finding_id = str(finding.get("id", "")).strip()
        if finding_id:
            finding_ids.add(finding_id)
        evidence_entries = _mapping_list(finding.get("evidence"))
        missing_event_refs: list[str] = []
        for entry in evidence_entries:
            event_id = str(entry.get("event_id", "")).strip()
            if not event_id:
                continue
            if event_id not in event_ids:
                missing_event_refs.append(event_id)
        if missing_event_refs:
            issues.append(
                "detection finding "
                + (finding_id or "<unknown>")
                + " references unknown evidence event_ids: "
                + ", ".join(sorted(set(missing_event_refs)))
            )

    rules_executed = _mapping_list(detection_payload.get("rules_executed"))
    for record in rules_executed:
        rule_id = str(record.get("rule_id", "")).strip()
        declared_findings = _string_list(record.get("finding_ids"))
        unknown = sorted(
            {value for value in declared_findings if value not in finding_ids}
        )
        if unknown:
            issues.append(
                "rule execution "
                + (rule_id or "<unknown>")
                + " references unknown finding_ids: "
                + ", ".join(unknown)
            )

    return issues
