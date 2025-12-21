"""
crud/crud.py
============

CRUD Operations for Extension Management
-----------------------------------------

This module implements the Data Access Layer (DAL) for the Extension model.
It provides Create, Read, Update, Delete operations following the Repository pattern.

Architecture Position:
    Router → Service → **CRUD** → SQLAlchemy ORM → PostgreSQL Database

Design Principles:
    1. Single Responsibility: Each function does one database operation
    2. Separation of Concerns: No business logic, only data access
    3. Error Handling: Database errors are caught and re-raised for upper layers
    4. Type Safety: Full type hints for IDE support and documentation

Current Implementation Status:
    ✅ Create (create_extension)
    ✅ Read by ID (get_extension_by_id)
    ✅ Read by Name (search_extension_by_name)
    ✅ Read All - Full (get_extensions_all_info)
    ✅ Read All - Partial (get_extensions_base_info)
    ✅ Delete (delete_extension)

SQLAlchemy 2.0 Style:
    This module uses the new SQLAlchemy 2.0 Query API:
    - select() instead of query()
    - scalars() for single-column results
    - where() instead of filter()

Usage Example:
    from crud.crud import create_extension, get_extension_by_id
    from database.session import SessionLocal

    db = SessionLocal()
    try:
        extension = get_extension_by_id(db, extension_id=1)
        if extension:
            print(f"Found: {extension.name}")
    finally:
        db.close()
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, load_only

from models.models import Extension, ExtensionCapabilities, ExtensionScripts
from schemas.schemas import (
    ExtensionCapabilitiesSchema,
    ExtensionSchema,
    ExtensionScriptsSchema,
)


def get_extension_by_id(db: Session, extension_id: int) -> Extension | None:
    """
    Retrieve a single extension by its database ID.

    Performs a primary key lookup which is the most efficient query type
    due to automatic indexing on the primary key column.

    Args:
        db: SQLAlchemy database session
        extension_id: Primary key ID of the extension to retrieve

    Returns:
        Extension object if found, None otherwise

    Example:
        >>> extension = get_extension_by_id(db, 42)
        >>> if extension:
        ...     print(extension.name)

    Performance:
        O(1) - Direct index lookup on primary key
    """
    stmt = select(Extension).where(Extension.id == extension_id)
    return db.scalars(stmt).first()


def search_extension_by_name(
    db: Session, name: str, publisher: str | None = None, version: str | None = None
) -> Extension | None:
    """
    Search for an extension by its exact name.

    Optionally filters by publisher and version.
    Uses indexed columns for efficient lookups.
    Note: This is an exact match search, not a partial/fuzzy search.

    Args:
        db: SQLAlchemy database session
        name: Exact extension name to search for (case-sensitive)
        publisher: Publisher name to filter on (recommended for precise matching)
        version: Specific version to search for (optional)

    Returns:
        Extension object if found, None otherwise

    Raises:
        ValueError: If multiple records match the given filters (ambiguous)

    Example:
        >>> extension = search_extension_by_name(db, "python", "ms-python", "1.0.0")
        >>> if extension:
        ...     print(f"Publisher: {extension.publisher}")

    Note:
        The unique constraint is (publisher, name, version). For unambiguous results,
        provide all three parameters. For partial matching, consider implementing:
        - ILIKE for case-insensitive search
        - Full-text search with PostgreSQL tsvector
        - Trigram similarity for fuzzy matching
    """
    stmt = (
        select(Extension)
        .options(
            joinedload(Extension.capabilities),
            joinedload(Extension.scripts),
        )
        .where(Extension.name == name)
    )
    if publisher:
        stmt = stmt.where(Extension.publisher == publisher)
    if version:
        stmt = stmt.where(Extension.version == version)

    results = db.scalars(stmt).unique().all()
    if not results:
        return None
    if len(results) > 1:
        # Avoid returning an arbitrary record when filters are insufficient
        raise ValueError(
            "Multiple extensions match this name. "
            "Specify publisher and version for an exact match."
        )
    return results[0]


def create_extension(
    db: Session,
    extension: ExtensionSchema,
    capabilities: ExtensionCapabilitiesSchema | None = None,
    scripts: list[ExtensionScriptsSchema] | None = None,
) -> Extension:
    """
    Create a new extension record in the database.

    Converts a Pydantic schema to SQLAlchemy model and persists it.
    Handles duplicate entries via unique constraint violation detection.

    Args:
        db: SQLAlchemy database session
        extension: Pydantic schema containing extension data
        capabilities: Optional Pydantic schema for extension capabilities
        scripts: Optional list of Pydantic schemas for extension scripts

    Returns:
        The created Extension ORM object with populated ID

    Raises:
        ValueError: If extension with same publisher+name+version already exists
        SQLAlchemyError: For other database errors (connection, etc.)

    Example:
        >>> schema = ExtensionSchema(
        ...     name="test", publisher="dev", version="2.3.4",
        ...     engines={"vscode": "^1.0.0"}
        ... )
        >>> try:
        ...     new_ext = create_extension(db, schema)
        ...     print(f"Created with ID: {new_ext.id}")
        ... except ValueError as e:
        ...     print(f"Duplicate: {e}")

    Database Behavior:
        - Uses transaction with automatic rollback on error
        - Unique constraint (publisher, name, version) prevents duplicates
        - Auto-generates ID and created_at timestamp
    """
    # Convert Pydantic model to dict, then to SQLAlchemy model
    db_extension = Extension(**extension.model_dump())

    try:
        db.add(db_extension)
        db.flush()  # Get the ID without committing

        # Create capabilities record if provided
        if capabilities:
            db_capabilities = ExtensionCapabilities(
                extension_id=db_extension.id,
                **capabilities.model_dump(),
            )
            db.add(db_capabilities)

        # Create scripts records if provided
        if scripts:
            for script in scripts:
                db_script = ExtensionScripts(
                    extension_id=db_extension.id,
                    **script.model_dump(),
                )
                db.add(db_script)

        db.commit()
        db.refresh(db_extension)
        return db_extension

    except IntegrityError:
        # Unique constraint violation - duplicate publisher+name+version
        db.rollback()
        # Re-raise as ValueError for router to return 409 Conflict
        raise ValueError("Extension already exists") from None

    except SQLAlchemyError as e:
        # Other database errors (connection issues, etc.)
        db.rollback()
        raise e


def get_extensions_all_info(db: Session) -> list[Extension]:
    """
    Retrieve all extensions with complete information.

    Returns every column for every extension in the database.
    Use with caution for large datasets due to memory implications.

    Args:
        db: SQLAlchemy database session

    Returns:
        List of all Extension objects with full data

    Example:
        >>> all_extensions = get_extensions_all_info(db)
        >>> for ext in all_extensions:
        ...     print(f"{ext.publisher}.{ext.name}: {ext.description}")

    Performance Considerations:
        - No pagination: Returns entire table
        - No lazy loading: All columns fetched immediately
        - For large datasets (>1000 records), consider:
            * Implementing pagination (LIMIT/OFFSET)
            * Cursor-based pagination for real-time data
            * Streaming responses for very large exports

    Use Cases:
        - Data export/backup
        - Administrative dashboards
        - Full-text search preprocessing
    """
    stmt = select(Extension).options(
        joinedload(Extension.capabilities),
        joinedload(Extension.scripts),
    )
    return list(db.scalars(stmt).unique().all())


def get_extensions_base_info(db: Session) -> list[Extension]:
    """
    Retrieve all extensions with only essential fields (optimized query).

    Uses SQLAlchemy's load_only() to fetch a subset of columns,
    reducing memory usage and network transfer for list views.

    Selected Fields:
        - id: For linking to detail views
        - name: Extension identifier
        - version: Extension version
        - publisher: Publisher name
        - description: Brief text for display
        - icon: Thumbnail image URL

    Args:
        db: SQLAlchemy database session

    Returns:
        List of Extension objects with only selected columns loaded

    Example:
        >>> extensions = get_extensions_base_info(db)
        >>> for ext in extensions:
        ...     # Only these fields are loaded from DB
        ...     print(f"{ext.name} by {ext.publisher}")
        ...     # Accessing other fields would trigger additional query

    Performance:
        - Reduces query payload by ~70% compared to full select
        - Ideal for gallery/grid views showing extension cards
        - Network I/O optimized for mobile/slow connections

    Warning:
        Accessing non-loaded columns will trigger lazy loading.
        If you need more fields, add them to load_only() or use
        get_extensions_all_info() instead.
    """
    stmt = select(Extension).options(
        load_only(
            Extension.id,
            Extension.name,
            Extension.version,
            Extension.publisher,
            Extension.description,
            Extension.icon,
        )
    )
    return list(db.scalars(stmt).all())


def delete_extension(
    db: Session, name: str, publisher: str | None = None, version: str | None = None
) -> bool:
    """
    Delete an extension by its name, optionally filtering by publisher and version.

    Args:
        db: SQLAlchemy database session
        name: Name of extension to delete
        publisher: Publisher name to filter on (recommended for precise matching)
        version: Specific version to delete (optional)

    Returns:
        True if the extension was found and deleted
        False if the extension was not found

    Raises:
        ValueError: If multiple records match the given filters (ambiguous)

    Note:
        The unique constraint is (publisher, name, version). For unambiguous deletion,
        provide all three parameters to avoid accidentally deleting the wrong extension.
    """
    stmt = select(Extension).where(Extension.name == name)
    if publisher:
        stmt = stmt.where(Extension.publisher == publisher)
    if version:
        stmt = stmt.where(Extension.version == version)

    results = db.scalars(stmt).all()
    if not results:
        return False
    if len(results) > 1:
        raise ValueError(
            "Multiple extensions match this name. "
            "Specify publisher and version to delete the correct one."
        )

    db.delete(results[0])
    db.commit()
    return True
