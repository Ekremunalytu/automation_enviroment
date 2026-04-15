"""Scenario selection and planner draft assembly helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from packages.analysis_contracts import TriggerPayload
from packages.analysis_planner.attempts import _build_event_attempt
from packages.analysis_planner.coverage import _finalize_payload
from packages.analysis_planner.io import (
    _activation_label,
    _collect_contributed_view_ids,
    _glob_to_bait_filename,
)
from packages.analysis_planner.registry import (
    _BUILTIN_VIEW_IDS,
    _HEURISTIC_TRACK,
    _OFFICIAL_TRACK,
    _SCENARIO_BY_NAME,
    _SCENARIO_PRIORITY,
    EVENT_TYPE_TO_SCENARIOS,
    HEURISTIC_EVENT_TYPE_TO_SCENARIOS,
    OFFICIAL_EVENT_REGISTRY,
)


@dataclass
class _TriggerPayloadDraft:
    """Mutable planner state before the canonical trigger contract is finalized."""

    analysis_profile: str = "layered_deep"
    selected_scenarios: list[str] = field(default_factory=list)
    official_selected_scenarios: list[str] = field(default_factory=list)
    heuristic_selected_scenarios: list[str] = field(default_factory=list)
    selected_scenario_details: list[dict[str, Any]] = field(default_factory=list)
    selection_reasons: dict[str, list[str]] = field(default_factory=dict)
    coverage_tracks: dict[str, dict[str, Any]] = field(default_factory=dict)
    coverage_summary: dict[str, Any] = field(default_factory=dict)
    coverage_matrix: list[dict[str, Any]] = field(default_factory=list)
    official_attempted_capabilities: list[str] = field(default_factory=list)
    heuristic_attempted_capabilities: list[str] = field(default_factory=list)
    target_extension_id: str | None = None
    command_targets: dict[str, str] = field(default_factory=dict)
    view_targets: dict[str, dict[str, str]] = field(default_factory=dict)
    extra_notebook_files: list[str] = field(default_factory=list)
    extra_custom_editor_files: list[str] = field(default_factory=list)
    extra_commands: list[str] = field(default_factory=list)
    auth_provider_ids: list[str] = field(default_factory=list)
    webview_view_ids: list[str] = field(default_factory=list)
    uri_trigger: str | None = None
    run_task_trigger: bool = False
    run_walkthrough_trigger: bool = False
    stimulus_passes: list[dict[str, Any]] = field(default_factory=list)
    event_attempts: list[dict[str, Any]] = field(default_factory=list)
    prerequisite_results: list[dict[str, Any]] = field(default_factory=list)
    official_event_coverage: dict[str, Any] = field(default_factory=dict)
    heuristic_workflow_coverage: dict[str, Any] = field(default_factory=dict)


def _apply_activation_event(
    event: dict[str, str | None],
    *,
    payload: _TriggerPayloadDraft,
    publisher_name: str | None,
    contributed_view_ids: set[str],
    official_extra_capabilities: set[str],
    mark_scenario: Callable[..., None],
    register_attempt: Callable[..., None],
) -> None:
    event_type = event.get("event_type", "") or ""
    event_value = event.get("event_value")
    event_label = _activation_label(event_type, event_value)

    if event_type in {"*", "onStartupFinished"}:
        register_attempt(
            event_type=event_type,
            event_value=event_value,
            track=_OFFICIAL_TRACK,
            reason=f"activation {event_type} requests startup coverage",
        )
        for index, scenario_name in enumerate(_SCENARIO_PRIORITY):
            mark_scenario(
                scenario_name,
                reason=f"activation {event_type} requests broad workspace coverage",
                score=10_000 - index,
                track=_HEURISTIC_TRACK,
            )
        return

    if event_type == "onView" and event_value:
        _apply_view_trigger(
            event_value=str(event_value),
            contributed_view_ids=contributed_view_ids,
            payload=payload,
            mark_scenario=mark_scenario,
            register_attempt=register_attempt,
            official_extra_capabilities=official_extra_capabilities,
        )
        return

    if event_type in OFFICIAL_EVENT_REGISTRY:
        register_attempt(
            event_type=event_type,
            event_value=event_value,
            track=_OFFICIAL_TRACK,
            reason=f"activation {event_label}",
        )
        scenario_names = EVENT_TYPE_TO_SCENARIOS.get(event_type, [])
        for index, scenario_name in enumerate(scenario_names):
            mark_scenario(
                scenario_name,
                reason=f"activation {event_label}",
                score=900 - index,
                track=_OFFICIAL_TRACK,
            )
    elif event_type in HEURISTIC_EVENT_TYPE_TO_SCENARIOS:
        scenario_names = HEURISTIC_EVENT_TYPE_TO_SCENARIOS[event_type]
        for index, scenario_name in enumerate(scenario_names):
            mark_scenario(
                scenario_name,
                reason=f"activation {event_label}",
                score=700 - index,
                track=_HEURISTIC_TRACK,
            )

    _apply_event_capability_metadata(
        event_type=event_type,
        event_value=event_value,
        publisher_name=publisher_name,
        payload=payload,
        contributed_view_ids=contributed_view_ids,
        official_extra_capabilities=official_extra_capabilities,
    )


def _apply_view_trigger(
    *,
    event_value: str,
    contributed_view_ids: set[str],
    payload: _TriggerPayloadDraft,
    mark_scenario: Callable[..., None],
    register_attempt: Callable[..., None],
    official_extra_capabilities: set[str],
) -> None:
    key = f"onView:{event_value}"
    if event_value in _BUILTIN_VIEW_IDS:
        register_attempt(
            event_type="onView",
            event_value=event_value,
            track=_HEURISTIC_TRACK,
            reason=f"built-in view trigger {key} is tracked as heuristic only",
        )
        scenario_names = HEURISTIC_EVENT_TYPE_TO_SCENARIOS.get(key, [])
        for index, scenario_name in enumerate(scenario_names):
            mark_scenario(
                scenario_name,
                reason=f"built-in view trigger {key} treated as heuristic coverage",
                score=1_000 - index,
                track=_HEURISTIC_TRACK,
            )
        return

    if event_value in contributed_view_ids:
        register_attempt(
            event_type="onView",
            event_value=event_value,
            track=_OFFICIAL_TRACK,
            reason=f"declared contributed view activation {key}",
        )
        if "webview" in event_value.lower():
            mark_scenario(
                "webview_probe",
                reason=f"contributed view trigger {key}",
                score=995,
                track=_OFFICIAL_TRACK,
            )
            official_extra_capabilities.add("webview")
            payload.webview_view_ids.append(event_value)
        else:
            mark_scenario(
                "project_exploration",
                reason=f"contributed view trigger {key}",
                score=990,
                track=_OFFICIAL_TRACK,
            )
        return

    register_attempt(
        event_type="onView",
        event_value=event_value,
        track=_HEURISTIC_TRACK,
        reason=(
            f"view trigger {key} was not matched to a contributed view and "
            "is therefore treated as heuristic"
        ),
    )
    mark_scenario(
        "project_exploration",
        reason=(
            f"unmapped view trigger {key} fell back to heuristic explorer coverage"
        ),
        score=250,
        track=_HEURISTIC_TRACK,
    )


def _apply_event_capability_metadata(
    *,
    event_type: str,
    event_value: str | None,
    publisher_name: str | None,
    payload: _TriggerPayloadDraft,
    contributed_view_ids: set[str],
    official_extra_capabilities: set[str],
) -> None:
    if event_type == "onNotebook":
        payload.extra_notebook_files.append("notebooks/analysis.ipynb")
        official_extra_capabilities.add("notebooks")
    if event_type == "onRenderer":
        payload.extra_notebook_files.append("notebooks/analysis.ipynb")
        official_extra_capabilities.update({"notebooks", "webview"})
    if event_type == "onTaskType":
        payload.run_task_trigger = True
        official_extra_capabilities.add("terminal_tasks")
    if event_type in {"onTerminal", "onTerminalProfile", "onTerminalShellIntegration"}:
        official_extra_capabilities.add("terminal_tasks")
    if event_type == "onAuthenticationRequest":
        if event_value:
            payload.auth_provider_ids.append(str(event_value))
        official_extra_capabilities.add("authentication")
    if event_type == "onWebviewPanel":
        if event_value:
            payload.webview_view_ids.append(str(event_value))
        official_extra_capabilities.add("webview")
    if (
        event_type == "onView"
        and event_value
        and str(event_value) in contributed_view_ids
    ):
        official_extra_capabilities.add("window_ui")
    if event_type == "onWalkthrough":
        payload.run_walkthrough_trigger = True
        official_extra_capabilities.add("uri_walkthrough")
    if event_type == "onOpenExternalUri":
        official_extra_capabilities.add("uri_walkthrough")
    if event_type == "onUri" and publisher_name:
        payload.uri_trigger = f"vscode://{publisher_name}/activate"
        official_extra_capabilities.add("uri_walkthrough")
    if event_type in {"onFileSystem", "onEditSession"}:
        official_extra_capabilities.add("workspace_fs")
    if event_type == "onSearch":
        official_extra_capabilities.add("search_views")
    if event_type in {"onChatParticipant", "onLanguageModelTool"}:
        official_extra_capabilities.add("chat")
    if event_type == "onIssueReporterOpened":
        official_extra_capabilities.add("window_ui")


def _apply_contributes_metadata(
    *,
    payload: _TriggerPayloadDraft,
    contributes_custom_editors: list[dict] | None,
    contributes_commands: list[dict] | None,
    contributes_authentication: list[dict] | None,
    contributes_views: dict[str, Any] | None,
    contributes_debuggers: list[dict] | None,
    contributes_walkthroughs: list[dict] | None,
    contributes_task_definitions: list[dict] | None,
    contributes_terminal_profiles: list[dict] | None,
    capability_metadata: dict[str, Any] | None,
    heuristic_extra_capabilities: set[str],
    official_extra_capabilities: set[str],
    mark_scenario: Callable[..., None],
) -> None:
    if contributes_custom_editors:
        for custom_editor in contributes_custom_editors:
            selectors = custom_editor.get("selector", [])
            for selector in selectors:
                glob_pattern = selector.get("filenamePattern", "")
                if not glob_pattern:
                    continue
                bait = _glob_to_bait_filename(glob_pattern)
                if bait:
                    payload.extra_custom_editor_files.append(bait)
                    heuristic_extra_capabilities.add("custom_editors")

    if contributes_commands:
        for command in contributes_commands:
            title = command.get("title", "")
            command_id = command.get("command_id", "") or command.get("command", "")
            if command_id:
                payload.command_targets[str(command_id)] = (
                    str(title) if title else str(command_id)
                )
            if title:
                payload.extra_commands.append(title)
                heuristic_extra_capabilities.add("commands")

    if contributes_authentication:
        mark_scenario(
            "authentication_probe",
            reason="contributes.authentication advertised provider metadata",
            score=520,
            track=_HEURISTIC_TRACK,
        )
        for provider in contributes_authentication:
            provider_id = provider.get("auth_id") or provider.get("id") or ""
            if provider_id:
                payload.auth_provider_ids.append(str(provider_id))
                heuristic_extra_capabilities.add("authentication")

    if contributes_views:
        if any(str(key).startswith("webview") for key in contributes_views):
            mark_scenario(
                "webview_probe",
                reason="contributes.views exposed a webview-oriented surface",
                score=510,
                track=_HEURISTIC_TRACK,
            )
            heuristic_extra_capabilities.add("webview")
        for location, views in contributes_views.items():
            if not isinstance(views, list):
                continue
            for view in views:
                if not isinstance(view, dict):
                    continue
                view_id = view.get("id") or ""
                if not view_id:
                    continue
                payload.view_targets[str(view_id)] = {
                    "container_id": str(location),
                    "view_type": str(view.get("type", "")),
                }
                if "webview" in str(view_id).lower():
                    payload.webview_view_ids.append(str(view_id))
                    heuristic_extra_capabilities.add("webview")

    if contributes_debuggers:
        official_extra_capabilities.add("debug")
    if contributes_walkthroughs:
        official_extra_capabilities.add("uri_walkthrough")
    if contributes_task_definitions or contributes_terminal_profiles:
        official_extra_capabilities.add("terminal_tasks")
    unsupported_trust = {
        "",
        "false",
        "unsupported",
    }
    if (
        capability_metadata
        and str(capability_metadata.get("untrusted_supported", "")).lower()
        not in unsupported_trust
    ):
        official_extra_capabilities.add("workspace_trust")


def _apply_default_fallback(
    *,
    selected_candidates: set[str],
    compiled_attempts: dict[tuple[str, str], dict[str, Any]],
    mark_scenario: Callable[..., None],
) -> None:
    if selected_candidates:
        return

    mark_scenario(
        "coding_session",
        reason=(
            "default fallback because activation metadata did not map to a "
            "stronger workflow"
        ),
        score=1,
        track=_HEURISTIC_TRACK,
    )
    compiled_attempts[(_HEURISTIC_TRACK, "heuristic:workspace_probe")] = {
        "attempt_id": "heuristic-workspace-probe",
        "declared_event": "heuristic:workspace_probe",
        "activation_event": "heuristic:workspace_probe",
        "event_family": "heuristic_workspace_probe",
        "event_value": "",
        "track": _HEURISTIC_TRACK,
        "selected_by": "fallback",
        "selection_reasons": [
            "default fallback because no declared activation event mapped cleanly"
        ],
        "pass_name": "ui_first_user_session",
        "backfill_pass_name": "",
        "prerequisite_keys": ["workspace_ready"],
        "verification_contract": ["automation_trace"],
        "trigger_method": "ui_simulation",
        "fallback_trigger_method": "",
        "executor_action": "scenario:coding_session",
        "backfill_executor_action": "",
        "legacy_scenarios": ["coding_session"],
        "capability_tags": [
            "commands",
            "languages_editor",
            "window_ui",
            "workspace_fs",
        ],
        "status": "planned",
        "trigger_method_used": "",
        "attempted_passes": [],
        "evidence": [],
        "verification_status": "not_attempted",
        "failure_reason_code": "",
        "blocked_reason_code": "",
        "result_details": "",
        "official": False,
        "heuristic": True,
    }


def select_scenarios(
    activation_events: list[dict[str, str | None]],
    contributes_custom_editors: list[dict] | None = None,
    publisher_name: str | None = None,
    contributes_commands: list[dict] | None = None,
    contributes_authentication: list[dict] | None = None,
    contributes_views: dict[str, Any] | None = None,
    contributes_debuggers: list[dict] | None = None,
    contributes_walkthroughs: list[dict] | None = None,
    contributes_task_definitions: list[dict] | None = None,
    contributes_terminal_profiles: list[dict] | None = None,
    capability_metadata: dict[str, Any] | None = None,
) -> TriggerPayload:
    """Compile declared activation metadata into a layered stimulus payload."""

    selected_candidates: set[str] = set()
    official_candidates: set[str] = set()
    heuristic_candidates: set[str] = set()
    scenario_scores: dict[str, int] = {}
    scenario_reasons: dict[str, set[str]] = {}
    official_extra_capabilities: set[str] = set()
    heuristic_extra_capabilities: set[str] = set()
    payload = _TriggerPayloadDraft(target_extension_id=publisher_name)
    contributed_view_ids = _collect_contributed_view_ids(contributes_views)

    def mark_scenario(
        name: str,
        *,
        reason: str,
        score: int,
        track: str,
    ) -> None:
        if name not in _SCENARIO_BY_NAME:
            return
        selected_candidates.add(name)
        scenario_scores[name] = max(score, scenario_scores.get(name, 0))
        scenario_reasons.setdefault(name, set()).add(reason)
        if track == _OFFICIAL_TRACK:
            official_candidates.add(name)
        else:
            heuristic_candidates.add(name)

    compiled_attempts: dict[tuple[str, str], dict[str, Any]] = {}

    def register_attempt(
        *,
        event_type: str,
        event_value: str | None,
        track: str,
        reason: str,
        selected_by: str = "activation_event",
    ) -> None:
        key = (track, _activation_label(event_type, event_value))
        if key in compiled_attempts:
            compiled_attempts[key]["selection_reasons"] = sorted(
                set(compiled_attempts[key]["selection_reasons"]) | {reason}
            )
            return
        strategy = OFFICIAL_EVENT_REGISTRY.get(event_type)
        if strategy is None:
            return
        compiled_attempts[key] = _build_event_attempt(
            strategy=strategy,
            event_type=event_type,
            event_value=event_value,
            track=track,
            reason=reason,
            publisher_name=publisher_name,
            selected_by=selected_by,
        )

    for event in activation_events:
        _apply_activation_event(
            event,
            payload=payload,
            publisher_name=publisher_name,
            contributed_view_ids=contributed_view_ids,
            official_extra_capabilities=official_extra_capabilities,
            mark_scenario=mark_scenario,
            register_attempt=register_attempt,
        )

    _apply_contributes_metadata(
        payload=payload,
        contributes_custom_editors=contributes_custom_editors,
        contributes_commands=contributes_commands,
        contributes_authentication=contributes_authentication,
        contributes_views=contributes_views,
        contributes_debuggers=contributes_debuggers,
        contributes_walkthroughs=contributes_walkthroughs,
        contributes_task_definitions=contributes_task_definitions,
        contributes_terminal_profiles=contributes_terminal_profiles,
        capability_metadata=capability_metadata,
        heuristic_extra_capabilities=heuristic_extra_capabilities,
        official_extra_capabilities=official_extra_capabilities,
        mark_scenario=mark_scenario,
    )
    _apply_default_fallback(
        selected_candidates=selected_candidates,
        compiled_attempts=compiled_attempts,
        mark_scenario=mark_scenario,
    )
    return _finalize_payload(
        payload=payload,
        selected_candidates=selected_candidates,
        official_candidates=official_candidates,
        heuristic_candidates=heuristic_candidates,
        scenario_scores=scenario_scores,
        scenario_reasons=scenario_reasons,
        compiled_attempts=compiled_attempts,
        official_extra_capabilities=official_extra_capabilities,
        heuristic_extra_capabilities=heuristic_extra_capabilities,
    )
