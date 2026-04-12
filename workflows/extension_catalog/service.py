"""Extension catalog workflow service."""

from __future__ import annotations

from pathlib import Path
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
from appcore.storage.crud import (
    delete_extension as delete_db_extension,
)
from appcore.storage.crud import (
    get_db_extensions_base_info,
    get_extensions_all_info,
)
from appcore.storage.crud import (
    get_extension_activation_events as get_db_extension_activation_events,
)
from appcore.storage.crud import (
    get_extension_capabilities as get_db_extension_capabilities,
)
from appcore.storage.crud import (
    get_extension_contributes_all as get_db_extension_contributes,
)
from appcore.storage.crud import (
    get_extension_contributes_commands as get_db_extension_contributes_commands,
)
from appcore.storage.crud import (
    get_extension_scripts as get_db_extension_scripts,
)
from appcore.storage.crud import (
    search_extension_by_name as search_db_extension,
)
from appcore.storage.models import (
    Extension,
    ExtensionActivationEvents,
    ExtensionCapabilities,
    ExtensionContributes,
    ExtensionContributesCommands,
    ExtensionScripts,
)

from .manifest_parser import (
    parse_activation_events,
    parse_capabilities,
    parse_contributes,
    parse_extra_fields,
    parse_npm_fields,
    parse_scripts,
)
from .manifest_reader import get_package_json
from .manifest_reader import search_extension as find_json_in_dir


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


def get_all_extensions_basic(db: Session) -> list[Extension]:
    """
    Retrieve all extensions with basic information only.

    This is a pass-through to CRUD for simple listing operations.
    Returns optimized payload suitable for gallery/grid displays.

    Args:
        db: SQLAlchemy database session from dependency injection

    Returns:
        List of Extension objects with only id, name, version, publisher,
        description, and icon fields loaded

    Example:
        >>> extensions = get_all_extensions_basic(db)
        >>> # Returns lightweight objects for listing

    Use Cases:
        - Extension gallery/marketplace view
        - Search results listing
        - Extension selector dropdowns
    """
    all_extensions_basic_information = get_db_extensions_base_info(db)
    return all_extensions_basic_information


def get_all_extensions_all(
    db: Session, skip: int = 0, limit: int | None = None
) -> list[Extension]:
    """
    Retrieve all extensions with complete information from the database.

    Returns full extension data including all metadata fields.
    Use sparingly due to larger payload size.

    Args:
        db: SQLAlchemy database session from dependency injection
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (for pagination)

    Returns:
        List of Extension objects with all columns loaded

    Example:
        >>> extensions = get_all_extensions_all(db)
        >>> # Returns complete objects for detailed analysis

    Use Cases:
        - Data export functionality
        - Detailed comparison views
        - Administrative reports
    """
    return get_extensions_all_info(db, skip=skip, limit=limit)


