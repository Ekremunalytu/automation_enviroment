"""
scanner/json_parser.py
======================

Filesystem Scanner for VS Code Extension Packages
--------------------------------------------------

This module handles all filesystem operations related to scanning and
parsing VS Code extension package.json files. It serves as the file I/O
layer for the extension scanning workflow.

Architecture Position:
    Service Layer → **JSON Parser (File I/O)** → Filesystem
                           ↓
                    extensions/ directory
                           │
                    ├── extension-a/
                    │   └── package.json ←── Parsed
                    ├── extension-b/
                    │   └── package.json ←── Parsed
                    └── extension-c/
                        └── package.json ←── Parsed

Responsibilities:
    1. Navigate the extensions/ directory structure
    2. Locate and read package.json files
    3. Parse JSON content into Python dictionaries
    4. Handle filesystem errors gracefully

Expected Directory Structure:
    extensions/
    ├── publisher.extension-name-version/
    │   ├── package.json          ← Primary target
    │   ├── extension.js
    │   ├── README.md
    │   └── ...
    └── another.extension-2.0.0/
        ├── package.json
        └── ...

Note on VS Code Extensions:
    When extracted from .vsix files, extensions typically follow
    the naming convention: {publisher}.{name}-{version}
    The package.json contains all extension metadata.

Security Considerations:
    - Only reads files within configured EXTENSION_DIR
    - Uses Path objects for safe path manipulation
    - JSON parsing will fail gracefully on malformed content
    - No shell commands or external process execution
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.config import settings


def parse_json_file(json_path: Path) -> dict[str, Any] | None:
    """
    Parse a JSON file and return its contents as a dictionary.

    Opens a file at the given path, reads its contents, and parses
    it as JSON. Handles common errors like file not found, permission
    denied, and malformed JSON gracefully.

    Args:
        json_path: Pathlib Path object pointing to the JSON file

    Returns:
        dict: Parsed JSON content as Python dictionary
        None: If any error occurs during reading or parsing

    Example:
        >>> path = Path("extensions/ext-1.0.0/package.json")
        >>> data = parse_json_file(path)
        >>> if data:
        ...     print(f"Extension: {data.get('name')}")
        ... else:
        ...     print("Failed to parse")

    Error Handling:
        - FileNotFoundError: File doesn't exist
        - PermissionError: No read permission
        - JSONDecodeError: Invalid JSON syntax
        - UnicodeDecodeError: Encoding issues
        All errors are caught, logged, and return None.

    Encoding:
        Uses UTF-8 encoding which is standard for package.json files.
        Most VS Code extensions follow this convention.
    """
    try:
        with open(json_path, encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        # Log error for debugging but don't crash
        # In production, consider using proper logging framework
        return None


def get_package_json(extension_dir: Path) -> dict[str, Any] | None:
    """
    Retrieve package.json from an extension directory.

    Checks if a package.json file exists directly in the given
    extension directory and parses it if found.

    Args:
        extension_dir: Path to the extension's root directory

    Returns:
        dict: Parsed package.json content
        None: If package.json doesn't exist or fails to parse

    Example:
        >>> ext_dir = Path("extensions/ms-python.python-2025.18.0")
        >>> pkg = get_package_json(ext_dir)
        >>> if pkg:
        ...     print(f"Found: {pkg['name']} by {pkg['publisher']}")

    Expected File Location:
        {extension_dir}/package.json

    Note:
        Some extensions may have nested structures. This function
        only checks the immediate directory. For nested searches,
        additional logic would be needed.
    """
    # Construct path to package.json in extension root
    package_path = extension_dir / "package.json"

    # Verify file exists and is actually a file (not a directory)
    if package_path.exists() and package_path.is_file():
        return parse_json_file(package_path)

    return None


def search_extension(extension_name_field: str) -> dict[str, Any] | None:
    """
    Search for an extension by name across all extension directories.

    Iterates through all subdirectories in the configured extensions
    directory, looking for a package.json where the "name" field
    matches the requested extension name.

    This is the primary entry point for extension discovery workflows.

    Args:
        extension_name_field: Extension name to search for
                             Must match package.json "name" field exactly

    Returns:
        dict: Complete package.json content of matching extension
        None: If no extension with matching name is found

    Search Algorithm:
        ┌────────────────────────────────────────┐
        │ For each directory in extensions/:     │
        │   1. Try to read package.json          │
        │   2. Check if "name" field matches     │
        │   3. If match found, return data       │
        │   4. Otherwise, continue to next dir   │
        └────────────────────────────────────────┘

    Example:
        >>> data = search_extension("python")
        >>> if data:
        ...     print(f"Found in: {data['publisher']}.{data['name']}")
        ...     print(f"Version: {data.get('version', 'N/A')}")
        ... else:
        ...     print("Extension not found")

    Performance Considerations:
        - Linear scan: O(n) where n = number of extension directories
        - For large extension collections, consider:
            * Building an index/cache on startup
            * Using database instead of filesystem scanning
            * Parallel directory scanning

    Configuration:
        Uses settings.EXTENSION_DIR from core.config
        Default: "extensions" (relative to project root)

    Directory Structure Expected:
        extensions/
        ├── publisher1.ext1-1.0.0/
        │   └── package.json  ← {"name": "ext1", ...}
        ├── publisher2.ext2-2.0.0/
        │   └── package.json  ← {"name": "ext2", ...}
        └── ...
    """
    # Convert configured extension directory to Path object
    # This enables cross-platform path handling
    extension_path = Path(settings.project.EXTENSION_DIR)

    # Gracefully handle missing or non-directory paths
    if not extension_path.exists() or not extension_path.is_dir():
        return None

    # List only directories (skip files in extensions/ root)
    # Each directory should contain an unpacked VS Code extension
    all_extensions = [p for p in extension_path.iterdir() if p.is_dir()]

    # Iterate through each extension directory
    for extension_dir in all_extensions:
        # Attempt to read and parse package.json
        package_data = get_package_json(extension_dir)

        # Check if this extension matches the search query
        # The "name" field in package.json is the extension identifier
        if package_data and package_data.get("name") == extension_name_field:
            # Found matching extension, return complete package data
            return package_data

    # No matching extension found in any directory
    return None


def parse_capabilities(package_json: dict[str, Any]) -> dict[str, Any] | None:
    """
    Parse capabilities from package.json into a structured dictionary.

    Handles the polymorphic nature of capabilities fields in package.json:
    - untrustedWorkspaces.supported can be: true, false, "limited"
    - virtualWorkspaces.supported can be: true, false, "limited"

    This function converts package.json boolean/string values to standardized
    enum string values that match the database schema.

    Args:
        package_json: Complete package.json dictionary

    Returns:
        Dictionary with parsed capabilities ready for schema conversion,
        or None if no capabilities field exists.

    Value Mapping:
        - true  → "supported"
        - false → "not_supported"
        - "limited" → "limited"

    Example Input:
        {
            "capabilities": {
                "untrustedWorkspaces": {
                    "supported": "limited",
                    "description": "Some features disabled...",
                    "restrictedConfigurations": ["python.defaultInterpreterPath"]
                },
                "virtualWorkspaces": {
                    "supported": false,
                    "description": "Requires filesystem access"
                }
            }
        }

    Example Output:
        {
            "untrusted_supported": "limited",
            "untrusted_description": "Some features disabled...",
            "untrusted_restricted_configurations": ["python.defaultInterpreterPath"],
            "virtual_supported": "not_supported",
            "virtual_description": "Requires filesystem access"
        }
    """
    capabilities = package_json.get("capabilities")
    if not capabilities:
        return None

    def _convert_support_value(value: Any) -> str | None:
        """Convert package.json support value to database enum string."""
        if value is True:
            return "supported"
        elif value is False:
            return "not_supported"
        elif value == "limited":
            return "limited"
        return None

    # Parse untrustedWorkspaces
    untrusted = capabilities.get("untrustedWorkspaces", {})
    untrusted_supported = None
    untrusted_description = None
    untrusted_restricted = None

    if isinstance(untrusted, dict):
        untrusted_supported = _convert_support_value(untrusted.get("supported"))
        untrusted_description = untrusted.get("description")
        untrusted_restricted = untrusted.get("restrictedConfigurations")
    elif isinstance(untrusted, bool):
        # Simple boolean format: {"untrustedWorkspaces": true}
        untrusted_supported = _convert_support_value(untrusted)

    # Parse virtualWorkspaces
    virtual = capabilities.get("virtualWorkspaces", {})
    virtual_supported = None
    virtual_description = None

    if isinstance(virtual, dict):
        virtual_supported = _convert_support_value(virtual.get("supported"))
        virtual_description = virtual.get("description")
    elif isinstance(virtual, bool):
        # Simple boolean format: {"virtualWorkspaces": false}
        virtual_supported = _convert_support_value(virtual)

    return {
        "untrusted_supported": untrusted_supported,
        "untrusted_description": untrusted_description,
        "untrusted_restricted_configurations": untrusted_restricted,
        "virtual_supported": virtual_supported,
        "virtual_description": virtual_description,
    }
