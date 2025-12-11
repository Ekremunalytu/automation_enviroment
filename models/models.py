"""
models/models.py
================

SQLAlchemy ORM Models for Database Tables
------------------------------------------

This module defines the database schema using SQLAlchemy's declarative
mapping pattern. Each class represents a database table, and each class
attribute represents a column.

Architecture Position:
    CRUD Operations → **ORM Models** → SQLAlchemy Core → PostgreSQL

ORM (Object-Relational Mapping):
    ORM allows us to work with Python objects instead of raw SQL.
    
    Instead of:
        cursor.execute("INSERT INTO extensions (name, publisher) VALUES (?, ?)")
    
    We write:
        extension = Extension(name="python", publisher="ms-python")
        db.add(extension)
        db.commit()

Database Design Principles Applied:
    1. Normalization: Each extension is a single record
    2. Indexing: Searchable fields (name, publisher) are indexed
    3. Constraints: Unique constraint prevents duplicate extensions
    4. Type Safety: PostgreSQL-specific types (JSONB, ARRAY)
    5. Timestamps: Automatic created_at and updated_at tracking

Table Overview:
    ┌─────────────────────────────────────────────────────────────┐
    │                        extensions                           │
    ├─────────────────────────────────────────────────────────────┤
    │ PK  │ id          │ Serial integer primary key             │
    │ IDX │ name        │ Extension identifier (indexed)         │
    │ IDX │ publisher   │ Publisher name (indexed)               │
    │     │ engines     │ VS Code version requirements (JSONB)   │
    │     │ ...         │ Additional metadata fields             │
    │ TS  │ created_at  │ Record creation timestamp              │
    │ TS  │ updated_at  │ Last update timestamp                  │
    ├─────────────────────────────────────────────────────────────┤
    │ UNIQUE CONSTRAINT: (publisher, name) - No duplicate extensions
    └─────────────────────────────────────────────────────────────┘

Migrations:
    This model is synchronized with the database via Alembic migrations.
    When changing this model:
    1. Modify the class attributes below
    2. Run: alembic revision --autogenerate -m "description"
    3. Run: alembic upgrade head
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base class.
    
    All ORM models inherit from this class. It provides:
    - Metadata registry for table definitions
    - Common base for all models
    - Alembic autogenerate support
    
    Usage:
        class MyModel(Base):
            __tablename__ = "my_table"
            id = Column(Integer, primary_key=True)
    """
    pass


