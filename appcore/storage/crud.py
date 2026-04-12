"""Public CRUD facade for ExTrace storage."""

from appcore.storage.crud_ops.reads import (
    get_db_extensions_base_info,
    get_extension_by_id,
    get_extensions_all_info,
    search_extension_by_name,
)
from appcore.storage.crud_ops.relations import (
    get_extension_activation_events,
    get_extension_capabilities,
    get_extension_contributes_all,
    get_extension_contributes_commands,
    get_extension_scripts,
)
from appcore.storage.crud_ops.writes import create_extension, delete_extension

__all__ = [
    "create_extension",
    "delete_extension",
    "get_db_extensions_base_info",
    "get_extension_activation_events",
    "get_extension_by_id",
    "get_extension_capabilities",
    "get_extension_contributes_all",
    "get_extension_contributes_commands",
    "get_extension_scripts",
    "get_extensions_all_info",
    "search_extension_by_name",
]
