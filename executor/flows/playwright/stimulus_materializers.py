"""Prerequisite materializers and target-resolution helpers for stimuli."""

from __future__ import annotations

import json
from typing import Any

from . import workspace
from .stimulus_types import (
    _HARNESS_CONTEXT_DIR,
    _HARNESS_CONTEXT_PATH,
    _LAUNCH_PATH,
    _TASKS_PATH,
    PrerequisiteMaterialization,
)
from .workspace_seed_data import LANGUAGE_EXTENSIONS


def materialize_task_definition() -> PrerequisiteMaterialization:
    _TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _TASKS_PATH.exists():
        _TASKS_PATH.write_text(
            json.dumps(
                {
                    "version": "2.0.0",
                    "tasks": [
                        {
                            "label": "ExTrace Harness Task",
                            "type": "shell",
                            "command": "echo extrace",
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return completed(
        f"Ensured task definition at {_TASKS_PATH}.",
        {"task_definition": str(_TASKS_PATH)},
    )


def materialize_debug_launch_config() -> PrerequisiteMaterialization:
    workspace.create_workspace_file("src/app.py", "print('debug fixture')\n")
    _LAUNCH_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _LAUNCH_PATH.exists():
        _LAUNCH_PATH.write_text(
            json.dumps(
                {
                    "version": "0.2.0",
                    "configurations": [
                        {
                            "name": "ExTrace Python",
                            "type": "python",
                            "request": "launch",
                            "program": "${workspaceFolder}/src/app.py",
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return completed(
        f"Ensured debug launch config at {_LAUNCH_PATH}.",
        {"debug_launch_config": str(_LAUNCH_PATH)},
    )


def materialize_workspace_contains_fixture(
    attempts: list[dict[str, Any]],
) -> PrerequisiteMaterialization:
    patterns = sorted(
        {
            _resolve_event_value(attempt)
            for attempt in attempts
            if _resolve_event_value(attempt)
        }
    )
    if not patterns:
        return blocked(
            "prerequisite_blocked",
            "workspaceContains prerequisite did not include a filename pattern.",
        )
    created: list[str] = []
    for pattern in patterns:
        try:
            created.extend(create_workspace_contains_fixture(pattern))
        except KeyError:
            return blocked(
                "materialization_failed",
                (
                    "workspaceContains fixture materialization does not support "
                    f"pattern {pattern!r}."
                ),
                {"pattern": pattern},
            )
        except ValueError as exc:
            return blocked(
                "prerequisite_blocked",
                (
                    "workspaceContains pattern rejected by workspace path "
                    f"policy: {pattern!r} ({exc})."
                ),
                {"pattern": pattern},
            )
    return completed(
        f"Prepared workspaceContains fixtures for {', '.join(patterns)}.",
        {"patterns": patterns, "paths": created},
    )


def materialize_language_fixture(
    attempts: list[dict[str, Any]],
) -> PrerequisiteMaterialization:
    languages = sorted(
        {
            language_id
            for attempt in attempts
            for language_id in [_resolve_language_id(attempt)]
            if language_id
        }
    )
    if not languages:
        return blocked(
            "prerequisite_blocked",
            "Language fixture target was unavailable for this attempt.",
        )
    created: list[str] = []
    for language_id in languages:
        try:
            created.extend(ensure_language_fixture(language_id))
        except KeyError:
            return blocked(
                "materialization_failed",
                (f"Language fixture materialization does not support {language_id!r}."),
                {"language_id": language_id},
            )
    return completed(
        f"Prepared language fixtures for {', '.join(languages)}.",
        {"languages": languages, "paths": created},
    )


def materialize_command_target(
    payload: Any,
    attempts: list[dict[str, Any]],
) -> PrerequisiteMaterialization:
    for attempt in attempts:
        command_text = resolve_command_text(payload, attempt)
        if command_text:
            return completed(
                f"Resolved command target {command_text}.",
                {"command_text": command_text},
            )
    return blocked(
        "prerequisite_blocked",
        "Command target metadata was unavailable for this attempt.",
    )


def create_workspace_contains_fixture(pattern: str) -> list[str]:
    normalized = pattern.strip()
    if not normalized:
        return []
    created: list[str] = []

    def create_file(path: str, content: str = "") -> None:
        created.append(str(workspace.create_workspace_file(path, content)))

    def create_dir(path: str) -> None:
        created.append(str(workspace.create_workspace_dir(path)))

    if normalized in {"**/.venv", ".venv"}:
        create_dir(".venv")
        return created
    if normalized in {"**/.conda", ".conda"}:
        create_dir(".conda")
        return created
    fixtures = {
        "Pipfile": '[packages]\nflask = "*"\n',
        "requirements.txt": "flask==3.0.0\n",
        "setup.py": "from setuptools import setup\nsetup(name='extrace')\n",
        "pyproject.toml": '[project]\nname = "extrace"\n',
        "pylock.toml": "[tool.extrace]\nlock = true\n",
        "manage.py": "print('manage')\n",
        "app.py": "print('app fixture')\n",
        "mspythonconfig.json": '{\n  "python.defaultInterpreterPath": "/usr/bin/python3"\n}\n',
    }
    if normalized in fixtures:
        create_file(normalized, fixtures[normalized])
        return created
    if normalized == "**/pylock.*.toml":
        create_file("nested/pylock.dev.toml", '[tool.extrace]\nchannel = "dev"\n')
        return created

    fallback = normalized.replace("**/", "nested/").lstrip("/")
    fallback = fallback.replace("*", "sample").replace("?", "x")
    if not fallback.strip("/"):
        raise KeyError(normalized)
    if fallback.endswith("/"):
        create_dir(fallback.rstrip("/"))
    else:
        create_file(fallback)
    return created


def ensure_language_fixture(language_id: str) -> list[str]:
    created: list[str] = []

    def create(path: str, content: str) -> None:
        created.append(str(workspace.create_workspace_file(path, content)))

    language_fixtures = {
        "python": ("src/app.py", "def main():\n    return 'extrace'\n"),
        "javascript": ("frontend/src/api.js", "export const api = () => 'ok';\n"),
        "typescript": (
            "frontend/src/index.ts",
            "export const version: string = '1.0.0';\n",
        ),
        "go": ("services/api/main.go", "package main\n\nfunc main() {}\n"),
        "rust": ("services/worker/src/main.rs", "fn main() {}\n"),
    }
    if language_id in language_fixtures:
        path, content = language_fixtures[language_id]
        create(path, content)
        return created
    if language_id in LANGUAGE_EXTENSIONS:
        created.append(str(workspace.create_language_file(language_id)))
        return created
    raise KeyError(language_id)


def _resolve_event_value(attempt: dict[str, Any]) -> str:
    event_value = str(attempt.get("event_value", "")).strip()
    if event_value:
        return event_value
    activation_event = str(attempt.get("activation_event", "")).strip()
    if ":" in activation_event:
        return activation_event.split(":", maxsplit=1)[1].strip()
    return ""


def _resolve_language_id(attempt: dict[str, Any]) -> str:
    if str(attempt.get("event_family", "")).strip() != "onLanguage":
        return ""
    return _resolve_event_value(attempt)


def completed(
    detail: str,
    resolved_targets: dict[str, Any] | None = None,
) -> PrerequisiteMaterialization:
    return PrerequisiteMaterialization(
        status="completed",
        detail=detail,
        resolved_targets=dict(resolved_targets or {}),
    )


def blocked(
    reason_code: str,
    detail: str,
    resolved_targets: dict[str, Any] | None = None,
) -> PrerequisiteMaterialization:
    return PrerequisiteMaterialization(
        status="blocked",
        detail=detail,
        reason_code=reason_code,
        resolved_targets=dict(resolved_targets or {}),
    )


def resolve_command_text(payload: Any, attempt: dict[str, Any]) -> str:
    command_id = str(attempt.get("event_value", "")).strip()
    activation_event = str(attempt.get("activation_event", "")).strip()
    if not command_id and activation_event.startswith("onCommand:"):
        command_id = activation_event.split(":", maxsplit=1)[1].strip()

    command_targets = getattr(payload, "command_targets", {}) or {}
    if isinstance(command_targets, dict) and command_id:
        command_text = str(command_targets.get(command_id, "")).strip()
        if command_text:
            return command_text
    if command_id:
        return command_id
    titles = list(getattr(payload, "extra_commands", []) or [])
    return str(titles[0]) if titles else ""


def write_harness_context(
    payload: Any, attempt: dict[str, Any], *, trigger_method: str
) -> None:
    _HARNESS_CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "attempt_id": str(attempt.get("attempt_id", "")),
        "attempt": attempt,
        "trigger_method": trigger_method,
        "resolved_targets": resolve_attempt_targets(payload, attempt),
        "command_targets": dict(getattr(payload, "command_targets", {}) or {}),
        "view_targets": dict(getattr(payload, "view_targets", {}) or {}),
        "auth_provider_ids": list(getattr(payload, "auth_provider_ids", []) or []),
        "webview_view_ids": list(getattr(payload, "webview_view_ids", []) or []),
        "uri_trigger": getattr(payload, "uri_trigger", None),
        "run_task_trigger": bool(getattr(payload, "run_task_trigger", False)),
        "run_walkthrough_trigger": bool(
            getattr(payload, "run_walkthrough_trigger", False)
        ),
    }
    _HARNESS_CONTEXT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def resolve_attempt_targets(payload: Any, attempt: dict[str, Any]) -> dict[str, Any]:
    event_value = _resolve_event_value(attempt)
    view_targets = getattr(payload, "view_targets", {}) or {}
    resolved: dict[str, Any] = {
        "event_value": event_value,
        "command_text": resolve_command_text(payload, attempt),
        "view_target": dict(view_targets.get(event_value, {}))
        if isinstance(view_targets, dict) and event_value in view_targets
        else {},
        "uri_trigger": getattr(payload, "uri_trigger", None),
        "auth_provider_ids": list(getattr(payload, "auth_provider_ids", []) or []),
        "webview_view_ids": list(getattr(payload, "webview_view_ids", []) or []),
    }
    family = str(attempt.get("event_family", "")).strip()
    if family == "onLanguageModelTool":
        resolved["language_model_tool_id"] = event_value
    if family in {"onTerminal", "onTerminalShellIntegration"}:
        resolved["terminal_shell"] = event_value or "bash"
    if family == "onTerminalProfile":
        resolved["terminal_profile"] = event_value
    return resolved
