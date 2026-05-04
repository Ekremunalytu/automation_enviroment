"""Planner helpers for event attempts, passes, and prerequisites."""

from __future__ import annotations

from typing import Any

from packages.analysis_contracts import validate_executor_action
from packages.analysis_planner.io import _activation_label, _slugify
from packages.analysis_planner.registry import (
    _BUILTIN_VIEW_IDS,
    _HEURISTIC_TRACK,
    _OFFICIAL_TRACK,
    _PASS_DESCRIPTIONS,
    _PASS_LABELS,
    _PASS_ORDER,
)


def _build_event_attempt(
    *,
    strategy,
    event_type: str,
    event_value: str | None,
    track: str,
    reason: str,
    publisher_name: str | None,
    selected_by: str,
) -> dict[str, Any]:
    activation_event = _activation_label(event_type, event_value)
    # W10-5: validate at the producer boundary so any typo in
    # _resolve_executor_action raises here instead of bubbling to the
    # playwright dispatcher's "Unsupported stimulus action" branch.
    executor_action = validate_executor_action(
        _resolve_executor_action(
            strategy.family,
            event_value,
            publisher_name=publisher_name,
        )
    )
    backfill_executor_action = validate_executor_action(
        f"harness:{strategy.harness_fallback}" if strategy.harness_fallback else ""
    )
    pass_name = _choose_primary_pass(strategy.family, track)
    backfill_pass_name = "unresolved_event_backfill" if backfill_executor_action else ""
    return {
        "attempt_id": _slugify(f"{track}-{activation_event}"),
        "declared_event": activation_event,
        "activation_event": activation_event,
        "event_family": strategy.family,
        "event_value": str(event_value or ""),
        "track": track,
        "selected_by": selected_by,
        "selection_reasons": [reason],
        "pass_name": pass_name,
        "backfill_pass_name": backfill_pass_name,
        "prerequisite_keys": list(strategy.prerequisites),
        "verification_contract": list(strategy.verification_contract),
        "trigger_method": _choose_trigger_method(strategy.family, executor_action),
        "fallback_trigger_method": "harness_api" if backfill_executor_action else "",
        "executor_action": executor_action,
        "backfill_executor_action": backfill_executor_action,
        "legacy_scenarios": list(strategy.legacy_scenarios),
        "capability_tags": list(strategy.capability_tags),
        "status": "planned",
        "trigger_method_used": "",
        "attempted_passes": [],
        "evidence": [],
        "verification_status": "not_attempted",
        "failure_reason_code": "",
        "blocked_reason_code": "",
        "result_details": "",
        "official": track == _OFFICIAL_TRACK,
        "heuristic": track == _HEURISTIC_TRACK,
        "ui_path": strategy.ui_path,
        "harness_fallback": strategy.harness_fallback or "",
    }


