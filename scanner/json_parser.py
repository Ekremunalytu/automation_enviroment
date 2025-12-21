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


def parse_scripts(package_json: dict[str, Any]) -> list[dict[str, Any]] | None:
    """
    Parse scripts from package.json into a list of structured dictionaries.

    Each script entry in package.json is converted to a dictionary with
    script_name and script_command fields matching the database schema.

    Args:
        package_json: Complete package.json dictionary

    Returns:
        List of dictionaries with parsed scripts ready for schema conversion,
        or None if no scripts field exists.

    Example Input:
        {
            "scripts": {
                "compile": "tsc -p ./",
                "watch": "tsc -watch -p ./",
                "test": "npm run compile && node ./out/test/runTest.js"
            }
        }

    Example Output:
        [
            {"script_name": "compile", "script_command": {"command": "tsc -p ./"}},
            {"script_name": "watch", "script_command": {"command": "tsc -watch"}},
            {"script_name": "test", "script_command": {"command": "npm run compile"}}
        ]
    """
    scripts = package_json.get("scripts")
    if not scripts or not isinstance(scripts, dict):
        return None

    parsed_scripts = []
    for script_name, script_command in scripts.items():
        # Convert string command to dict format for JSONB storage
        if isinstance(script_command, str):
            command_data = {"command": script_command}
        elif isinstance(script_command, dict):
            command_data = script_command
        else:
            # Skip invalid script entries
            continue

        parsed_scripts.append(
            {
                "script_name": script_name,
                "script_command": command_data,
            }
        )

    return parsed_scripts if parsed_scripts else None


def parse_activation_events(
    package_json: dict[str, Any],
) -> list[dict[str, Any]] | None:
    """
    Parse activationEvents from package.json into a list of structured dictionaries.

    Each activation event string is parsed into event_type and event_value components.
    Format: "eventType:eventValue" or just "eventType" (e.g., "*", "onStartupFinished")

    Args:
        package_json: Complete package.json dictionary

    Returns:
        List of dictionaries with parsed activation events ready for schema conversion,
        or None if no activationEvents field exists.

    Reference: https://code.visualstudio.com/api/references/activation-events

    Supported Event Types:
        - onLanguage:languageId (e.g., onLanguage:python)
        - onCommand:commandId (e.g., onCommand:extension.sayHello)
        - workspaceContains:globPattern (e.g., workspaceContains:**/.gitignore)
        - onFileSystem:scheme (e.g., onFileSystem:sftp)
        - onView:viewId (e.g., onView:nodeDependencies)
        - onUri (no value)
        - onWebviewPanel:viewType (e.g., onWebviewPanel:catCoding)
        - onCustomEditor:viewType (e.g., onCustomEditor:catCustoms.pawDraw)
        - onAuthenticationRequest:providerId (e.g., onAuthenticationRequest:github)
        - onStartupFinished (no value)
        - onTaskType:taskType (e.g., onTaskType:npm)
        - onNotebook:notebookType (e.g., onNotebook:jupyter-notebook)
        - onTerminal:shellType (e.g., onTerminal:bash)
        - onTerminalProfile:profileId
        - onWalkthrough:walkthroughId
        - onChatParticipant:participantId
        - onLanguageModelTool:toolId
        - * (startup - no value)

    Example Input:
        {
            "activationEvents": [
                "onLanguage:python",
                "onCommand:extension.activate",
                "workspaceContains:**/.gitignore",
                "*"
            ]
        }

    Example Output:
        [
            {"event_type": "onLanguage", "event_value": "python"},
            {"event_type": "onCommand", "event_value": "extension.activate"},
            {"event_type": "workspaceContains", "event_value": "**/.gitignore"},
            {"event_type": "*", "event_value": None}
        ]
    """
    activation_events = package_json.get("activationEvents")
    if not activation_events or not isinstance(activation_events, list):
        return None

    parsed_events = []
    for event in activation_events:
        if not isinstance(event, str):
            # Skip invalid entries
            continue

        # Handle events without value (e.g., "*", "onStartupFinished", "onUri")
        if ":" not in event:
            parsed_events.append(
                {
                    "event_type": event,
                    "event_value": None,
                }
            )
        else:
            # Split on first colon only (value may contain additional colons)
            # e.g., "onUri" has no colon, "onCommand:ext.cmd" splits to
            # ["onCommand", "ext.cmd"]
            parts = event.split(":", 1)
            event_type = parts[0]
            event_value = parts[1] if len(parts) > 1 else None

            parsed_events.append(
                {
                    "event_type": event_type,
                    "event_value": event_value,
                }
            )

    return parsed_events if parsed_events else None


