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

Future Enhancements:
    - Risk score calculation
    - Malware pattern detection
    - Caching layer integration
    - Batch processing operations
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from schemas.schemas import ExtensionSchema

# Aliased imports to avoid naming conflicts between service and CRUD functions
# This is a common pattern when service methods wrap CRUD operations
from crud.crud import create_extension as create_db_extension
from crud.crud import search_extension_by_name as search_db_extension
from crud.crud import delete_extension as delete_db_extension
from crud.crud import get_extensions_all_info
from crud.crud import get_extensions_base_info

# File system operations for scanning extensions directory
from .json_parser import search_extension as find_json_in_dir


def get_all_extensions_basic(db: Session):
    """
    Retrieve all extensions with basic information only.
    
    This is a pass-through to CRUD for simple listing operations.
    Returns optimized payload suitable for gallery/grid displays.
    
    Args:
        db: SQLAlchemy database session from dependency injection
    
    Returns:
        List of Extension objects with only id, name, publisher,
        description, and icon fields loaded
    
    Example:
        >>> extensions = get_all_extensions_basic(db)
        >>> # Returns lightweight objects for listing
    
    Use Cases:
        - Extension gallery/marketplace view
        - Search results listing
        - Extension selector dropdowns
    """
    all_extensions_basic_information = get_extensions_base_info(db)
    return all_extensions_basic_information


def get_all_extensions_all(db: Session):
    """
    Retrieve all extensions with complete information.
    
    Returns full extension data including all metadata fields.
    Use sparingly due to larger payload size.
    
    Args:
        db: SQLAlchemy database session from dependency injection
    
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
    all_extensions_all_information = get_extensions_all_info(db)
    return all_extensions_all_information


def search_extension_by_name(db: Session, extension_name: str):
    """
    Search for an extension by name in the database.
    
    Performs an exact-match database lookup. The result is returned
    directly as FastAPI's response_model handles Pydantic conversion.
    
    Args:
        db: SQLAlchemy database session from dependency injection
        extension_name: Exact name of extension to find
    
    Returns:
        Extension ORM object if found, None otherwise
    
    Note:
        FastAPI's response_model automatically converts the SQLAlchemy
        Extension object to ExtensionSchema for the JSON response.
        No manual conversion needed in the service layer.
    
    Example:
        >>> result = search_extension_by_name(db, "python")
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
    extension = search_db_extension(db, extension_name)
    
    # Return as-is; FastAPI's response_model handles serialization
    # from SQLAlchemy ORM object to Pydantic schema automatically
    return extension


def delete_extension_by_name(db: Session, extension_name: str):
    """
    Delete an extension by name from the database.
    
    Args:
        db: SQLAlchemy database session
        extension_name: Name of extension to delete
        
    Returns:
        True if deleted, False if not found
    """
    return delete_db_extension(db, extension_name)


def create_extension_by_name(db: Session, extension_name: str):
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
        package_schema = ExtensionSchema(**package_json)

        # Step 3: Persist to database via CRUD layer
        # create_db_extension handles:
        # - ORM model creation
        # - Transaction commit
        # - Duplicate detection (raises ValueError)
        return create_db_extension(db, package_schema)

    # Extension not found in filesystem
    return None
