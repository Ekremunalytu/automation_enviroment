"""Trigger payload helpers for marketplace analysis."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from appcore.api.config import settings
from appcore.contracts.schemas import AnalyzeRequest
from appcore.storage.crud import (
    get_extension_activation_events,
    get_extension_contributes_all,
)
from workflows.marketplace.triggers import select_scenarios, write_trigger_file

logger = logging.getLogger(__name__)


def build_trigger_payload(
    db: Session,
    request: AnalyzeRequest,
) -> tuple[str | None, list[str], str]:
    if request.scenario:
        return None, [], "Explicit scenario selected; smart trigger selection skipped."

    activation_events = get_extension_activation_events(
        db,
        extension_name=request.name,
        extension_publisher=request.publisher,
        extension_version=request.version,
    )
    contributes = get_extension_contributes_all(
        db,
        extension_name=request.name,
        extension_publisher=request.publisher,
        extension_version=request.version,
    )

    if not activation_events:
        return (
            None,
            [],
            "No stored activation events found; using default sandbox flow.",
        )

    events_data = [
        {"event_type": event.event_type, "event_value": event.event_value}
        for event in activation_events
    ]
    custom_editors = contributes.customEditors if contributes else None
    authentication_data = None
    if contributes and contributes.authentication:
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
            for item in contributes.authentication
        ]
    views = contributes.views if contributes else None
    publisher_name = f"{request.publisher}.{request.name}"
    commands_data = None
    if contributes and contributes.commands:
        commands_data = [
            {"title": command.title, "command_id": command.command_id}
            for command in contributes.commands
        ]

    payload = select_scenarios(
        events_data,
        custom_editors,
        publisher_name,
        contributes_commands=commands_data,
        contributes_authentication=authentication_data,
        contributes_views=views,
    )
    trigger_container_path = write_trigger_file(
        request.publisher,
        request.name,
        request.version,
        payload,
        output_dir=settings.project.OUTPUT_DIR,
    )
    logger.info(
        "Smart triggers: %d scenarios for %s.%s",
        len(payload.selected_scenarios),
        request.publisher,
        request.name,
    )
    return (
        trigger_container_path,
        payload.selected_scenarios,
        (
            "Trigger requested for "
            f"{publisher_name}: selected {len(payload.selected_scenarios)} "
            f"scenario(s) [{', '.join(payload.selected_scenarios) or 'none'}]; "
            f"payload written to {trigger_container_path}."
        ),
    )


__all__ = ["build_trigger_payload"]
