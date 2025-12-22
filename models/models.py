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
    Index,
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

    browser: Mapped[str | None] = mapped_column(String, nullable=True)
    """
    Web extension entry point (browser host).
    Required for extensions running in vscode.dev or github.dev.
    Example: "./dist/web-extension.js"
    """

    dependencies: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    """NPM dependencies from package.json."""

    devDependencies: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    """NPM development dependencies from package.json."""

    extensionPack: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    """List of extension IDs bundled in this extension pack."""

    extensionDependencies: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    """List of extension IDs that this extension depends on."""

    extensionKind: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    """Where the extension should run: ['ui'], ['workspace'], or both."""

    npm_fields: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    """
    Standard npm package.json fields not stored in dedicated columns.

    Includes common npm fields like repository, author, bugs, homepage,
    contributors, funding, etc. These are standard npm fields but not
    specific to VS Code extensions.
    """

    extra_fields: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    """
    Dynamic/custom fields from package.json not part of any standard schema.

    Stores truly unknown fields that publishers may add to their package.json.
    Examples include custom metadata, build configuration, or publisher-specific
    fields that aren't part of npm or VS Code extension specifications.
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

    activation_events: Mapped[list[ExtensionActivationEvents]] = relationship(
        back_populates="extension",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    contributes: Mapped[ExtensionContributes | None] = relationship(
        back_populates="extension",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )

    # =========================================================================
    # TABLE CONSTRAINTS AND INDEXES
    # =========================================================================

    __table_args__ = (
        UniqueConstraint(
            "publisher", "name", "version", name="uix_publisher_name_version"
        ),
        # Composite index for common search pattern (publisher + name + version)
        # This dramatically speeds up search_extension_by_name queries
        Index(
            "ix_extensions_publisher_name_version",
            "publisher",
            "name",
            "version",
        ),
        # Composite index for publisher + name lookups (when version is not specified)
        Index("ix_extensions_publisher_name", "publisher", "name"),
    )
    """
    Table-level constraints and indexes.

    UniqueConstraint('publisher', 'name', 'version'):
        - Prevents duplicate extensions from same publisher with same version
        - publisher + name + version combination must be unique
        - Raises IntegrityError if violated (caught in CRUD layer)

    Composite Indexes for Performance:
        1. ix_extensions_publisher_name_version:
           - Optimizes: search_extension_by_name(db, name, publisher, version)
           - Covers the most common search pattern with all three parameters
           - PostgreSQL can use this index for prefix matches too

        2. ix_extensions_publisher_name:
           - Optimizes: search_extension_by_name(db, name, publisher)
           - When version is not specified in the search
           - Faster than using only individual column indexes

    Performance Impact:
        - Without indexes: O(n) table scan for each search
        - With composite indexes: O(log n) B-tree lookup
        - 10-100x faster for large datasets (1000+ extensions)

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


