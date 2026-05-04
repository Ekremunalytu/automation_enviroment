"""Coverage accounting and payload finalization for planner outputs."""

from __future__ import annotations

from typing import Any, cast

from packages.analysis_contracts import TriggerPayload
from packages.analysis_contracts.contracts import (
    EventAttemptRecord,
    PrerequisiteResult,
    TriggerScenarioDetail,
    TriggerStimulusPass,
)
from packages.analysis_planner.attempts import (
    _build_prerequisite_results,
    _build_stimulus_passes,
    _summarize_event_attempts,
)
from packages.analysis_planner.io import (
    _serialize_event_strategy,
    _serialize_scenario_definition,
)
from packages.analysis_planner.registry import (
    _GLOBAL_CAPABILITY_NOTES,
    _HEURISTIC_CAPABILITY_SUPPORT,
    _HEURISTIC_TRACK,
    _MAX_EXTRA_COMMANDS,
    _MAX_SCENARIOS_PER_RUN,
    _OFFICIAL_CAPABILITY_SUPPORT,
    _OFFICIAL_TRACK,
    _SCENARIO_BY_NAME,
    _SCENARIO_PRIORITY,
    _TRACK_SOURCE,
    CAPABILITY_TAXONOMY,
    OFFICIAL_EVENT_REGISTRY,
    SCENARIO_REGISTRY,
)


def _finalize_payload(
    *,
    payload: TriggerPayload,
    selected_candidates: set[str],
    official_candidates: set[str],
    heuristic_candidates: set[str],
    scenario_scores: dict[str, int],
    scenario_reasons: dict[str, set[str]],
    compiled_attempts: dict[tuple[str, str], dict[str, Any]],
    official_extra_capabilities: set[str],
    heuristic_extra_capabilities: set[str],
) -> TriggerPayload:
    payload.extra_commands = payload.extra_commands[:_MAX_EXTRA_COMMANDS]
    payload.auth_provider_ids = sorted(set(payload.auth_provider_ids))
    payload.webview_view_ids = sorted(set(payload.webview_view_ids))
    payload.extra_custom_editor_files = sorted(set(payload.extra_custom_editor_files))
    payload.extra_notebook_files = sorted(set(payload.extra_notebook_files))
    # During the planner mutation phase TriggerPayload's typed list slots
    # (event_attempts, stimulus_passes, prerequisite_results,
    # selected_scenario_details) hold raw dicts; the model_validate call at
    # the bottom of this function is what coerces them into typed records.
    # cast(...) tells mypy to trust the post-validation shape.
    payload.event_attempts = cast(
        list[EventAttemptRecord],
        [
            compiled_attempts[key]
            for key in sorted(compiled_attempts, key=lambda item: (item[0], item[1]))
        ],
    )
    payload.stimulus_passes = cast(
        list[TriggerStimulusPass],
        _build_stimulus_passes(cast(list[dict[str, Any]], payload.event_attempts)),
    )
    payload.prerequisite_results = cast(
        list[PrerequisiteResult],
        _build_prerequisite_results(cast(list[dict[str, Any]], payload.event_attempts)),
    )
    payload.selected_scenarios = _order_scenarios(selected_candidates, scenario_scores)
    payload.official_selected_scenarios = [
        scenario_name
        for scenario_name in payload.selected_scenarios
        if scenario_name in official_candidates
    ]
    payload.heuristic_selected_scenarios = [
        scenario_name
        for scenario_name in payload.selected_scenarios
        if scenario_name in heuristic_candidates
    ]
    payload.selection_reasons = {
        scenario_name: sorted(scenario_reasons.get(scenario_name, set()))
        for scenario_name in payload.selected_scenarios
    }
    payload.selected_scenario_details = cast(
        list[TriggerScenarioDetail],
        [
            _serialize_scenario_definition(
                _SCENARIO_BY_NAME[scenario_name],
                payload.selection_reasons.get(scenario_name, []),
            )
            for scenario_name in payload.selected_scenarios
        ],
    )
    payload.official_attempted_capabilities = _collect_active_capabilities(
        payload.official_selected_scenarios,
        payload=payload,
        track=_OFFICIAL_TRACK,
        extra_capabilities=official_extra_capabilities,
    )
    official_attempted = set(payload.official_attempted_capabilities)
    payload.heuristic_attempted_capabilities = [
        capability
        for capability in _collect_active_capabilities(
            payload.heuristic_selected_scenarios,
            payload=payload,
            track=_HEURISTIC_TRACK,
            extra_capabilities=heuristic_extra_capabilities,
        )
        if capability not in official_attempted
    ]
    official_matrix = build_coverage_matrix(payload, track=_OFFICIAL_TRACK)
    heuristic_matrix = build_coverage_matrix(payload, track=_HEURISTIC_TRACK)
    payload.coverage_summary = _summarize_coverage_matrix(official_matrix)
    payload.coverage_matrix = official_matrix
    payload.coverage_tracks = {
        _OFFICIAL_TRACK: {
            "source": _TRACK_SOURCE[_OFFICIAL_TRACK],
            "selected_scenarios": payload.official_selected_scenarios,
            "summary": payload.coverage_summary,
            "matrix": official_matrix,
        },
        _HEURISTIC_TRACK: {
            "source": _TRACK_SOURCE[_HEURISTIC_TRACK],
            "selected_scenarios": payload.heuristic_selected_scenarios,
            "summary": _summarize_coverage_matrix(heuristic_matrix),
            "matrix": heuristic_matrix,
        },
    }
    payload.official_event_coverage = _summarize_event_attempts(
        cast(list[dict[str, Any]], payload.event_attempts),
        track=_OFFICIAL_TRACK,
    )
    payload.heuristic_workflow_coverage = _summarize_event_attempts(
        cast(list[dict[str, Any]], payload.event_attempts),
        track=_HEURISTIC_TRACK,
    )
    # W10-2: payload was built via TriggerPayload.model_construct so typed
    # list slots (selected_scenario_details, event_attempts, ...) currently
    # hold plain dicts. model_dump(warnings=False) suppresses the expected
    # "untyped item in typed slot" notices; the model_validate that follows
    # is the authoritative contract enforcement on the way out.
    return TriggerPayload.model_validate(payload.model_dump(warnings=False))