def parse_contributes(package_json: dict[str, Any]) -> dict[str, Any] | None:
    """
    Parse contributes from package.json into a structured dictionary.

    Extracts contribution points from package.json and structures them for
    database storage. Child arrays (keybindings, menus, authentication, terminal)
    are parsed into lists of dictionaries. Complex structures are kept as-is
    for JSONB storage.

    Args:
        package_json: Complete package.json dictionary

    Returns:
        Dictionary with parsed contributes ready for schema conversion,
        or None if no contributes field exists.

    Reference: https://code.visualstudio.com/api/references/contribution-points

    Example Input:
        {
            "contributes": {
                "keybindings": [
                    {"key": "ctrl+shift+p", "command": "workbench.action.showCommands"}
                ],
                "menus": {
                    "editor/context": [
                        {"command": "extension.sayHello", "group": "navigation"}
                    ]
                },
                "authentication": [
                    {"id": "github", "label": "GitHub"}
                ],
                "terminal": {
                    "profiles": [
                        {"id": "my-profile", "title": "My Terminal"}
                    ]
                },
                "configuration": {...}
            }
        }

    Example Output:
        {
            "keybindings": [
                {"key": "ctrl+shift+p", "command": "workbench.action.showCommands", ...}
            ],
            "menus": [
                {"menu_location": "editor/context",
                 "command": "extension.sayHello", ...}
            ],
            "authentication": [
                {"auth_id": "github", "label": "GitHub"}
            ],
            "terminal": [
                {"profile_id": "my-profile", "title": "My Terminal"}
            ],
            "configuration": {...},
            ...
        }
    """
    contributes = package_json.get("contributes")
    if not contributes or not isinstance(contributes, dict):
        return None

    result: dict[str, Any] = {}

    # Parse keybindings (array of objects)
    keybindings = contributes.get("keybindings")
    if keybindings and isinstance(keybindings, list):
        parsed_keybindings = []
        for kb in keybindings:
            if isinstance(kb, dict) and "key" in kb and "command" in kb:
                parsed_keybindings.append(
                    {
                        "key": kb.get("key"),
                        "command": kb.get("command"),
                        "when": kb.get("when"),
                        "mac": kb.get("mac"),
                        "linux": kb.get("linux"),
                        "win": kb.get("win"),
                        "args": kb.get("args"),
                    }
                )
        if parsed_keybindings:
            result["keybindings"] = parsed_keybindings

    # Parse commands (array of objects)
    commands = contributes.get("commands")
    if commands and isinstance(commands, list):
        parsed_commands = []
        for cmd in commands:
            if isinstance(cmd, dict) and "command" in cmd and "title" in cmd:
                parsed_commands.append(
                    {
                        "command_id": cmd.get("command"),
                        "title": cmd.get("title"),
                        "category": cmd.get("category"),
                        "icon": cmd.get("icon"),
                        "when": cmd.get("when"),
                    }
                )
        if parsed_commands:
            result["commands"] = parsed_commands

    # Parse menus (object with arrays - flatten to list with menu_location)
    menus = contributes.get("menus")
    if menus and isinstance(menus, dict):
        parsed_menus = []
        for menu_location, menu_items in menus.items():
            if isinstance(menu_items, list):
                for item in menu_items:
                    if isinstance(item, dict):
                        parsed_menus.append(
                            {
                                "menu_location": menu_location,
                                "command": item.get("command"),
                                "submenu": item.get("submenu"),
                                "when": item.get("when"),
                                "group": item.get("group"),
                                "alt": item.get("alt"),
                            }
                        )
        if parsed_menus:
            result["menus"] = parsed_menus

    # Parse authentication (array of objects)
    authentication = contributes.get("authentication")
    if authentication and isinstance(authentication, list):
        parsed_auth = []
        for auth in authentication:
            if isinstance(auth, dict) and "id" in auth and "label" in auth:
                parsed_auth.append(
                    {
                        "auth_id": auth.get("id"),
                        "label": auth.get("label"),
                    }
                )
        if parsed_auth:
            result["authentication"] = parsed_auth

    # Parse terminal profiles (nested in terminal.profiles)
    terminal = contributes.get("terminal")
    if terminal and isinstance(terminal, dict):
        profiles = terminal.get("profiles")
        if profiles and isinstance(profiles, list):
            parsed_terminal = []
            for profile in profiles:
                if isinstance(profile, dict) and "id" in profile and "title" in profile:
                    parsed_terminal.append(
                        {
                            "profile_id": profile.get("id"),
                            "title": profile.get("title"),
                            "icon": profile.get("icon"),
                        }
                    )
            if parsed_terminal:
                result["terminal"] = parsed_terminal

    jsonb_fields = [
        "configuration",
        "debuggers",
        "walkthroughs",
        "grammars",
        "colors",
        "icons",
        "snippets",
        "views",
        "viewsContainers",
        "languages",
        "themes",
        "iconThemes",
        "productIconThemes",
        "jsonValidation",
        "problemMatchers",
        "problemPatterns",
        "taskDefinitions",
        "customEditors",
        "submenus",
        "viewsWelcome",
        "breakpoints",
        "configurationDefaults",
        "typescriptServerPlugins",
    ]

    for field in jsonb_fields:
        value = contributes.get(field)
        if value is not None:
            result[field] = value

    return result if result else None
