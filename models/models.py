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
    │ PK  │ id          │ Serial integer primary key              │
    │ IDX │ name        │ Extension identifier (indexed)          │
    │ IDX │ version     │ Extension version (indexed)             │
    │ IDX │ publisher   │ Publisher name (indexed)                │
    │     │ engines     │ VS Code version requirements (JSONB)    │
    │     │ ...         │ Additional metadata fields              │
    │ TS  │ created_at  │ Record creation timestamp               │
    │ TS  │ updated_at  │ Last update timestamp                   │
    ├─────────────────────────────────────────────────────────────┤
    │ UNIQUE CONSTRAINT: (publisher, name, version) - No duplicate extensions
    └─────────────────────────────────────────────────────────────┘

Migrations:
    This model is synchronized with the database via Alembic migrations.
    When changing this model:
    1. Modify the class attributes below
    2. Run: alembic revision --autogenerate -m "description"
    3. Run: alembic upgrade head
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


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


capability_support_enum = Enum(
    "supported",
    "not_supported",
    "limited",
    name="capability_support_state",
)


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

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """
    Auto-incrementing primary key.
    PostgreSQL SERIAL type - automatically generated on INSERT.
    Used for internal references and API endpoints like /extension/{id}
    """

    # =========================================================================
    # REQUIRED FIELDS (NOT NULL)
    # These fields must be present in every extension's package.json
    # =========================================================================

    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    """
    Extension identifier from package.json "name" field.

    This is the unique identifier within a publisher's namespace.
    Examples: "python", "prettier-vscode", "gitlens"

    Index: Created for fast name-based lookups
    Constraint: Part of unique (publisher, name, version) constraint
    """

    version: Mapped[str] = mapped_column(String, nullable=False, index=True)
    """
    Extension version from package.json "version" field.

    This is the unique identifier within a publisher's namespace.
    Examples: '2.5.6'
    Index: Created for fast version-based lookups
    Constraint: Part of unique (publisher, name, version) constraint
    """

    publisher: Mapped[str] = mapped_column(String, nullable=False, index=True)
    """
    Publisher account name from package.json "publisher" field.

    The organization or individual who publishes the extension.
    Examples: "ms-python", "esbenp", "eamodio"

    Index: Created for publisher-based filtering
    Constraint: Part of unique (publisher, name, version) constraint
    """

    engines: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
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

    license: Mapped[str | None] = mapped_column(String, nullable=True)
    """SPDX license identifier (MIT, Apache-2.0, etc.)"""

    displayName: Mapped[str | None] = mapped_column(String, nullable=True)
    """Human-readable name with spaces/special characters."""

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    """
    Extension description for marketplace display.

    Using TEXT instead of String because:
    - Descriptions can be very long (no length limit)
    - TEXT is more appropriate semantically
    - Same storage efficiency in PostgreSQL
    """

    categories: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    """
    Marketplace category tags.

    PostgreSQL ARRAY type allows storing lists natively.
    Example: ["Programming Languages", "Linters", "Debuggers"]

    Common categories:
    - Programming Languages, Snippets, Linters, Themes
    - Debuggers, Formatters, Keymaps, SCM Providers
    """

    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    """
    Search keywords for marketplace discovery.
    Example: ["python", "django", "flask", "pylint"]
    """

    galleryBanner: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    """
    Marketplace banner styling configuration.
    Example: {"color": "#1e415e", "theme": "dark"}
    """

    preview: Mapped[bool | None] = mapped_column(nullable=True)
    """Flag indicating if extension is in preview/beta state."""

    badges: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
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

    markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    """
    Markdown engine preference: "github" or "standard".

    Using TEXT type because in some cases this might store
    actual markdown content (README). TEXT has no length limit.
    """

    qna: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    """
    Q&A configuration - flexible type handling.

    Can be:
    - Boolean: false (disable Q&A)
    - String: "marketplace" or custom URL
    - Object: Complex Q&A configuration

    JSONB handles all these variants elegantly.
    """

    sponsor: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    """Sponsor/donation link configuration. Example: {"url": "..."}"""

    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    """Path or URL to extension icon (128x128 PNG recommended)."""

    pricing: Mapped[str | None] = mapped_column(String, nullable=True)
    """Pricing model: "Free", "Trial", or "Paid"."""

    main: Mapped[str | None] = mapped_column(String, nullable=True)
    """
    Desktop extension entry point (Node.js host).
    Relative path to main JavaScript file.
    Example: "./dist/extension.js"
    This file is very important for malicious analysis.
    """

    web: Mapped[str | None] = mapped_column(String, nullable=True)
    """
    Web extension entry point (browser host).
    Required for vscode.dev and github.dev compatibility.
    Example: "./dist/web-extension.js"
    """

    # =========================================================================
    # TIMESTAMP FIELDS (AUTO-MANAGED)
    # =========================================================================

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    """
    Record creation timestamp (auto-set by database).

    Uses server_default=func.now() for database-side timestamp.
    This ensures consistent timestamps regardless of app server time.
    Timezone-aware (WITH TIME ZONE in PostgreSQL).
    """

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    """
    Last update timestamp (auto-set on updates).

    Uses onupdate=func.now() to automatically update on any change.
    Initially NULL, populated on first update.
    Useful for tracking when extensions were re-scanned.
    """

    # =========================================================================
    # RELATIONSHIPS
    # =========================================================================

    capabilities: Mapped[ExtensionCapabilities | None] = relationship(
        back_populates="extension",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )

    scripts: Mapped[list[ExtensionScripts]] = relationship(
        back_populates="extension",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    # =========================================================================
    # TABLE CONSTRAINTS
    # =========================================================================

    __table_args__ = (
        UniqueConstraint(
            "publisher", "name", "version", name="uix_publisher_name_version"
        ),
    )
    """
    Table-level constraints.

    UniqueConstraint('publisher', 'name', 'version'):
        - Prevents duplicate extensions from same publisher with same version
        - publisher + name + version combination must be unique
        - Raises IntegrityError if violated (caught in CRUD layer)

    Example:
        ✅ ("ms-python", "python", "1.0.0") - First insertion OK
        ❌ ("ms-python", "python", "1.0.0") - Duplicate, blocked!
        ✅ ("ms-python", "python", "2.0.0") - Different version, OK
        ✅ ("other-pub", "python", "1.0.0") - Different publisher, OK
    """


class ExtensionCapabilities(Base):
    """
    Extension Capabilities (Normalized).

    Parses and stores contents of 'capabilities' from package.json into
    structured columns for easier SQL querying and security analysis.

    Source: package.json -> capabilities (top-level)

    Design:
        - Strict 1:1 relationship with Extension (shares Primary Key).
        - Flattens polymorphic JSON fields into structured columns.
        - Original package.json remains in filesystem if raw data needed.
    """

    __tablename__ = "extension_capabilities"

    # =========================================================================
    # PRIMARY KEY (Shared with Extension)
    # =========================================================================
    extension_id: Mapped[int] = mapped_column(
        ForeignKey("extensions.id", ondelete="CASCADE"),
        primary_key=True,  # Hem PK hem FK olmasi 1:1 iliskiyi garantiler
    )

    # =========================================================================
    # WORKSPACE TRUST (Untrusted Workspaces)
    # =========================================================================
    # Security Critical: Determines if extension runs in Restricted Mode.

    untrusted_supported: Mapped[str | None] = mapped_column(
        capability_support_enum, nullable=True
    )
    """
    Values: 'supported', 'not_supported', 'limited', or NULL.
    Note: Converted from boolean/string in package.json to standardized enum.
    """

    untrusted_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Explanation provided by the author specifically for trust issues."""

    untrusted_restricted_configurations: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    """
    List of configuration IDs (settings) that are disabled in Restricted Mode.
    Example: ['python.defaultInterpreterPath', 'git.path']
    Great for analysis: "Which extensions try to hide settings?"
    """

    # =========================================================================
    # VIRTUAL WORKSPACES
    # =========================================================================
    # Determines if extension runs in vscode.dev / GitHub Codespaces

    virtual_supported: Mapped[str | None] = mapped_column(
        capability_support_enum, nullable=True
    )
    """Values: 'supported', 'not_supported', 'limited', or NULL."""

    virtual_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # =========================================================================
    # RELATIONSHIPS
    # =========================================================================

    extension: Mapped[Extension] = relationship(back_populates="capabilities")


class ExtensionCommand(Base):
    """
    Extension Commands defined in package.json (contributes.commands).

    This table stores the commands that an extension exposes to the VS Code
    Command Palette or other extensions.

    Table Name: extension_commands

    Relationship:
        - Many-to-One with Extension table (One extension has Many commands)
        - On Delete: CASCADE (Deleting extension deletes all its commands)
    """

    __tablename__ = "extension_commands"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary Key"""

    extension_id: Mapped[int] = mapped_column(
        ForeignKey("extensions.id", ondelete="CASCADE"),
        index=True,
    )
    """Foreign Key linking to the parent Extension"""

    command_id: Mapped[str] = mapped_column(String)
    """
    The identifier of the command (e.g., 'extension.helloWorld').
    Required field in package.json.
    """

    title: Mapped[str] = mapped_column(String)
    """
    Title of the command, like 'Hello World'.
    Shown in the Command Palette.
    """

    category: Mapped[str | None] = mapped_column(String, nullable=True)
    """
    Category for grouping commands in the Palette (e.g., 'Git', 'File').
    Optional.
    """

    icon: Mapped[dict[str, Any] | str | None] = mapped_column(JSONB, nullable=True)
    """
    Icon for the command.
    Can be a string (path) or object ({dark: ..., light: ...}).
    Using JSONB to support both formats.
    """

    when: Mapped[dict[str, Any] | str | None] = mapped_column(JSONB, nullable=True)
    """
    When condition for the command.
    Can be a string (e.g., 'editorTextFocus') or object ({resource: ...}).
    Using JSONB to support both formats.
    """


class ExtensionScripts(Base):
    __tablename__ = "extension_scripts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    extension_id: Mapped[int] = mapped_column(
        ForeignKey("extensions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    script_name: Mapped[str] = mapped_column(String, nullable=False)

    script_command: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    extension: Mapped[Extension] = relationship(back_populates="scripts")