def build_coverage_matrix(
    payload: TriggerPayload,
    *,
    track: str = _OFFICIAL_TRACK,
) -> list[dict[str, Any]]:
    """Build target-first coverage information for the selected payload."""

    if track == _OFFICIAL_TRACK:
        track_selected_scenarios = payload.official_selected_scenarios
        active_capabilities = set(payload.official_attempted_capabilities)
        support_map = _OFFICIAL_CAPABILITY_SUPPORT
    else:
        track_selected_scenarios = payload.heuristic_selected_scenarios
        active_capabilities = set(payload.heuristic_attempted_capabilities)
        support_map = _HEURISTIC_CAPABILITY_SUPPORT
    matrix: list[dict[str, Any]] = []

    for capability in CAPABILITY_TAXONOMY:
        supported_scenarios = [
            scenario.name
            for scenario in SCENARIO_REGISTRY
            if capability in scenario.api_capabilities
        ]
        capability_selected_scenarios = [
            scenario_name
            for scenario_name in track_selected_scenarios
            if capability in _SCENARIO_BY_NAME[scenario_name].api_capabilities
        ]
        support_level = support_map[capability]
        if support_level == "missing":
            status = "missing"
        elif capability in active_capabilities and support_level == "covered":
            status = "covered"
        else:
            status = "partial"

        matrix.append(
            {
                "capability": capability,
                "status": status,
                "track": track,
                "source": _TRACK_SOURCE[track],
                "support_status": support_level,
                "selected_scenarios": capability_selected_scenarios,
                "supported_scenarios": supported_scenarios,
                "is_active": capability in active_capabilities,
                "notes": _GLOBAL_CAPABILITY_NOTES.get(capability, ""),
                "selected": capability in active_capabilities,
            }
        )

    return matrix


def build_static_coverage_audit() -> dict[str, Any]:
    """Describe overall framework support independent of a specific extension."""

    official_matrix = _build_static_track_matrix(_OFFICIAL_TRACK)
    heuristic_matrix = _build_static_track_matrix(_HEURISTIC_TRACK)

    return {
        "summary": _summarize_coverage_matrix(official_matrix),
        "matrix": official_matrix,
        "coverage_tracks": {
            _OFFICIAL_TRACK: {
                "source": _TRACK_SOURCE[_OFFICIAL_TRACK],
                "summary": _summarize_coverage_matrix(official_matrix),
                "matrix": official_matrix,
            },
            _HEURISTIC_TRACK: {
                "source": _TRACK_SOURCE[_HEURISTIC_TRACK],
                "summary": _summarize_coverage_matrix(heuristic_matrix),
                "matrix": heuristic_matrix,
            },
        },
        "official_event_registry": [
            _serialize_event_strategy(strategy)
            for strategy in OFFICIAL_EVENT_REGISTRY.values()
        ],
        "scenarios": [
            _serialize_scenario_definition(scenario, [])
            for scenario in SCENARIO_REGISTRY
        ],
    }