def _build_stimulus_passes(
    event_attempts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    passes: dict[str, dict[str, Any]] = {
        pass_name: {
            "pass_id": pass_name,
            "label": _PASS_LABELS[pass_name],
            "order": index,
            "description": _PASS_DESCRIPTIONS[pass_name],
            "attempt_ids": [],
            "prerequisite_keys": [],
        }
        for index, pass_name in enumerate(_PASS_ORDER, start=1)
    }
    for attempt in event_attempts:
        pass_name = str(attempt.get("pass_name", "")).strip()
        if pass_name in passes:
            passes[pass_name]["attempt_ids"].append(str(attempt.get("attempt_id", "")))
            passes[pass_name]["prerequisite_keys"].extend(
                str(item) for item in attempt.get("prerequisite_keys", [])
            )
        backfill_pass = str(attempt.get("backfill_pass_name", "")).strip()
        if backfill_pass in passes and attempt.get("backfill_executor_action"):
            passes[backfill_pass]["attempt_ids"].append(
                str(attempt.get("attempt_id", ""))
            )
            passes[backfill_pass]["prerequisite_keys"].extend(
                str(item) for item in attempt.get("prerequisite_keys", [])
            )
    for pass_data in passes.values():
        pass_data["attempt_ids"] = [
            attempt_id
            for attempt_id in dict.fromkeys(pass_data["attempt_ids"])
            if attempt_id
        ]
        pass_data["prerequisite_keys"] = [
            item for item in dict.fromkeys(pass_data["prerequisite_keys"]) if item
        ]
        pass_data["status"] = "planned"
    return [passes[pass_name] for pass_name in _PASS_ORDER]


def _build_prerequisite_results(
    event_attempts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    prerequisites: dict[str, dict[str, Any]] = {}
    for attempt in event_attempts:
        attempt_id = str(attempt.get("attempt_id", ""))
        pass_name = str(attempt.get("pass_name", ""))
        for key in attempt.get("prerequisite_keys", []):
            prep_key = str(key).strip()
            if not prep_key:
                continue
            entry = prerequisites.setdefault(
                prep_key,
                {
                    "prerequisite_id": _slugify(f"prep-{prep_key}"),
                    "key": prep_key,
                    "label": prep_key.replace("_", " "),
                    "status": "planned",
                    "materializer": _materializer_for_prerequisite(prep_key),
                    "pass_name": pass_name,
                    "attempt_ids": [],
                    "detail": _detail_for_prerequisite(prep_key),
                },
            )
            entry["attempt_ids"].append(attempt_id)
    return [
        {
            **value,
            "attempt_ids": [
                attempt_id
                for attempt_id in dict.fromkeys(value["attempt_ids"])
                if attempt_id
            ],
        }
        for value in prerequisites.values()
    ]


def _summarize_event_attempts(
    attempts: list[dict[str, Any]],
    *,
    track: str,
) -> dict[str, Any]:
    selected = [attempt for attempt in attempts if attempt.get("track") == track]
    verified = [attempt for attempt in selected if attempt.get("status") == "verified"]
    attempted_only = [
        attempt for attempt in selected if attempt.get("status") == "attempted_only"
    ]
    failed = [attempt for attempt in selected if attempt.get("status") == "failed"]
    blocked = [attempt for attempt in selected if attempt.get("status") == "blocked"]
    return {
        "track": track,
        "declared": len(selected),
        "verified": len(verified),
        "attempted_only": len(attempted_only),
        "failed": len(failed),
        "blocked": len(blocked),
        "unresolved": max(len(selected) - len(verified), 0),
        "declared_events": [
            str(attempt.get("activation_event", ""))
            for attempt in selected
            if str(attempt.get("activation_event", "")).strip()
        ],
    }


def _choose_primary_pass(family: str, track: str) -> str:
    if track == _HEURISTIC_TRACK:
        return "ui_first_user_session"
    if family in {"workspaceContains", "*", "onStartupFinished"}:
        return "workspace_bootstrap"
    if family in {"onLanguage", "onCommand", "onSearch", "onView"}:
        return "ui_first_user_session"
    return "target_specific_activation"


def _choose_trigger_method(family: str, executor_action: str) -> str:
    if family in {"onCustomEditor", "workspaceContains"}:
        return "mixed"
    if executor_action.startswith("scenario:") or executor_action.startswith(
        "command:"
    ):
        return "ui_simulation"
    if executor_action.startswith("extra:"):
        return "mixed"
    if executor_action.startswith("harness:"):
        return "harness_api"
    if executor_action.startswith("fixture:"):
        return "workspace_fixture"
    return "ui_simulation"


def _resolve_executor_action(
    family: str,
    event_value: str | None,
    *,
    publisher_name: str | None,
) -> str:
    value = str(event_value or "").strip()
    if family == "onCommand":
        return "scenario:coding_session" if not value else "command:auto"
    if family == "onLanguage":
        return "scenario:coding_session"
    if family in {
        "onDebug",
        "onDebugAdapterProtocolTracker",
        "onDebugDynamicConfigurations",
        "onDebugInitialConfigurations",
        "onDebugResolve",
    }:
        return "extra:debug_lifecycle"
    if family == "workspaceContains":
        return "scenario:project_exploration"
    if family in {"onNotebook", "onRenderer"}:
        return "scenario:notebook_session"
    if family == "onTaskType":
        return "extra:task_trigger"
    if family in {"onTerminal", "onTerminalProfile", "onTerminalShellIntegration"}:
        return "scenario:terminal_usage"
    if family in {
        "onAuthenticationRequest",
        "onChatParticipant",
        "onLanguageModelTool",
    }:
        return "harness:run_current_stimulus"
    if family == "onWebviewPanel":
        return "harness:run_current_stimulus"
    if family == "onWalkthrough":
        return "extra:walkthrough"
    if family == "onOpenExternalUri":
        return "harness:run_current_stimulus"
    if family == "onUri":
        if publisher_name:
            return "extra:uri_trigger"
        return "harness:run_current_stimulus"
    if family == "onCustomEditor":
        return "extra:custom_editor"
    if family == "onFileSystem":
        return "harness:run_current_stimulus"
    if family == "onEditSession":
        return "harness:run_current_stimulus"
    if family == "onIssueReporterOpened":
        return "command:Help: Report Issue"
    if family == "onSearch":
        return "scenario:search_workflow"
    if family in {"onStartupFinished", "*"}:
        return "fixture:startup_observe"
    if family == "onView":
        if value in _BUILTIN_VIEW_IDS:
            return f"command:View: Show {value}"
        return "harness:run_current_stimulus"
    return "harness:run_current_stimulus"


def _materializer_for_prerequisite(key: str) -> str:
    if key in {
        "language_fixture",
        "workspace_contains_fixture",
        "searchable_workspace",
    }:
        return "workspace_fixture"
    if key in {"custom_editor_bait_files", "notebook_fixture", "renderer_fixture"}:
        return "workspace_fixture"
    if key in {"debug_launch_config", "task_definition_target"}:
        return "workspace_fixture"
    return "harness_api"


def _detail_for_prerequisite(key: str) -> str:
    details = {
        "auth_request_target": (
            "Provider or consumer id must be available inside the sandbox."
        ),
        "chat_participant_target": (
            "Chat participant id is staged for local-only invocation."
        ),
        "command_target": (
            "Command title/id is resolved through contributes.commands when present."
        ),
        "custom_editor_bait_files": (
            "Create bait files that match contributes.customEditors selectors."
        ),
        "debug_launch_config": (
            "Ensure launch.json and debuggable files exist before the debug flow."
        ),
        "edit_session_fixture": (
            "Prepare edit-session commands or local stubs before stimulation."
        ),
        "filesystem_scheme_target": (
            "Custom filesystem scheme must be reachable locally."
        ),
        "language_fixture": (
            "Prepare a file that resolves to the declared language id."
        ),
        "language_model_tool_target": (
            "Language-model tool id is prepared for local-only invocation."
        ),
        "notebook_fixture": (
            "Create a notebook document and any required output content."
        ),
        "loopback_uri_target": (
            "Use a loopback-only URI target; no external service calls are allowed."
        ),
        "renderer_fixture": (
            "Materialize notebook output so renderer activation can be observed."
        ),
        "searchable_workspace": (
            "Prepare a workspace tree that VS Code can search deterministically."
        ),
        "task_definition_target": (
            "Task definitions must exist before Tasks: Run Task is invoked."
        ),
        "terminal_profile_target": (
            "Terminal profile ids must be available before profile launch."
        ),
        "terminal_shell_target": (
            "Terminal shell type must be selected before the terminal opens."
        ),
        "uri_target": (
            "Target vscode:// URI is staged from the publisher.name identifier."
        ),
        "view_target": "The contributed view id is prepared for expansion.",
        "walkthrough_target": (
            "Walkthrough id is prepared for the Getting Started flow."
        ),
        "webview_target": (
            "Restore context for the target webview panel before backfill."
        ),
        "workspace_contains_fixture": (
            "Create the file pattern expected by workspaceContains."
        ),
        "workspace_ready": (
            "VS Code workbench must finish loading before startup events are assessed."
        ),
    }
    return details.get(key, "")