class ExtensionContributesCommands(Base):
    """
    Extension Commands defined in package.json (contributes.commands).

    This table stores the commands that an extension exposes to the VS Code
    Command Palette or other extensions.

    SECURITY IMPORTANT: Commands are entry points for extension functionality.
    Analyzing command names and their conditions helps identify potentially
    dangerous operations.

    Source: package.json -> contributes.commands (array)

    Design:
        - Many-to-One with ExtensionContributes
        - Stores command ID, title, category, icon, and when clause
        - On Delete: CASCADE
    """

    __tablename__ = "extension_contributes_commands"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary Key"""

    contributes_id: Mapped[int] = mapped_column(
        ForeignKey("extension_contributes.extension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """Foreign Key linking to the parent ExtensionContributes"""

    command_id: Mapped[str] = mapped_column(String, nullable=False)
    """
    The identifier of the command (e.g., 'extension.helloWorld').
    Required field in package.json.
    """

    title: Mapped[str] = mapped_column(String, nullable=False)
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

    when: Mapped[str | None] = mapped_column(Text, nullable=True)
    """
    When condition for the command visibility.
    Example: 'editorTextFocus', 'resourceScheme == file'
    """

    contributes: Mapped[ExtensionContributes] = relationship(back_populates="commands")


class ExtensionScripts(Base):
    """
    Extension Scripts from package.json.

    This table stores npm scripts defined in the extension's package.json.
    Each script entry is stored as a separate row for easy querying and analysis.

    Source: package.json -> scripts (object)

    Design:
        - Many-to-One with Extension (one extension can have many scripts)
        - Script commands stored as JSONB for flexibility
        - On Delete: CASCADE (deleting extension deletes all its scripts)

    Example package.json:
        "scripts": {
            "compile": "tsc -p ./",
            "watch": "tsc -watch -p ./",
            "test": "npm run compile && node ./out/test/runTest.js"
        }

    Resulting rows:
        | script_name | script_command                        |
        |-------------|---------------------------------------|
        | compile     | {"command": "tsc -p ./"}              |
        | watch       | {"command": "tsc -watch -p ./"}       |
        | test        | {"command": "npm run compile && ..."}|

    Security Note:
        Script commands may contain potentially dangerous operations.
        This data is valuable for security analysis to detect:
        - Pre/post-install hooks that run arbitrary code
        - External network calls in scripts
        - File system modifications
    """

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


class ExtensionActivationEvents(Base):
    """
    Extension Activation Events from package.json.

    This table stores activation events that determine when a VS Code extension
    is activated. Each event is stored as a separate row for easy querying.

    Source: package.json -> activationEvents (array of strings)
    Reference: https://code.visualstudio.com/api/references/activation-events

    Design:
        - Many-to-One with Extension (one extension can have many events)
        - Event string is parsed into event_type and event_value
        - Format: "eventType:eventValue" or just "eventType" (e.g., "*")

    Example package.json:
        "activationEvents": [
            "onLanguage:python",
            "onCommand:extension.activate",
            "workspaceContains:**/.gitignore",
            "*"
        ]

    Resulting rows:
        | event_type        | event_value       |
        |-------------------|-------------------|
        | onLanguage        | python            |
        | onCommand         | extension.activate|
        | workspaceContains | **/.gitignore     |
        | *                 | NULL              |
    """

    __tablename__ = "extension_activation_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary Key"""

    extension_id: Mapped[int] = mapped_column(
        ForeignKey("extensions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """Foreign Key linking to the parent Extension"""

    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    """
    The activation event type.
    Examples: onLanguage, onCommand, workspaceContains, onFileSystem,
              onView, onUri, onWebviewPanel, onCustomEditor, onStartupFinished,
              onAuthenticationRequest, onTaskType, onNotebook, onTerminal, *
    """

    event_value: Mapped[str | None] = mapped_column(String, nullable=True)
    """
    The activation event value/parameter.
    Examples: python (for onLanguage:python), extension.activate (for onCommand)
    NULL for events without parameters like "*" or "onStartupFinished"
    """

    extension: Mapped[Extension] = relationship(back_populates="activation_events")


class ExtensionContributes(Base):
    """
    VS Code Extension Contribution Points container.

    This table stores the `contributes` section from package.json.
    It has a 1:1 relationship with Extension and acts as a parent
    for all contribution-related child tables.

    Source: package.json -> contributes (object)

    Design:
        - Strict 1:1 relationship with Extension (shares Primary Key)
        - JSONB columns for complex/deep structures that don't need querying
        - Child tables for frequently queried contribution types
        - On Delete: CASCADE (deleting extension deletes all contributes data)

    Reference: https://code.visualstudio.com/api/references/contribution-points
    """

    __tablename__ = "extension_contributes"

    # Shared PK with Extension (1:1)
    extension_id: Mapped[int] = mapped_column(
        ForeignKey("extensions.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # =========================================================================
    # JSONB COLUMNS (Complex structures, sorgulama gerekmeyenler)
    # =========================================================================

    configuration: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """Extension configuration/settings schema. Very deep nested structure."""

    debuggers: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Debugger adapter contributions. Complex with configurationAttributes."""

    walkthroughs: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Interactive walkthrough contributions with steps and media."""

    grammars: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """TextMate grammar contributions for syntax highlighting."""

    colors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Custom color contributions with dark/light/highContrast variants."""

    icons: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """Custom icon definitions."""

    snippets: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Code snippet contributions."""

    views: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """View contributions (sidebar panels, explorer views)."""

    viewsContainers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """View container contributions (activity bar items)."""

    languages: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Language contributions (language identifiers, extensions, aliases)."""

    themes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Color theme contributions."""

    iconThemes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """File icon theme contributions."""

    productIconThemes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Product icon theme contributions."""

    jsonValidation: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """JSON schema validation contributions."""

    problemMatchers: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Problem matcher contributions for task output parsing."""

    problemPatterns: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Problem pattern contributions."""

    taskDefinitions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Task definition contributions."""

    customEditors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Custom editor contributions. SECURITY: Can handle arbitrary file types."""

    submenus: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Submenu contributions."""

    viewsWelcome: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """View welcome content contributions."""

    breakpoints: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """Breakpoint contributions for debugging."""

    configurationDefaults: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """Default configuration value overrides."""

    typescriptServerPlugins: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    """
    TypeScript server plugin contributions.
    SECURITY: Can inject code into TS server.
    """

    # =========================================================================
    # RELATIONSHIPS
    # =========================================================================

    extension: Mapped[Extension] = relationship(back_populates="contributes")

    keybindings: Mapped[list[ExtensionContributesKeybindings]] = relationship(
        back_populates="contributes",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    menus: Mapped[list[ExtensionContributesMenus]] = relationship(
        back_populates="contributes",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    authentication: Mapped[list[ExtensionContributesAuthentication]] = relationship(
        back_populates="contributes",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    terminal: Mapped[list[ExtensionContributesTerminal]] = relationship(
        back_populates="contributes",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    commands: Mapped[list[ExtensionContributesCommands]] = relationship(
        back_populates="contributes",
        cascade="all, delete-orphan",
        single_parent=True,
    )


class ExtensionContributesKeybindings(Base):
    """
    Extension Keybinding contributions from package.json.

    This table stores keyboard shortcuts that an extension defines.
    Important for security analysis: which keys does the extension override?

    Source: package.json -> contributes.keybindings (array)

    Design:
        - Many-to-One with ExtensionContributes
        - Separate columns for different platform overrides
        - On Delete: CASCADE
    """

    __tablename__ = "extension_contributes_keybindings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    contributes_id: Mapped[int] = mapped_column(
        ForeignKey("extension_contributes.extension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    key: Mapped[str] = mapped_column(String, nullable=False)
    """Default key combination (e.g., 'ctrl+shift+p', 'cmd+k cmd+s')."""

    command: Mapped[str] = mapped_column(String, nullable=False)
    """Command to invoke when key is pressed."""

    when: Mapped[str | None] = mapped_column(Text, nullable=True)
    """When clause condition (e.g., 'editorTextFocus', 'inDebugMode')."""

    mac: Mapped[str | None] = mapped_column(String, nullable=True)
    """macOS key override (e.g., 'cmd+shift+p')."""

    linux: Mapped[str | None] = mapped_column(String, nullable=True)
    """Linux key override."""

    win: Mapped[str | None] = mapped_column(String, nullable=True)
    """Windows key override."""

    args: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """Additional arguments passed to the command."""

    contributes: Mapped[ExtensionContributes] = relationship(
        back_populates="keybindings"
    )


class ExtensionContributesMenus(Base):
    """
    Extension Menu contributions from package.json.

    This table stores menu items that an extension adds to VS Code.
    Important for security: where does the extension inject UI elements?

    Source: package.json -> contributes.menus (object with arrays)

    Design:
        - Many-to-One with ExtensionContributes
        - menu_location stores the menu key (editor/context, explorer/context, etc.)
        - On Delete: CASCADE
    """

    __tablename__ = "extension_contributes_menus"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    contributes_id: Mapped[int] = mapped_column(
        ForeignKey("extension_contributes.extension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    menu_location: Mapped[str] = mapped_column(String, nullable=False, index=True)
    """
    Menu location identifier.
    Examples: editor/context, explorer/context, commandPalette, view/title, etc.
    """

    command: Mapped[str | None] = mapped_column(String, nullable=True)
    """Command to invoke when menu item is selected."""

    submenu: Mapped[str | None] = mapped_column(String, nullable=True)
    """Submenu ID to render at this location."""

    when: Mapped[str | None] = mapped_column(Text, nullable=True)
    """When clause condition for visibility."""

    group: Mapped[str | None] = mapped_column(String, nullable=True)
    """Menu group for sorting (e.g., 'navigation', '1_modification')."""

    alt: Mapped[str | None] = mapped_column(String, nullable=True)
    """Alternative command when Alt/Shift is held."""

    contributes: Mapped[ExtensionContributes] = relationship(back_populates="menus")


class ExtensionContributesAuthentication(Base):
    """
    Extension Authentication Provider contributions from package.json.

    SECURITY CRITICAL: Extensions that provide authentication can access credentials.

    Source: package.json -> contributes.authentication (array)

    Design:
        - Many-to-One with ExtensionContributes
        - Simple structure: just id and label
        - On Delete: CASCADE
    """

    __tablename__ = "extension_contributes_authentication"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    contributes_id: Mapped[int] = mapped_column(
        ForeignKey("extension_contributes.extension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    auth_id: Mapped[str] = mapped_column(String, nullable=False)
    """Authentication provider ID (e.g., 'github', 'azuredevops')."""

    label: Mapped[str] = mapped_column(String, nullable=False)
    """Display label for the authentication provider."""

    contributes: Mapped[ExtensionContributes] = relationship(
        back_populates="authentication"
    )


class ExtensionContributesTerminal(Base):
    """
    Extension Terminal Profile contributions from package.json.

    SECURITY CRITICAL: Extensions can define terminal profiles that may
    execute arbitrary shell commands.

    Source: package.json -> contributes.terminal.profiles (array)

    Design:
        - Many-to-One with ExtensionContributes
        - Stores terminal profile definitions
        - On Delete: CASCADE
    """

    __tablename__ = "extension_contributes_terminal"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    contributes_id: Mapped[int] = mapped_column(
        ForeignKey("extension_contributes.extension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    profile_id: Mapped[str] = mapped_column(String, nullable=False)
    """Terminal profile ID (e.g., 'my-ext.terminal-profile')."""

    title: Mapped[str] = mapped_column(String, nullable=False)
    """Display title for the terminal profile."""

    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    """Icon for the terminal profile."""

    contributes: Mapped[ExtensionContributes] = relationship(back_populates="terminal")