class Extension(Base):
    """
    VS Code Extension metadata database model.
    
    This model stores metadata parsed from VS Code extension package.json
    files. It's designed to support extension security analysis by storing
    all relevant manifest fields for later inspection.
    
    The schema follows the VS Code Extension Manifest specification:
    https://code.visualstudio.com/api/references/extension-manifest
    
    Table Name: extensions
    
    Key Design Decisions:
        - JSONB for flexible nested structures (engines, badges, etc.)
        - ARRAY for simple lists (categories, keywords)
        - TEXT for potentially large strings (description, markdown)
        - Indexed name/publisher for fast lookups
        - Unique constraint prevents duplicate extensions
    
    Example Record:
        {
            "id": 1,
            "name": "python",
            "publisher": "ms-python",
            "engines": {"vscode": "^1.95.0"},
            "displayName": "Python",
            "description": "Python language support...",
            "created_at": "2025-12-11T10:00:00Z"
        }
    """
    
    # Table name in PostgreSQL
    __tablename__ = "extensions"

    # =========================================================================
    # PRIMARY KEY
    # =========================================================================
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    """
    Auto-incrementing primary key.
    PostgreSQL SERIAL type - automatically generated on INSERT.
    Used for internal references and API endpoints like /extension/{id}
    """

    # =========================================================================
    # REQUIRED FIELDS (NOT NULL)
    # These fields must be present in every extension's package.json
    # =========================================================================
    
    name = Column(String, nullable=False, index=True)
    """
    Extension identifier from package.json "name" field.
    
    This is the unique identifier within a publisher's namespace.
    Examples: "python", "prettier-vscode", "gitlens"
    
    Index: Created for fast name-based lookups
    Constraint: Part of unique (publisher, name) constraint
    """
    
    publisher = Column(String, nullable=False, index=True)
    """
    Publisher account name from package.json "publisher" field.
    
    The organization or individual who publishes the extension.
    Examples: "ms-python", "esbenp", "eamodio"
    
    Index: Created for publisher-based filtering
    Constraint: Part of unique (publisher, name) constraint
    """
    
    engines = Column(JSONB, nullable=False)
    """
    VS Code version compatibility requirements.
    
    JSONB type allows efficient storage and querying of nested data.
    PostgreSQL JSONB provides:
    - Binary storage (faster than JSON text)
    - Indexable (can create GIN indexes)
    - Query operators (@>, ?, etc.)
    
    Example value: {"vscode": "^1.95.0"}
    The caret (^) indicates compatible versions (semver).
    """

    # =========================================================================
    # OPTIONAL METADATA FIELDS (NULLABLE)
    # These fields may or may not be present in package.json
    # =========================================================================
    
    license = Column(String, nullable=True)
    """SPDX license identifier (MIT, Apache-2.0, etc.)"""
    
    displayName = Column(String, nullable=True)
    """Human-readable name with spaces/special characters."""
    
    description = Column(Text, nullable=True)
    """
    Extension description for marketplace display.
    
    Using TEXT instead of String because:
    - Descriptions can be very long (no length limit)
    - TEXT is more appropriate semantically
    - Same storage efficiency in PostgreSQL
    """
    
    categories = Column(ARRAY(String), nullable=True)
    """
    Marketplace category tags.
    
    PostgreSQL ARRAY type allows storing lists natively.
    Example: ["Programming Languages", "Linters", "Debuggers"]
    
    Common categories:
    - Programming Languages, Snippets, Linters, Themes
    - Debuggers, Formatters, Keymaps, SCM Providers
    """
    
    keywords = Column(ARRAY(String), nullable=True)
    """
    Search keywords for marketplace discovery.
    Example: ["python", "django", "flask", "pylint"]
    """
    
    galleryBanner = Column(JSONB, nullable=True)
    """
    Marketplace banner styling configuration.
    Example: {"color": "#1e415e", "theme": "dark"}
    """
    
    preview = Column(Boolean, nullable=True)
    """Flag indicating if extension is in preview/beta state."""
    
    badges = Column(JSONB, nullable=True)
    """
    Status badges for marketplace display.
    
    Changed from ARRAY to JSONB because badges are complex objects:
    [
        {
            "url": "https://badge-image-url.svg",
            "href": "https://link-when-clicked",
            "description": "Alt text for badge"
        }
    ]
    """
    
    markdown = Column(Text, nullable=True)
    """
    Markdown engine preference: "github" or "standard".
    
    Using TEXT type because in some cases this might store
    actual markdown content (README). TEXT has no length limit.
    """
    
    qna = Column(JSONB, nullable=True)
    """
    Q&A configuration - flexible type handling.
    
    Can be:
    - Boolean: false (disable Q&A)
    - String: "marketplace" or custom URL
    - Object: Complex Q&A configuration
    
    JSONB handles all these variants elegantly.
    """
    
    sponsor = Column(JSONB, nullable=True)
    """Sponsor/donation link configuration. Example: {"url": "..."}"""
    
    icon = Column(String, nullable=True)
    """Path or URL to extension icon (128x128 PNG recommended)."""
    
    pricing = Column(String, nullable=True)
    """Pricing model: "Free", "Trial", or "Paid"."""
    
    main = Column(String, nullable=True)
    """
    Desktop extension entry point (Node.js host).
    Relative path to main JavaScript file.
    Example: "./dist/extension.js"
    """
    
    web = Column(String, nullable=True)
    """
    Web extension entry point (browser host).
    Required for vscode.dev and github.dev compatibility.
    Example: "./dist/web-extension.js"
    """

    # =========================================================================
    # TIMESTAMP FIELDS (AUTO-MANAGED)
    # =========================================================================
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    """
    Record creation timestamp (auto-set by database).
    
    Uses server_default=func.now() for database-side timestamp.
    This ensures consistent timestamps regardless of app server time.
    Timezone-aware (WITH TIME ZONE in PostgreSQL).
    """
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    """
    Last update timestamp (auto-set on updates).
    
    Uses onupdate=func.now() to automatically update on any change.
    Initially NULL, populated on first update.
    Useful for tracking when extensions were re-scanned.
    """

    # =========================================================================
    # TABLE CONSTRAINTS
    # =========================================================================
    
    __table_args__ = (
        UniqueConstraint('publisher', 'name', name='uix_publisher_name'),
    )
    """
    Table-level constraints.
    
    UniqueConstraint('publisher', 'name'):
        - Prevents duplicate extensions from same publisher
        - publisher + name combination must be unique
        - Raises IntegrityError if violated (caught in CRUD layer)
    
    Example:
        ✅ ("ms-python", "python") - First insertion OK
        ❌ ("ms-python", "python") - Duplicate, blocked!
        ✅ ("other-pub", "python") - Different publisher, OK
    """
