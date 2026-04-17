"""Trigger payload helpers for marketplace analysis."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from appcore.api.config import settings
from appcore.contracts.schemas import AnalyzeRequest
from appcore.storage.crud import (
    get_extension_activation_events,
    get_extension_capabilities,
    get_extension_contributes_all,
)
from packages.analysis_planner import select_scenarios, write_trigger_file

logger = logging.getLogger(__name__)

_NON_EXECUTABLE_CONTRIBUTE_FIELDS = (
    "themes",
    "iconThemes",
    "productIconThemes",
    "colors",
    "snippets",
)
_EXECUTABLE_CONTRIBUTE_FIELDS = (
    "authentication",
    "breakpoints",
    "commands",
    "configuration",
    "configurationDefaults",
    "customEditors",
    "debuggers",
    "grammars",
    "jsonValidation",
    "keybindings",
    "languages",
    "menus",
    "taskDefinitions",
    "terminal",
    "typescriptServerPlugins",
    "views",
    "viewsContainers",
    "viewsWelcome",
    "walkthroughs",
)


@dataclass(frozen=True, slots=True)
class TriggerPlan:
    trigger_container_path: str | None
    selected_scenarios: list[str]
    skip_automation: bool
    reason_code: str
    message: str


def _is_mock_like(value: object) -> bool:
    return value.__class__.__module__.startswith("unittest.mock")


def _has_meaningful_contribute_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list | tuple | set | dict):
        return bool(value)
    return True


def _is_non_executable_fixture(contributes: object | None) -> bool:
    if contributes is None:
        return False
    if any(
        _has_meaningful_contribute_value(getattr(contributes, field, None))
        for field in _EXECUTABLE_CONTRIBUTE_FIELDS
    ):
        return False
    return any(
        _has_meaningful_contribute_value(getattr(contributes, field, None))
        for field in _NON_EXECUTABLE_CONTRIBUTE_FIELDS
    )


def build_trigger_payload(
    db: Session,
    request: AnalyzeRequest,
) -> TriggerPlan:
    if request.scenario:
        return TriggerPlan(
            trigger_container_path=None,
            selected_scenarios=[],
            skip_automation=False,
            reason_code="explicit_scenario",
            message="Explicit scenario selected; smart trigger selection skipped.",
        )

    activation_events = (
        get_extension_activation_events(
            db,
            extension_name=request.name,
            extension_publisher=request.publisher,
            extension_version=request.version,
        )
        or []
    )
    contributes = get_extension_contributes_all(
        db,
        extension_name=request.name,
        extension_publisher=request.publisher,
        extension_version=request.version,
    )
    capabilities = get_extension_capabilities(
        db,
        extension_name=request.name,
        extension_publisher=request.publisher,
        extension_version=request.version,
    )

    events_data = [
        {"event_type": event.event_type, "event_value": event.event_value}
        for event in activation_events
    ]
    custom_editors = (
        getattr(contributes, "customEditors", None) if contributes else None
    )
    authentication_data = None
    if contributes and getattr(contributes, "authentication", None):
        authentication_data = [
            {
                "auth_id": (
                    item.get("auth_id", "")
                    if isinstance(item, dict)
                    else getattr(item, "auth_id", "")
                ),
                "label": (
                    item.get("label", "")
                    if isinstance(item, dict)
                    else getattr(item, "label", "")
                ),
            }
            for item in getattr(contributes, "authentication", [])
        ]
    views = getattr(contributes, "views", None) if contributes else None
    debuggers = getattr(contributes, "debuggers", None) if contributes else None
    walkthroughs = getattr(contributes, "walkthroughs", None) if contributes else None
    task_definitions = (
        getattr(contributes, "taskDefinitions", None) if contributes else None
    )
    terminal_profiles = getattr(contributes, "terminal", None) if contributes else None
    publisher_name = f"{request.publisher}.{request.name}"
    commands_data = None
    if contributes and getattr(contributes, "commands", None):
        commands_data = [
            {"title": command.title, "command_id": command.command_id}
            for command in getattr(contributes, "commands", [])
        ]

    capability_metadata: dict[str, Any] | None = None
    if capabilities is not None and not _is_mock_like(capabilities):
        capability_metadata = {
            "untrusted_supported": getattr(capabilities, "untrusted_supported", None),
            "untrusted_description": getattr(
                capabilities,
                "untrusted_description",
                None,
            ),
            "virtual_supported": getattr(capabilities, "virtual_supported", None),
            "virtual_description": getattr(
                capabilities,
                "virtual_description",
                None,
            ),
        }
        if not any(value is not None for value in capability_metadata.values()):
            capability_metadata = None

    payload = select_scenarios(
        events_data,
        custom_editors,
        publisher_name,
        contributes_commands=commands_data,
        contributes_authentication=authentication_data,
        contributes_views=views,
        contributes_debuggers=debuggers,
        contributes_walkthroughs=walkthroughs,
        contributes_task_definitions=task_definitions,
        contributes_terminal_profiles=terminal_profiles,
        capability_metadata=capability_metadata,
    )
    if not activation_events and _is_non_executable_fixture(contributes):
        return TriggerPlan(
            trigger_container_path=None,
            selected_scenarios=[],
            skip_automation=True,
            reason_code="non_executable_fixture",
            message=(
                "No stored activation events or executable contribution surfaces "
                "were found; skipping automation for a scenario-zero analysis run."
            ),
        )
    trigger_container_path = write_trigger_file(
        request.publisher,
        request.name,
        request.version,
        payload,
        output_dir=settings.project.OUTPUT_DIR,
    )
    logger.info(
        "Layered stimulus plan: %d scenarios, %d official events for %s.%s",
        len(payload.selected_scenarios),
        getattr(payload, "official_event_coverage", {}).get("declared", 0),
        request.publisher,
        request.name,
    )
    return TriggerPlan(
        trigger_container_path=trigger_container_path,
        selected_scenarios=payload.selected_scenarios,
        skip_automation=False,
        reason_code="generated_trigger_plan",
        message=_build_trigger_summary(
            publisher_name,
            payload.selected_scenarios,
            getattr(payload, "official_event_coverage", {}).get("declared", 0),
            len(getattr(payload, "stimulus_passes", [])),
            trigger_container_path,
        ),
    )


def _build_trigger_summary(
    publisher_name: str,
    selected_scenarios: list[str],
    official_event_count: object,
    pass_count: int,
    trigger_container_path: str,
) -> str:
    return (
        "Trigger requested for "
        f"{publisher_name}: selected {len(selected_scenarios)} "
        "compatibility scenario(s) "
        f"[{', '.join(selected_scenarios) or 'none'}]; "
        f"compiled {official_event_count} official event target(s) "
        f"across {pass_count} pass(es); "
        f"payload written to {trigger_container_path}."
    )


__all__ = ["TriggerPlan", "build_trigger_payload"]
