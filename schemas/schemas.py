"""
schemas/schemas.py
==================

Pydantic Schema Definitions for ExTrace API
--------------------------------------------

This module contains all Pydantic models (schemas) used for data validation,
serialization, and API documentation in the ExTrace VS Code Extension Scanner.

Pydantic schemas serve three primary purposes:
1. **Request Validation**: Validates incoming API request payloads
2. **Response Serialization**: Converts SQLAlchemy models to JSON responses
3. **API Documentation**: Auto-generates OpenAPI/Swagger documentation

Schema Design Philosophy:
- ExtensionSchema mirrors the database model for full data transfer
- Request schemas (ScanRequest, SearchRequest) are minimal for input validation
- Response schemas provide filtered views of extension data

Note on ConfigDict:
- `from_attributes=True`: Enables ORM mode for SQLAlchemy model conversion
- `extra="ignore"`: Silently ignores extra fields not defined in schema
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExtensionSchema(BaseModel):
    """
    Complete VS Code Extension data schema.

    This is the primary schema representing a VS Code extension's package.json
    metadata. It mirrors the Extension SQLAlchemy model and is used for:
    - Creating new extensions (POST /createExtension)
    - Returning extension details (GET /searchExtension)

    The schema follows the VS Code extension manifest specification:
    https://code.visualstudio.com/api/references/extension-manifest

    Attributes:
        name: Unique extension identifier (e.g., 'python', 'prettier-vscode')
        publisher: Publisher/vendor name (e.g., 'ms-python', 'esbenp')
        engines: VS Code version compatibility (e.g., {'vscode': '^1.95.0'})
        license: SPDX license identifier (e.g., 'MIT', 'Apache-2.0')
        displayName: Human-readable extension name shown in marketplace
        description: Short description of extension functionality
        categories: Marketplace categories (e.g., ['Programming Languages', 'Linters'])
        keywords: Search keywords for marketplace discovery
        galleryBanner: Marketplace banner styling (color, theme)
        preview: Whether this is a preview/beta extension
        badges: Status badges displayed on marketplace page
        markdown: Markdown engine preference ('github' or 'standard')
        qna: Q&A settings (marketplace URL, false to disable, or custom config)
        sponsor: Sponsor/donation information
        icon: Path or URL to extension icon
        pricing: Pricing tier ('Free', 'Trial', 'Paid')
        main: Entry point for Node.js extension host
        web: Entry point for web extension host

    Example:
        >>> extension = ExtensionSchema(
        ...     name="python",
        ...     publisher="ms-python",
        ...     engines={"vscode": "^1.95.0"},
        ...     description="Python language support"
        ... )
    """

    # Pydantic v2 configuration
    # - from_attributes: Allows conversion from SQLAlchemy ORM objects
    # - extra="ignore": Prevents validation errors from unknown fields in package.json
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    # =========================================================================
    # REQUIRED FIELDS
    # These fields MUST be present in every extension's package.json
    # =========================================================================

    name: str
    """Extension identifier. Must be unique per publisher. Used in extension ID: publisher.name"""

    publisher: str
    """Publisher account name on VS Code Marketplace."""

    version: str
    """ Extension version"""

    engines: dict[str, Any]
    """
    VS Code version requirements. Format: {'vscode': 'version-range'}
    Example: {'vscode': '^1.95.0'} means VS Code 1.95.0 or higher
    The caret (^) allows minor and patch updates.
    """

    # =========================================================================
    # OPTIONAL METADATA FIELDS
    # These fields enhance extension discovery and display
    # =========================================================================

    license: str | None = None
    """SPDX license identifier (MIT, Apache-2.0, GPL-3.0, etc.)"""

    displayName: str | None = None
    """Human-friendly name shown in Marketplace (can include spaces/special chars)"""

    description: str | None = None
    """Brief description shown in search results. Keep under 200 chars for best display."""

    categories: list[str] | None = None
    """
    Marketplace category tags. Valid values include:
    - Programming Languages, Snippets, Linters, Themes
    - Debuggers, Formatters, Keymaps, SCM Providers
    - Other, Extension Packs, Language Packs
    """

    keywords: list[str] | None = None
    """Search keywords. Max 5 keywords, each up to 50 characters."""

    galleryBanner: dict[str, Any] | None = None
    """
    Marketplace page banner styling.
    Example: {'color': '#1e415e', 'theme': 'dark'}
    Theme can be 'dark' or 'light' - affects text color on banner.
    """

    preview: bool | None = None
    """If True, extension is marked as Preview in Marketplace."""

    badges: list[dict[str, Any]] | None = None
    """
    Status badges displayed on Marketplace page.
    Each badge: {'url': 'badge-image-url', 'href': 'link-url', 'description': 'alt-text'}
    Example: Build status, test coverage, download count badges.
    """

    markdown: str | None = None
    """Markdown rendering engine: 'github' (GitHub Flavored) or 'standard'."""

    # =========================================================================
    # OPTIONAL ADVANCED FIELDS
    # These fields control extension behavior and monetization
    # =========================================================================

    qna: str | bool | dict[str, Any] | None = None
    """
    Q&A configuration. Can be:
    - 'marketplace': Use VS Code Marketplace Q&A (default)
    - False: Disable Q&A section
    - Custom URL string: Link to external Q&A
    """

    sponsor: dict[str, Any] | None = None
    """Sponsor/donation link. Example: {'url': 'https://github.com/sponsors/...'}"""

    icon: str | None = None
    """
    Path to extension icon (128x128 PNG recommended).
    Relative path in extension or absolute URL.
    """

    pricing: str | None = None
    """Pricing model: 'Free', 'Trial', or 'Paid'."""

    main: str | None = None
    """
    Entry point for desktop extension host (Node.js).
    Relative path to the main JavaScript file.
    Example: './dist/extension.js'
    """

    web: str | None = None
    """
    Entry point for web extension host (browser).
    Required for extensions running in vscode.dev or github.dev.
    Example: './dist/web-extension.js'
    """


class ScanRequest(BaseModel):
    """
    Request schema for creating/scanning a new extension.

    Used by POST /createExtension endpoint. The extension name is used to
    search for the extension's package.json in the extensions directory.

    Flow:
    1. Client sends extension name
    2. Server searches extensions/ directory for matching package.json
    3. If found, parses and stores extension metadata in database

    Attributes:
        name: Extension name to search for (must match package.json "name" field)

    Example:
        POST /createExtension
        {"name": "python"}
    """

    name: str = Field(
        ...,  # Ellipsis means required field
        min_length=1,
        description="Extension name to create/scan. Must match package.json name field.",
    )


class SearchRequest(BaseModel):
    """
    Request schema for searching extensions in the database.

    Used by GET /searchExtension endpoint as query parameters.
    FastAPI's Depends() converts query params to this model.

    Attributes:
        name: Extension name to search for in database
        version: Optional specific version to filter on

    Example:
        GET /searchExtension?name=python
    """

    name: str = Field(
        ..., min_length=1, description="Extension name to search for in the database."
    )

    version: str | None = Field(
        default=None,
        description="Specific extension version to target; if omitted, matches by name regardless of version.",
    )


class SearchAllExtensionsInfo(BaseModel):
    """
    Lightweight extension listing schema.

    Returns only essential fields for extension list/grid views.
    Used by GET /getExtensionsBaseInfo for performance optimization.

    This schema is designed for:
    - Extension gallery/grid displays
    - Search result listings
    - Quick overview without full metadata

    Performance Note:
        By excluding large fields (badges, markdown, engines),
        response size is significantly reduced for list views.

    Attributes:
        id: Database primary key
        name: Extension identifier
        publisher: Publisher name
        description: Brief description for display
        icon: Icon URL for thumbnail display
    """

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    """Database auto-generated primary key."""

    name: str
    """Extension identifier (from package.json)."""

    publisher: str
    """Publisher account name."""

    description: str | None = None
    """Short description for list display."""

    version: str | None = None
    """Extension version."""

    icon: str | None = None
    """Icon URL for thumbnail rendering."""


class SearchAllExtensionsAllInfo(ExtensionSchema):
    """
    Complete extension listing schema with database ID.

    Extends ExtensionSchema to include the database ID.
    Used by GET /getExtensionsAllInfo for full data export.

    Inherits all fields from ExtensionSchema plus:
        id: Database primary key for reference

    Use Cases:
        - Full data export/backup
        - Detailed extension comparison
        - Administrative views

    Note:
        This returns significantly more data than SearchAllExtensionsInfo.
        Use sparingly for large datasets to avoid performance issues.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    """Database auto-generated primary key."""
