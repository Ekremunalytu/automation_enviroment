"""Manifest dict → Pydantic schema → ORM hidrasyon pipeline.

Owns the end-to-end "validated manifest dict in, persisted Extension out"
pipeline: schema hydration, identity validation, and the final
`crud.create_extension` call. Public callers go through `lifecycle.py`
or the back-compat `service.py` facade; they should not import the
private helpers here directly.
"""

from typing import Any

from sqlalchemy.orm import Session

from appcore.contracts.schemas import (
    ExtensionActivationEventsSchema,
    ExtensionCapabilitiesSchema,
    ExtensionContributesAuthenticationSchema,
    ExtensionContributesCommandsSchema,
    ExtensionContributesKeybindingsSchema,
    ExtensionContributesMenusSchema,
    ExtensionContributesSchema,
    ExtensionContributesTerminalSchema,
    ExtensionSchema,
    ExtensionScriptsSchema,
)
from appcore.storage.crud import (
    create_extension as create_db_extension,
)
from appcore.storage.models import Extension

from .manifest_parser import (
    parse_activation_events,
    parse_capabilities,
    parse_contributes,
    parse_extra_fields,
    parse_npm_fields,
    parse_scripts,
)


class ExtensionManifestMismatchError(ValueError):
    """Raised when a package.json does not match the requested extension."""


def _create_extension_from_package_json(
    db: Session,
    package_json: dict[str, Any],
) -> Extension:
    """Validate parsed manifest data and persist it via the CRUD layer."""
    npm_fields_data = parse_npm_fields(package_json)
    extra_fields_data = parse_extra_fields(package_json)
    package_schema = ExtensionSchema(
        **package_json, npm_fields=npm_fields_data, extra_fields=extra_fields_data
    )

    capabilities_data = parse_capabilities(package_json)
    capabilities_schema = (
        ExtensionCapabilitiesSchema(**capabilities_data) if capabilities_data else None
    )

    scripts_data = parse_scripts(package_json)
    scripts_schema = (
        [ExtensionScriptsSchema(**script) for script in scripts_data]
        if scripts_data
        else None
    )

    activation_events_data = parse_activation_events(package_json)
    activation_events_schema = (
        [ExtensionActivationEventsSchema(**event) for event in activation_events_data]
        if activation_events_data
        else None
    )

    contributes_data = parse_contributes(package_json)
    contributes_schema = None
    if contributes_data:
        keybindings = [
            ExtensionContributesKeybindingsSchema(**kb)
            for kb in contributes_data.pop("keybindings", [])
        ]
        menus = [
            ExtensionContributesMenusSchema(**menu)
            for menu in contributes_data.pop("menus", [])
        ]
        authentication = [
            ExtensionContributesAuthenticationSchema(**auth)
            for auth in contributes_data.pop("authentication", [])
        ]
        terminal = [
            ExtensionContributesTerminalSchema(**term)
            for term in contributes_data.pop("terminal", [])
        ]
        commands = [
            ExtensionContributesCommandsSchema(**cmd)
            for cmd in contributes_data.pop("commands", [])
        ]

        contributes_schema = ExtensionContributesSchema(
            **contributes_data,
            keybindings=keybindings,
            menus=menus,
            authentication=authentication,
            terminal=terminal,
            commands=commands,
        )

    return create_db_extension(
        db,
        package_schema,
        capabilities_schema,
        scripts_schema,
        activation_events_schema,
        contributes_schema,
    )


def _validate_manifest_identity(
    package_json: dict[str, Any],
    *,
    expected_name: str | None = None,
    expected_publisher: str | None = None,
    expected_version: str | None = None,
) -> None:
    """Ensure the parsed manifest matches the extension requested by the caller."""
    mismatches: list[str] = []

    if expected_name and package_json.get("name") != expected_name:
        mismatches.append(f"name={package_json.get('name')!r}")
    if expected_publisher and package_json.get("publisher") != expected_publisher:
        mismatches.append(f"publisher={package_json.get('publisher')!r}")
    if expected_version and package_json.get("version") != expected_version:
        mismatches.append(f"version={package_json.get('version')!r}")

    if mismatches:
        raise ExtensionManifestMismatchError(
            "Downloaded extension metadata does not match the requested artifact: "
            + ", ".join(mismatches)
        )
