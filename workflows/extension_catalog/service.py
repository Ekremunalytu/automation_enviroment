"""Extension catalog workflow service (back-compat facade).

Production callers should import from `lifecycle` and `manifest_to_schema`
directly. This facade exists so external consumers that still hold the
legacy import path keep working without a flag day:

- `workflows/marketplace/router.py` imports `ExtensionManifestMismatchError`,
  `create_extension_from_directory`, and `search_extension_by_name`
  directly from this module.
- `tests/platform/test_canonical_imports.py` imports the module to assert
  the public-surface symbol set.
"""

from .lifecycle import (
    create_extension_by_name as create_extension_by_name,
)
from .lifecycle import (
    create_extension_from_directory as create_extension_from_directory,
)
from .lifecycle import (
    delete_extension_by_name as delete_extension_by_name,
)
from .lifecycle import (
    get_all_extensions_all as get_all_extensions_all,
)
from .lifecycle import (
    get_all_extensions_basic as get_all_extensions_basic,
)
from .lifecycle import (
    get_extension_activation_events as get_extension_activation_events,
)
from .lifecycle import (
    get_extension_capabilities as get_extension_capabilities,
)
from .lifecycle import (
    get_extension_contributes_all as get_extension_contributes_all,
)
from .lifecycle import (
    get_extension_contributes_commands as get_extension_contributes_commands,
)
from .lifecycle import (
    get_extension_scripts as get_extension_scripts,
)
from .lifecycle import (
    search_extension_by_name as search_extension_by_name,
)
from .manifest_to_schema import (
    ExtensionManifestMismatchError as ExtensionManifestMismatchError,
)

__all__ = [
    "ExtensionManifestMismatchError",
    "create_extension_by_name",
    "create_extension_from_directory",
    "delete_extension_by_name",
    "get_all_extensions_all",
    "get_all_extensions_basic",
    "get_extension_activation_events",
    "get_extension_capabilities",
    "get_extension_contributes_all",
    "get_extension_contributes_commands",
    "get_extension_scripts",
    "search_extension_by_name",
]
