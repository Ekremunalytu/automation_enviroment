"""Public ORM facade for ExTrace."""

from appcore.storage.model_defs.base import Base, capability_support_enum
from appcore.storage.model_defs.contributes import (
    ExtensionContributes,
    ExtensionContributesAuthentication,
    ExtensionContributesCommands,
    ExtensionContributesKeybindings,
    ExtensionContributesMenus,
    ExtensionContributesTerminal,
)
from appcore.storage.model_defs.extension import (
    Extension,
    ExtensionActivationEvents,
    ExtensionCapabilities,
    ExtensionScripts,
)

__all__ = [
    "Base",
    "Extension",
    "ExtensionActivationEvents",
    "ExtensionCapabilities",
    "ExtensionContributes",
    "ExtensionContributesAuthentication",
    "ExtensionContributesCommands",
    "ExtensionContributesKeybindings",
    "ExtensionContributesMenus",
    "ExtensionContributesTerminal",
    "ExtensionScripts",
    "capability_support_enum",
]
