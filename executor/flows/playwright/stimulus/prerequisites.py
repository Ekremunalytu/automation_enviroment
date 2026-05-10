"""Prerequisite resolution helpers for layered stimulus execution."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .. import workspace
from .materializers import (
    _resolve_event_value,
    blocked,
    completed,
    materialize_command_target,
    materialize_debug_launch_config,
    materialize_language_fixture,
    materialize_task_definition,
    materialize_workspace_contains_fixture,
)


def materialize_prerequisite(
    prerequisite: dict[str, Any],
    *,
    payload: Any,
    attempts_by_id: dict[str, dict[str, Any]],
    monitor: Any | None,
) -> Any:
    prerequisite_id = str(
        prerequisite.get("prerequisite_id", "") or prerequisite.get("key", "")
    )
    attempts = [
        attempt
        for attempt_id in prerequisite.get("attempt_ids", []) or []
        for attempt in [attempts_by_id.get(str(attempt_id))]
        if attempt is not None
    ]
    result = resolve_prerequisite_materialization(
        str(prerequisite.get("key", "")),
        payload=payload,
        attempts=attempts,
        detail=str(prerequisite.get("detail", "")),
    )
    if monitor is not None:
        monitor.record_prerequisite_result(
            prerequisite_id,
            status=result.status,
            detail=result.detail,
            reason_code=result.reason_code,
            resolved_targets=result.resolved_targets,
        )
    return result


def trigger_item_as_dict(item: Any) -> dict[str, Any] | None:
    if isinstance(item, Mapping):
        return dict(item)
    model_dump = getattr(item, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="python")
        if isinstance(dumped, dict):
            return dumped
    dict_method = getattr(item, "dict", None)
    if callable(dict_method):
        dumped = dict_method()
        if isinstance(dumped, dict):
            return dumped
    return None


def resolve_prerequisite_materialization(
    key: str,
    *,
    payload: Any,
    attempts: list[dict[str, Any]],
    detail: str,
):
    if key == "task_definition_target":
        return materialize_task_definition()
    if key == "debug_launch_config":
        return materialize_debug_launch_config()
    if key == "workspace_contains_fixture":
        return materialize_workspace_contains_fixture(attempts)
    if key == "language_fixture":
        return materialize_language_fixture(attempts)
    if key == "command_target":
        return materialize_command_target(payload, attempts)
    if key == "auth_request_target":
        providers = sorted(
            {
                str(provider_id).strip()
                for provider_id in getattr(payload, "auth_provider_ids", []) or []
                if str(provider_id).strip()
            }
        )
        return (
            completed(
                f"Resolved auth providers: {', '.join(providers)}",
                {"auth_provider_ids": providers},
            )
            if providers
            else blocked(
                "prerequisite_blocked",
                "Authentication request target was not available in the trigger payload.",
            )
        )
    if key == "language_model_tool_target":
        tool_id = next(
            (value for value in (_resolve_event_value(a) for a in attempts) if value),
            "",
        )
        return (
            completed(
                f"Resolved language-model tool target {tool_id}.",
                {"language_model_tool_id": tool_id},
            )
            if tool_id
            else blocked(
                "prerequisite_blocked",
                "Language-model tool id was missing from the trigger payload.",
            )
        )
    if key == "chat_participant_target":
        participant_id = next(
            (value for value in (_resolve_event_value(a) for a in attempts) if value),
            "",
        )
        return (
            completed(
                f"Resolved chat participant {participant_id}.",
                {"chat_participant_id": participant_id},
            )
            if participant_id
            else blocked(
                "prerequisite_blocked",
                "Chat participant id was missing from the trigger payload.",
            )
        )
    if key == "terminal_shell_target":
        shell = next(
            (value for value in (_resolve_event_value(a) for a in attempts) if value),
            "bash",
        )
        return completed(
            f"Using terminal shell target {shell}.", {"terminal_shell": shell}
        )
    if key == "terminal_profile_target":
        profile_id = next(
            (value for value in (_resolve_event_value(a) for a in attempts) if value),
            "",
        )
        return (
            completed(
                f"Resolved terminal profile {profile_id}.",
                {"terminal_profile": profile_id},
            )
            if profile_id
            else blocked(
                "prerequisite_blocked",
                "Terminal profile id was missing from the trigger payload.",
            )
        )
    if key == "view_target":
        view_id = next(
            (value for value in (_resolve_event_value(a) for a in attempts) if value),
            "",
        )
        view_targets = getattr(payload, "view_targets", {}) or {}
        if (
            not view_id
            or not isinstance(view_targets, dict)
            or view_id not in view_targets
        ):
            return blocked(
                "prerequisite_blocked",
                "Contributed view target metadata was unavailable for this attempt.",
                {"view_id": view_id},
            )
        return completed(
            f"Resolved view target {view_id}.",
            {"view_id": view_id, "view_target": dict(view_targets.get(view_id, {}))},
        )
    if key == "webview_target":
        view_id = next(
            (value for value in (_resolve_event_value(a) for a in attempts) if value),
            "",
        )
        webview_ids = [
            str(item).strip()
            for item in getattr(payload, "webview_view_ids", []) or []
            if str(item).strip()
        ]
        resolved_id = view_id or (webview_ids[0] if webview_ids else "")
        return (
            completed(
                f"Resolved webview target {resolved_id}.",
                {"webview_view_id": resolved_id},
            )
            if resolved_id
            else blocked(
                "prerequisite_blocked",
                "Webview target metadata was unavailable for this attempt.",
            )
        )
    if key == "uri_target":
        uri = str(getattr(payload, "uri_trigger", "") or "").strip()
        return (
            completed(f"Resolved URI target {uri}.", {"uri_trigger": uri})
            if uri
            else blocked(
                "prerequisite_blocked",
                "Target vscode URI was unavailable for this attempt.",
            )
        )
    if key == "loopback_uri_target":
        uri = (
            str(getattr(payload, "uri_trigger", "") or "").strip()
            or "http://127.0.0.1/extrace"
        )
        return completed(f"Resolved loopback URI target {uri}.", {"uri_trigger": uri})
    if key == "walkthrough_target":
        walkthrough_id = next(
            (value for value in (_resolve_event_value(a) for a in attempts) if value),
            "",
        )
        if not walkthrough_id and getattr(payload, "run_walkthrough_trigger", False):
            walkthrough_id = "walkthrough"
        return (
            completed(
                f"Resolved walkthrough target {walkthrough_id}.",
                {"walkthrough_id": walkthrough_id},
            )
            if walkthrough_id
            else blocked(
                "prerequisite_blocked",
                "Walkthrough target metadata was unavailable for this attempt.",
            )
        )
    if key == "custom_editor_bait_files":
        filenames = [
            str(item).strip()
            for item in getattr(payload, "extra_custom_editor_files", []) or []
            if str(item).strip()
        ]
        if not filenames:
            return blocked(
                "prerequisite_blocked",
                "Custom editor bait files were missing from the trigger payload.",
            )
        created = [str(path) for path in workspace.create_bait_files(filenames)]
        return completed(
            f"Created custom editor bait files: {', '.join(created)}",
            {"bait_files": created},
        )
    if key == "notebook_fixture":
        notebook_files = [
            str(item).strip()
            for item in getattr(payload, "extra_notebook_files", []) or []
            if str(item).strip()
        ] or ["notebooks/analysis.ipynb"]
        created = [
            str(
                workspace.create_workspace_file(
                    # Notebook fixture content is stable across trigger variants.
                    notebook_file,
                    '{\n  "cells": [],\n  "metadata": {},\n  "nbformat": 4,\n  "nbformat_minor": 5\n}\n',
                )
            )
            for notebook_file in notebook_files
        ]
        return completed(
            f"Prepared notebook fixture(s): {', '.join(created)}",
            {"notebook_files": created},
        )
    if key == "renderer_fixture":
        notebook_result = resolve_prerequisite_materialization(
            "notebook_fixture",
            payload=payload,
            attempts=attempts,
            detail=detail,
        )
        if notebook_result.status != "completed":
            return notebook_result
        rendered = str(
            workspace.create_workspace_file(
                "notebooks/renderer-output.txt",
                "renderer output\n",
            )
        )
        return completed(
            f"Prepared renderer fixture {rendered}.",
            {**notebook_result.resolved_targets, "renderer_output": rendered},
        )
    if key == "searchable_workspace":
        created = [
            str(workspace.create_workspace_file("README.md", "# ExTrace\n")),
            str(workspace.create_workspace_file("src/app.py", "print('extrace')\n")),
        ]
        return completed(
            f"Prepared searchable workspace fixture(s): {', '.join(created)}",
            {"paths": created},
        )
    if key == "filesystem_scheme_target":
        scheme = next(
            (value for value in (_resolve_event_value(a) for a in attempts) if value),
            "",
        )
        return (
            completed(
                f"Resolved filesystem scheme {scheme}.", {"filesystem_scheme": scheme}
            )
            if scheme
            else blocked(
                "prerequisite_blocked",
                "Filesystem scheme target was unavailable for this attempt.",
            )
        )
    if key == "edit_session_fixture":
        return blocked(
            "prerequisite_blocked",
            "Edit session stimulus requires harness metadata that was not provided.",
        )
    if key == "workspace_ready":
        return completed(detail or "Workbench readiness prerequisite acknowledged.")
    return completed(detail or f"Prerequisite {key} was acknowledged.")
