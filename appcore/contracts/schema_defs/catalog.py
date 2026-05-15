"""Catalog-facing schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from appcore.contracts.schema_defs.common import CapabilitySupportState


class ExtensionCapabilitiesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    untrusted_supported: CapabilitySupportState | None = None
    untrusted_description: str | None = None
    untrusted_restricted_configurations: list[str] | None = None
    virtual_supported: CapabilitySupportState | None = None
    virtual_description: str | None = None


class ExtensionScriptsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    script_name: str
    script_command: dict[str, Any]


class ExtensionActivationEventsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    event_type: str = Field(..., max_length=64)
    event_value: str | None = Field(default=None, max_length=1024)


class ExtensionContributesKeybindingsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    key: str
    command: str
    when: str | None = None
    mac: str | None = None
    linux: str | None = None
    win: str | None = None
    args: dict[str, Any] | None = None


class ExtensionContributesMenusSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    menu_location: str
    command: str | None = None
    submenu: str | None = None
    when: str | None = None
    group: str | None = None
    alt: str | None = None


class ExtensionContributesAuthenticationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    auth_id: str
    label: str


class ExtensionContributesTerminalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    profile_id: str
    title: str
    icon: str | None = None


class ExtensionContributesCommandsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    command_id: str
    title: str
    category: str | None = None
    icon: dict[str, Any] | str | None = None
    when: str | None = None


class ExtensionContributesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    configuration: dict | None = None
    debuggers: list | None = None
    walkthroughs: list | None = None
    grammars: list | None = None
    colors: list | None = None
    icons: dict | None = None
    snippets: list | None = None
    views: dict | None = None
    viewsContainers: dict | None = None
    languages: list | None = None
    themes: list | None = None
    iconThemes: list | None = None
    productIconThemes: list | None = None
    jsonValidation: list | None = None
    problemMatchers: list | None = None
    problemPatterns: list | None = None
    taskDefinitions: list | None = None
    customEditors: list | None = None
    submenus: list | None = None
    viewsWelcome: list | None = None
    breakpoints: list | None = None
    configurationDefaults: dict | None = None
    typescriptServerPlugins: list | None = None
    keybindings: list[ExtensionContributesKeybindingsSchema] = Field(
        default_factory=list
    )
    menus: list[ExtensionContributesMenusSchema] = Field(default_factory=list)
    authentication: list[ExtensionContributesAuthenticationSchema] = Field(
        default_factory=list
    )
    terminal: list[ExtensionContributesTerminalSchema] = Field(default_factory=list)
    commands: list[ExtensionContributesCommandsSchema] = Field(default_factory=list)


class ExtensionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    name: str
    publisher: str
    version: str
    engines: dict[str, Any]
    license: str | None = None
    displayName: str | None = None
    description: str | None = None
    categories: list[str] | None = None
    keywords: list[str] | None = None
    galleryBanner: dict[str, Any] | None = None
    preview: bool | None = None
    badges: list[dict[str, Any]] | None = None
    markdown: str | None = None
    qna: str | bool | dict[str, Any] | None = None
    sponsor: dict[str, Any] | None = None
    icon: str | None = None
    pricing: str | None = None
    main: str | None = None
    browser: str | None = None
    dependencies: dict[str, Any] | None = None
    devDependencies: dict[str, Any] | None = None
    extensionPack: list[str] | None = None
    extensionDependencies: list[str] | None = None
    extensionKind: list[str] | None = None
    npm_fields: dict[str, Any] | None = None
    extra_fields: dict[str, Any] | None = None


class ScanRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Extension name to create/scan.")


class SearchRequest(BaseModel):
    name: str = Field(
        ..., min_length=1, description="Extension name to search for in the database."
    )
    publisher: str | None = Field(
        default=None,
        description="Publisher name to filter on (recommended for precise matching).",
    )
    version: str | None = Field(
        default=None,
        description="Specific extension version to target.",
    )


class SearchAllExtensionsInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    name: str
    publisher: str
    description: str | None = None
    version: str
    icon: str | None = None


class ExtensionDetailSchema(ExtensionSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    capabilities: ExtensionCapabilitiesSchema | None = None
    scripts: list[ExtensionScriptsSchema] = Field(default_factory=list)
    activation_events: list[ExtensionActivationEventsSchema] = Field(
        default_factory=list, max_length=512
    )
    contributes: ExtensionContributesSchema | None = None


__all__ = [
    "ExtensionActivationEventsSchema",
    "ExtensionCapabilitiesSchema",
    "ExtensionContributesAuthenticationSchema",
    "ExtensionContributesCommandsSchema",
    "ExtensionContributesKeybindingsSchema",
    "ExtensionContributesMenusSchema",
    "ExtensionContributesSchema",
    "ExtensionContributesTerminalSchema",
    "ExtensionDetailSchema",
    "ExtensionSchema",
    "ExtensionScriptsSchema",
    "ScanRequest",
    "SearchAllExtensionsInfo",
    "SearchRequest",
]
