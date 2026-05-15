"""Manifest parsing helpers for extension catalog ingestion."""

from __future__ import annotations

from typing import Any

# Mirror of the caps on ``ExtensionActivationEventsSchema`` /
# ``ExtensionDetailSchema.activation_events`` — kept here so the parser
# can short-circuit hostile manifests before Pydantic walks an
# adversarial list. Pydantic remains the safety net for any path that
# bypasses this parser.
_MAX_ACTIVATION_EVENTS = 512
_MAX_ACTIVATION_EVENT_TYPE_LEN = 64
_MAX_ACTIVATION_EVENT_VALUE_LEN = 1024


def parse_capabilities(package_json: dict[str, Any]) -> dict[str, Any] | None:
    capabilities = package_json.get("capabilities")
    if not capabilities:
        return None

    def _convert_support_value(value: Any) -> str | None:
        if value is True:
            return "supported"
        if value is False:
            return "not_supported"
        if value == "limited":
            return "limited"
        return None

    untrusted = capabilities.get("untrustedWorkspaces", {})
    untrusted_supported = None
    untrusted_description = None
    untrusted_restricted = None
    if isinstance(untrusted, dict):
        untrusted_supported = _convert_support_value(untrusted.get("supported"))
        untrusted_description = untrusted.get("description")
        untrusted_restricted = untrusted.get("restrictedConfigurations")
    elif isinstance(untrusted, bool):
        untrusted_supported = _convert_support_value(untrusted)

    virtual = capabilities.get("virtualWorkspaces", {})
    virtual_supported = None
    virtual_description = None
    if isinstance(virtual, dict):
        virtual_supported = _convert_support_value(virtual.get("supported"))
        virtual_description = virtual.get("description")
    elif isinstance(virtual, bool):
        virtual_supported = _convert_support_value(virtual)

    return {
        "untrusted_supported": untrusted_supported,
        "untrusted_description": untrusted_description,
        "untrusted_restricted_configurations": untrusted_restricted,
        "virtual_supported": virtual_supported,
        "virtual_description": virtual_description,
    }


def parse_scripts(package_json: dict[str, Any]) -> list[dict[str, Any]] | None:
    scripts = package_json.get("scripts")
    if not scripts or not isinstance(scripts, dict):
        return None

    parsed_scripts = []
    for script_name, script_command in scripts.items():
        if isinstance(script_command, str):
            command_data = {"command": script_command}
        elif isinstance(script_command, dict):
            command_data = script_command
        else:
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
    activation_events = package_json.get("activationEvents")
    if not activation_events or not isinstance(activation_events, list):
        return None

    activation_events = activation_events[:_MAX_ACTIVATION_EVENTS]

    parsed_events = []
    for event in activation_events:
        if not isinstance(event, str):
            continue
        if ":" not in event:
            if len(event) > _MAX_ACTIVATION_EVENT_TYPE_LEN:
                continue
            parsed_events.append({"event_type": event, "event_value": None})
            continue
        event_type, event_value = event.split(":", 1)
        if (
            len(event_type) > _MAX_ACTIVATION_EVENT_TYPE_LEN
            or len(event_value) > _MAX_ACTIVATION_EVENT_VALUE_LEN
        ):
            continue
        parsed_events.append({"event_type": event_type, "event_value": event_value})

    return parsed_events if parsed_events else None


def parse_contributes(package_json: dict[str, Any]) -> dict[str, Any] | None:
    contributes = package_json.get("contributes")
    if not contributes or not isinstance(contributes, dict):
        return None

    result: dict[str, Any] = {}

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


_DB_STORED_FIELDS = {
    "name",
    "version",
    "publisher",
    "engines",
    "license",
    "displayName",
    "description",
    "categories",
    "keywords",
    "galleryBanner",
    "preview",
    "badges",
    "markdown",
    "qna",
    "sponsor",
    "icon",
    "pricing",
    "main",
    "browser",
    "dependencies",
    "devDependencies",
    "extensionPack",
    "extensionDependencies",
    "extensionKind",
}
_PARSED_FIELDS = {"capabilities", "scripts", "activationEvents", "contributes"}
_NPM_FIELDS = {
    "repository",
    "bugs",
    "homepage",
    "author",
    "contributors",
    "funding",
    "private",
    "type",
    "exports",
    "imports",
    "workspaces",
    "bin",
    "files",
    "typings",
    "types",
    "module",
    "sideEffects",
    "browserslist",
    "eslintConfig",
    "prettier",
    "jest",
    "husky",
    "lint-staged",
    "config",
    "publishConfig",
    "packageManager",
    "directories",
    "man",
    "cpu",
    "os",
}
_VSCODE_FIELDS = {"l10n", "enabledApiProposals", "enableProposedApi"}


def parse_npm_fields(package_json: dict[str, Any]) -> dict[str, Any] | None:
    npm = {key: value for key, value in package_json.items() if key in _NPM_FIELDS}
    return npm if npm else None


def parse_extra_fields(package_json: dict[str, Any]) -> dict[str, Any] | None:
    all_known = _DB_STORED_FIELDS | _PARSED_FIELDS | _NPM_FIELDS | _VSCODE_FIELDS
    extra = {key: value for key, value in package_json.items() if key not in all_known}
    return extra if extra else None


__all__ = [
    "parse_activation_events",
    "parse_capabilities",
    "parse_contributes",
    "parse_extra_fields",
    "parse_npm_fields",
    "parse_scripts",
]