def search_extension_by_name(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> Extension | None:
    """
    Search for an extension by name in the database.

    Performs an exact-match database lookup. The result is returned
    directly as FastAPI's response_model handles Pydantic conversion.

    Args:
        db: SQLAlchemy database session from dependency injection
        extension_name: Exact name of extension to find
        extension_publisher: Optional publisher filter (recommended for uniqueness)
        extension_version: Optional version filter

    Returns:
        Extension ORM object if found, None otherwise

    Note:
        FastAPI's response_model automatically converts the SQLAlchemy
        Extension object to ExtensionSchema for the JSON response.
        No manual conversion needed in the service layer.

        The unique constraint is (publisher, name, version). For unambiguous
        results, provide all three parameters.

    Example:

        >>> result = search_extension_by_name(db, "python", "ms-python", "1.0.0")
        >>> if result:
        ...     # Extension found, will be serialized by FastAPI
        ...     return result
        ... else:
        ...     # Not found, router should return 404
        ...     raise HTTPException(404)


    Search Strategy:
        Currently: Exact match only (case-sensitive)
        Future: Could add fuzzy search, LIKE queries, or full-text search
    """
    # Delegate to CRUD layer for database query
    extension = search_db_extension(
        db, extension_name, extension_publisher, extension_version
    )

    # Return as-is; FastAPI's response_model handles serialization
    # from SQLAlchemy ORM object to Pydantic schema automatically
    return extension


def delete_extension_by_name(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> bool:
    """
    Delete an extension by name from the database.

    Args:
        db: SQLAlchemy database session
        extension_name: Name of extension to delete
        extension_publisher: Optional publisher filter (recommended for uniqueness)
        extension_version: Optional version filter

    Returns:
        True if deleted, False if not found

    Note:
        The unique constraint is (publisher, name, version). For unambiguous
        deletion, provide all three parameters.
    """
    return delete_db_extension(
        db, extension_name, extension_publisher, extension_version
    )


def create_extension_by_name(db: Session, extension_name: str) -> Extension | None:
    """
    Create a new extension by scanning for it in the filesystem.

    This is the main "scan and store" workflow:
    1. Search the extensions/ directory for matching package.json
    2. Validate the package.json data against Pydantic schema
    3. Persist the validated data to the PostgreSQL database

    This function bridges the gap between filesystem scanning and
    database persistence, implementing the core scanning logic.

    Args:
        db: SQLAlchemy database session from dependency injection
        extension_name: Name to search for in package.json files

    Returns:
        Extension ORM object if successfully created, None if not found

    Raises:
        ValueError: If extension already exists (from CRUD layer)
        ValidationError: If package.json fails Pydantic validation

    Workflow:
        ┌─────────────────┐
        │ Extension Name  │
        └────────┬────────┘
                 ↓
        ┌─────────────────────────────────────┐
        │ Step 1: Scan extensions/ directory  │
        │ Look for matching package.json      │
        └────────┬────────────────────────────┘
                 ↓
        ┌─────────────────────────────────────┐
        │ Step 2: Validate with Pydantic      │
        │ ExtensionSchema(**package_json)     │
        └────────┬────────────────────────────┘
                 ↓
        ┌─────────────────────────────────────┐
        │ Step 3: Persist to PostgreSQL       │
        │ create_db_extension(db, schema)     │
        └────────┬────────────────────────────┘
                 ↓
        ┌─────────────────┐
        │ Extension ORM   │
        └─────────────────┘

    Example:
        >>> result = create_extension_by_name(db, "python")
        >>> if result:
        ...     print(f"Created extension with ID: {result.id}")
        ... else:
        ...     print("Extension not found in filesystem")

    Error Handling:
        - Package.json not found → Returns None
        - Validation failure → Pydantic ValidationError propagates
        - Duplicate entry → ValueError propagates to router
    """
    # Step 1: Search for package.json in extensions/ directory
    # find_json_in_dir iterates through subdirectories looking for
    # a package.json where the "name" field matches extension_name
    package_json = find_json_in_dir(extension_name)

    if package_json:
        return _create_extension_from_package_json(db, package_json)

    # Extension not found in filesystem
    return None


def create_extension_from_directory(
    db: Session,
    extension_dir: Path,
    *,
    expected_name: str | None = None,
    expected_publisher: str | None = None,
    expected_version: str | None = None,
) -> Extension | None:
    """Create an extension record from a specific extracted extension directory."""
    package_json = get_package_json(extension_dir)
    if package_json is None:
        return None

    _validate_manifest_identity(
        package_json,
        expected_name=expected_name,
        expected_publisher=expected_publisher,
        expected_version=expected_version,
    )
    return _create_extension_from_package_json(db, package_json)


def get_extension_scripts(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> list[ExtensionScripts] | None:
    """
    Retrieve all scripts defined in an extension's package.json.

    Scripts are npm-style commands defined in the "scripts" section
    of package.json (e.g., build, test, lint commands).
    """
    extension_scripts = get_db_extension_scripts(
        db, extension_name, extension_publisher, extension_version
    )
    return extension_scripts


def get_extension_activation_events(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> list[ExtensionActivationEvents] | None:
    """
    Retrieve all activation events for a specific extension.

    Activation events define when a VS Code extension becomes active.
    """
    extension_activation_events = get_db_extension_activation_events(
        db, extension_name, extension_publisher, extension_version
    )
    return extension_activation_events


def get_extension_capabilities(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> ExtensionCapabilities | None:
    """
    Retrieve capability declarations for a specific extension.

    Capabilities define how an extension behaves in restricted environments:
        - untrustedWorkspaces
        - virtualWorkspaces
    """
    extension_capabilities = get_db_extension_capabilities(
        db, extension_name, extension_publisher, extension_version
    )
    return extension_capabilities


def get_extension_contributes_all(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> ExtensionContributes | None:
    extension_contributes = get_db_extension_contributes(
        db, extension_name, extension_publisher, extension_version
    )
    return extension_contributes


def get_extension_contributes_commands(
    db: Session,
    extension_name: str,
    extension_publisher: str | None = None,
    extension_version: str | None = None,
) -> list[ExtensionContributesCommands] | None:
    """Retrieve command contributions for a specific extension."""
    return get_db_extension_contributes_commands(
        db, extension_name, extension_publisher, extension_version
    )
