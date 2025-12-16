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
    ⏳ Update (TODO: update_extension)
    ⏳ Delete (TODO: delete_extension)

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

from typing import Optional, List

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session, load_only

from models.models import Extension
from schemas.schemas import ExtensionSchema


def get_extension_by_id(db: Session, id: int) -> Optional[Extension]:
    """
    Retrieve a single extension by its database ID.
    
    Performs a primary key lookup which is the most efficient query type
    due to automatic indexing on the primary key column.
    
    Args:
        db: SQLAlchemy database session
        id: Primary key ID of the extension to retrieve
    
    Returns:
        Extension object if found, None otherwise
    
    Example:
        >>> extension = get_extension_by_id(db, 42)
        >>> if extension:
        ...     print(extension.name)
    
    Performance:
        O(1) - Direct index lookup on primary key
    """
    return db.query(Extension).filter(Extension.id == id).first()


def search_extension_by_name(db: Session, name: str) -> Optional[Extension]:
    """
    Search for an extension by its exact name.
    
    Uses the indexed 'name' column for efficient lookups.
    Note: This is an exact match search, not a partial/fuzzy search.
    
    Args:
        db: SQLAlchemy database session
        name: Exact extension name to search for (case-sensitive)
    
    Returns:
        Extension object if found, None otherwise
    
    Example:
        >>> extension = search_extension_by_name(db, "python")
        >>> if extension:
        ...     print(f"Publisher: {extension.publisher}")
    
    Note:
        For partial matching, consider implementing:
        - ILIKE for case-insensitive search
        - Full-text search with PostgreSQL tsvector
        - Trigram similarity for fuzzy matching
    """
    return db.query(Extension).filter(Extension.name == name).first()


def create_extension(db: Session, extension: ExtensionSchema) -> Extension:
    """
    Create a new extension record in the database.
    
    Converts a Pydantic schema to SQLAlchemy model and persists it.
    Handles duplicate entries via unique constraint violation detection.
    
    Args:
        db: SQLAlchemy database session
        extension: Pydantic schema containing extension data
    
    Returns:
        The created Extension ORM object with populated ID
    
    Raises:
        ValueError: If extension with same publisher+name already exists
        SQLAlchemyError: For other database errors (connection, etc.)
    
    Example:
        >>> schema = ExtensionSchema(name="test", publisher="dev", engines={"vscode": "^1.0.0"})
        >>> try:
        ...     new_ext = create_extension(db, schema)
        ...     print(f"Created with ID: {new_ext.id}")
        ... except ValueError as e:
        ...     print(f"Duplicate: {e}")
    
    Database Behavior:
        - Uses transaction with automatic rollback on error
        - Unique constraint (publisher, name) prevents duplicates
        - Auto-generates ID and created_at timestamp
    """
    # Convert Pydantic model to dict, then to SQLAlchemy model
    # model_dump() replaces deprecated dict() in Pydantic v2
    db_extension = Extension(**extension.model_dump())
    
    try:
        db.add(db_extension)      # Stage the object for insertion
        db.commit()               # Write to database
        db.refresh(db_extension)  # Reload to get auto-generated fields (id, created_at)
        return db_extension
        
    except IntegrityError:
        # Unique constraint violation - duplicate publisher+name
        db.rollback()
        # Re-raise as ValueError for router to return 409 Conflict
        raise ValueError("Extension already exists")
        
    except SQLAlchemyError as e:
        # Other database errors (connection issues, etc.)
        db.rollback()
        print("database commit error: ", e)
        raise e


def get_extensions_all_info(db: Session) -> List[Extension]:
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
    return db.query(Extension).all()


def get_extensions_base_info(db: Session) -> List[Extension]:
    """
    Retrieve all extensions with only essential fields (optimized query).
    
    Uses SQLAlchemy's load_only() to fetch a subset of columns,
    reducing memory usage and network transfer for list views.
    
    Selected Fields:
        - id: For linking to detail views
        - name: Extension identifier
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
    return db.query(Extension).options(
        load_only(
            Extension.id,
            Extension.name,
            Extension.publisher,
            Extension.description,
            Extension.icon
        )
    ).all()


# =============================================================================
# TODO: CRUD Operations to Implement ( update is not necessary for Extension Table beacuse extension data should not be changed )
# =============================================================================

# def update_extension(db: Session, extension_id: int, update_data: dict) -> Optional[Extension]:
#     """
#     Update an existing extension's fields.
#     
#     Args:
#         db: SQLAlchemy database session
#         extension_id: ID of extension to update
#         update_data: Dictionary of field names and new values
#     
#     Returns:
#         Updated Extension object or None if not found
#     """
#     extension = db.query(Extension).filter(Extension.id == extension_id).first()
#     if extension:
#         for key, value in update_data.items():
#             if hasattr(extension, key):
#                 setattr(extension, key, value)
#         db.commit()
#         db.refresh(extension)
#     return extension


def delete_extension(db: Session, name: str) -> bool:
    """
    Delete an extension by its name.
    
    Args:
        db: SQLAlchemy database session
        name: Name of extension to delete
    
    Returns:
        True if deleted, False if not found
    """
    extension = db.query(Extension).filter(Extension.name == name).first()
    if extension:
        db.delete(extension)
        db.commit()
        return True
    return False
