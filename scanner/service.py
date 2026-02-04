"""
scanner/service.py
==================

Business Logic Layer for Extension Operations
----------------------------------------------

This module serves as the Service Layer (Business Logic Layer) in the
application's layered architecture. It orchestrates operations between
the API layer (routers) and the data access layer (CRUD).

Architecture Position:
    Router (API) → **Service (Business Logic)** → CRUD (Data Access) → Database
                                                ↘ JSON Parser (File System)

Responsibilities:
    1. Coordinate between multiple data sources (DB + filesystem)
    2. Implement business rules and validation logic
    3. Transform data between layers as needed
    4. Handle cross-cutting concerns before they reach CRUD

Why a Service Layer?
    - Keeps routers thin and focused on HTTP concerns
    - Enables reuse of business logic across different endpoints
    - Provides a natural place for transaction management
    - Simplifies unit testing by isolating business rules

Current Functions:
    - get_all_extensions_basic: List extensions with minimal data
    - get_all_extensions_all: List extensions with full data
    - search_extension_by_name: Find extension in database
    - create_extension_by_name: Scan filesystem and persist to database
    - delete_extension_by_name: Remove extension from database
    - get_extension_scripts: Retrieve npm scripts for an extension
    - get_extension_activation_events: Retrieve activation events
    - get_extension_capabilites: Retrieve capability declarations
    - get_extension_contributes_all: Retrieve contributes container
    - get_extension_contributes_commands: Retrieve command contributions

Future Enhancements:
    - Malware pattern detection
    - Caching layer integration
    - Batch processing operations
"""

from __future__ import annotations

from sqlalchemy.orm import Session

# Aliased imports to avoid naming conflicts between service and CRUD functions
# This is a common pattern when service methods wrap CRUD operations
from crud.crud import create_extension as create_db_extension
from crud.crud import delete_extension as delete_db_extension
from crud.crud import get_db_extensions_base_info, get_extensions_all_info
from crud.crud import (
    get_extension_activation_events as get_db_extension_activation_events,
)
from crud.crud import get_extension_capabilities as get_db_extension_capabilities
from crud.crud import get_extension_contributes_all as get_db_extension_contributes
from crud.crud import (
    get_extension_contributes_commands as get_db_extension_contributes_commands,
)
from crud.crud import get_extension_scripts as get_db_extension_scripts
from crud.crud import search_extension_by_name as search_db_extension
from models.models import (
    Extension,
    ExtensionActivationEvents,
    ExtensionCapabilities,
    ExtensionContributes,
    ExtensionContributesCommands,
    ExtensionScripts,
)
from schemas.schemas import (
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

# File system operations for scanning extensions directory
from .json_parser import (
    parse_activation_events,
    parse_capabilities,
    parse_contributes,
    parse_extra_fields,
    parse_npm_fields,
    parse_scripts,
)
from .json_parser import search_extension as find_json_in_dir


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
        # Step 2: Validate and convert to Pydantic schema
        # This performs full validation of the package.json data
        # against ExtensionSchema. Invalid data raises ValidationError.
        # The `extra="ignore"` config silently drops unknown fields.
        # npm_fields and extra_fields are extracted separately and stored in JSONB.
        npm_fields_data = parse_npm_fields(package_json)
        extra_fields_data = parse_extra_fields(package_json)
        package_schema = ExtensionSchema(
            **package_json, npm_fields=npm_fields_data, extra_fields=extra_fields_data
        )

        # Step 2.5: Parse capabilities from package.json
        capabilities_data = parse_capabilities(package_json)
        capabilities_schema = (
            ExtensionCapabilitiesSchema(**capabilities_data)
            if capabilities_data
            else None
        )

        # Step 2.6: Parse scripts from package.json
        scripts_data = parse_scripts(package_json)
        scripts_schema = (
            [ExtensionScriptsSchema(**script) for script in scripts_data]
            if scripts_data
            else None
        )

        # Step 2.7: Parse activation events from package.json
        activation_events_data = parse_activation_events(package_json)
        activation_events_schema = (
            [
                ExtensionActivationEventsSchema(**event)
                for event in activation_events_data
            ]
            if activation_events_data
            else None
        )

        # Step 2.8: Parse contributes from package.json
        contributes_data = parse_contributes(package_json)
        contributes_schema = None
        if contributes_data:
            # Build child schemas from parsed data
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

        # Step 3: Persist to database via CRUD layer
        # create_db_extension handles:
        # - ORM model creation
        # - Transaction commit
        # - Duplicate detection (raises ValueError)
        return create_db_extension(
            db,
            package_schema,
            capabilities_schema,
            scripts_schema,
            activation_events_schema,
            contributes_schema,
        )

    # Extension not found in filesystem
    return None


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


def get_extension_capabilites(
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
    extension_capabilites = get_db_extension_capabilities(
        db, extension_name, extension_publisher, extension_version
    )
    return extension_capabilites


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
