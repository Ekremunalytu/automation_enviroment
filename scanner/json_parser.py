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

import json
from pathlib import Path
from core.config import settings


def parse_json_file(json_path: Path) -> dict | None:
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
        with open(json_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        # Log error for debugging but don't crash
        # In production, consider using proper logging framework
        print(f"JSON read error ({json_path}): {e}")
        return None


def get_package_json(extension_dir: Path) -> dict | None:
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


def search_extension(extension_name_field: str) -> dict | None:
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
    extension_path = Path(settings.EXTENSION_DIR)

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