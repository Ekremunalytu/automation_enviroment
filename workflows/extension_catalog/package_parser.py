"""Public manifest parsing facade for the extension catalog workflow."""

from workflows.extension_catalog.manifest_parser import (
    parse_activation_events,
    parse_capabilities,
    parse_contributes,
    parse_extra_fields,
    parse_npm_fields,
    parse_scripts,
)
from workflows.extension_catalog.manifest_reader import (
    get_package_json,
    parse_json_file,
    search_extension,
)

__all__ = [
    "get_package_json",
    "parse_activation_events",
    "parse_capabilities",
    "parse_contributes",
    "parse_extra_fields",
    "parse_json_file",
    "parse_npm_fields",
    "parse_scripts",
    "search_extension",
]
