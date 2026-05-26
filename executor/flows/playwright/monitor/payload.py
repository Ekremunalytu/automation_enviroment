"""Trigger-payload mapping helpers for activation monitoring."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .records import (
    EventAttemptRecord,
    PrerequisiteResult,
    StimulusPassTrace,
)
from .runtime import (
    _extract_heuristic_attempted_capabilities,
    _extract_official_attempted_capabilities,
    _trigger_item_as_dict,
)

if TYPE_CHECKING:
    from .types import ActivationReport


def _payload_items(payload: Any, field_name: str) -> list[dict[str, Any]]:
    return [
        item
        for raw_item in getattr(payload, field_name, []) or []
        for item in [_trigger_item_as_dict(raw_item)]
        if item is not None
    ]


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value or [] if str(item).strip()]


def _build_stimulus_passes(payload: Any) -> list[StimulusPassTrace]:
    return [
        StimulusPassTrace(
            pass_id=str(item.get("pass_id", "")),
            label=str(item.get("label", "")),
            order=int(item.get("order", 0) or 0),
            started_at=0.0,
            status=str(item.get("status", "planned")),
            trigger_method=str(item.get("trigger_method", "")),
        )
        for item in _payload_items(payload, "stimulus_passes")
    ]


def _build_prerequisite_results(payload: Any) -> list[PrerequisiteResult]:
    return [
        PrerequisiteResult(
            prerequisite_id=str(item.get("prerequisite_id", "")),
            key=str(item.get("key", "")),
            label=str(item.get("label", "")),
            status=str(item.get("status", "planned")),
            materializer=str(item.get("materializer", "")),
            pass_name=str(item.get("pass_name", "")),
            attempt_ids=_string_list(item.get("attempt_ids", [])),
            detail=str(item.get("detail", "")),
            reason_code=str(item.get("reason_code", "")),
            resolved_targets=dict(item.get("resolved_targets", {}) or {}),
        )
        for item in _payload_items(payload, "prerequisite_results")
    ]


def _build_event_attempts(payload: Any) -> list[EventAttemptRecord]:
    return [
        EventAttemptRecord(
            attempt_id=str(item.get("attempt_id", "")),
            declared_event=str(item.get("declared_event", "")),
            activation_event=str(item.get("activation_event", "")),
            event_family=str(item.get("event_family", "")),
            event_value=str(item.get("event_value", "")),
            track=str(item.get("track", "official")),
            selected_by=str(item.get("selected_by", "")),
            selection_reasons=_string_list(item.get("selection_reasons", [])),
            pass_name=str(item.get("pass_name", "")),
            backfill_pass_name=str(item.get("backfill_pass_name", "")),
            prerequisite_keys=_string_list(item.get("prerequisite_keys", [])),
            verification_contract=_string_list(item.get("verification_contract", [])),
            trigger_method=str(item.get("trigger_method", "")),
            fallback_trigger_method=str(item.get("fallback_trigger_method", "")),
            executor_action=str(item.get("executor_action", "")),
            backfill_executor_action=str(item.get("backfill_executor_action", "")),
            legacy_scenarios=_string_list(item.get("legacy_scenarios", [])),
            capability_tags=_string_list(item.get("capability_tags", [])),
            status=str(item.get("status", "planned")),
            trigger_method_used=str(item.get("trigger_method_used", "")),
            attempted_passes=_string_list(item.get("attempted_passes", [])),
            evidence=_string_list(item.get("evidence", [])),
            verification_status=str(item.get("verification_status", "not_attempted")),
            failure_reason_code=str(item.get("failure_reason_code", "")),
            blocked_reason_code=str(item.get("blocked_reason_code", "")),
            result_details=str(item.get("result_details", "")),
            official=bool(item.get("official", True)),
            heuristic=bool(item.get("heuristic", False)),
            ui_path=str(item.get("ui_path", "")),
            harness_fallback=str(item.get("harness_fallback", "")),
            confirmation_source=str(item.get("confirmation_source", "none") or "none"),
        )
        for item in _payload_items(payload, "event_attempts")
    ]


def populate_report_from_trigger_payload(
    report: ActivationReport,
    payload: Any,
) -> None:
    """Attach trigger-selection metadata to the in-progress report."""
    report.trigger_plan_requested = True
    report.trigger_plan_loaded = True
    report.coverage_tracks = dict(getattr(payload, "coverage_tracks", {}))
    report.coverage_summary = dict(getattr(payload, "coverage_summary", {}))
    report.coverage_matrix = list(getattr(payload, "coverage_matrix", []))
    report.official_event_coverage = dict(
        getattr(payload, "official_event_coverage", {})
    )
    report.heuristic_workflow_coverage = dict(
        getattr(payload, "heuristic_workflow_coverage", {})
    )
    report.attempted_capabilities = _extract_official_attempted_capabilities(payload)
    report.heuristic_attempted_capabilities = _extract_heuristic_attempted_capabilities(
        payload
    )
    report.stimulus_passes = _build_stimulus_passes(payload)
    report.prerequisite_results = _build_prerequisite_results(payload)
    report.event_attempts = _build_event_attempts(payload)
    report.requested_scenarios = list(getattr(payload, "selected_scenarios", []) or [])

    payload_target = getattr(payload, "target_extension_id", None)
    if payload_target and not report.target_extension_id:
        report.target_extension_id = payload_target


__all__ = ["populate_report_from_trigger_payload"]