def _order_scenarios(selected: set[str], scores: dict[str, int]) -> list[str]:
    ordered = sorted(
        selected,
        key=lambda name: (-scores.get(name, 0), _SCENARIO_PRIORITY.index(name)),
    )
    return ordered[:_MAX_SCENARIOS_PER_RUN]


def _collect_active_capabilities(
    selected_scenarios: list[str],
    *,
    payload: TriggerPayload,
    track: str,
    extra_capabilities: set[str] | None = None,
) -> list[str]:
    support_map = (
        _OFFICIAL_CAPABILITY_SUPPORT
        if track == _OFFICIAL_TRACK
        else _HEURISTIC_CAPABILITY_SUPPORT
    )
    capabilities: set[str] = set()
    for scenario_name in selected_scenarios:
        capabilities.update(_SCENARIO_BY_NAME[scenario_name].api_capabilities)
    # event_attempts items are still raw dicts here (planner mutation
    # phase); .get(...) is the right access pattern. The slot becomes
    # list[EventAttemptRecord] only after _finalize_payload's model_validate.
    for attempt in cast(list[dict[str, Any]], payload.event_attempts):
        if attempt.get("track") != track:
            continue
        if track == _OFFICIAL_TRACK and attempt.get("event_family") in {
            "*",
            "onStartupFinished",
        }:
            continue
        capabilities.update(
            str(item)
            for item in attempt.get("capability_tags", [])
            if str(item).strip()
        )
    if payload.extra_commands and track == _HEURISTIC_TRACK:
        capabilities.add("commands")
    if payload.extra_custom_editor_files:
        capabilities.add("custom_editors")
    if payload.extra_notebook_files and track == _OFFICIAL_TRACK:
        capabilities.add("notebooks")
    if payload.run_task_trigger and track == _OFFICIAL_TRACK:
        capabilities.add("terminal_tasks")
    if (
        payload.run_walkthrough_trigger or payload.uri_trigger
    ) and track == _OFFICIAL_TRACK:
        capabilities.add("uri_walkthrough")
    if "authentication_probe" in selected_scenarios:
        capabilities.add("authentication")
    if "webview_probe" in selected_scenarios:
        capabilities.add("webview")
    if extra_capabilities:
        capabilities.update(extra_capabilities)
    return sorted(
        capability
        for capability in capabilities
        if support_map.get(capability, "missing") == "covered"
    )


def _build_static_track_matrix(track: str) -> list[dict[str, Any]]:
    support_map = (
        _OFFICIAL_CAPABILITY_SUPPORT
        if track == _OFFICIAL_TRACK
        else _HEURISTIC_CAPABILITY_SUPPORT
    )
    return [
        {
            "capability": capability,
            "status": support_map[capability],
            "track": track,
            "source": _TRACK_SOURCE[track],
            "support_status": support_map[capability],
            "supported_scenarios": [
                scenario.name
                for scenario in SCENARIO_REGISTRY
                if capability in scenario.api_capabilities
            ],
            "notes": _GLOBAL_CAPABILITY_NOTES.get(capability, ""),
            "selected": False,
            "is_active": False,
            "selected_scenarios": [],
        }
        for capability in CAPABILITY_TAXONOMY
    ]


def _summarize_coverage_matrix(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    covered = [
        entry["capability"] for entry in matrix if entry.get("status") == "covered"
    ]
    partial = [
        entry["capability"] for entry in matrix if entry.get("status") == "partial"
    ]
    missing = [
        entry["capability"] for entry in matrix if entry.get("status") == "missing"
    ]
    return {
        "covered": len(covered),
        "partial": len(partial),
        "missing": len(missing),
        "covered_capabilities": covered,
        "partial_capabilities": partial,
        "missing_capabilities": missing,
    }
