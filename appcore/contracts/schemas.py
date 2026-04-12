"""Public schema facade for ExTrace."""

from appcore.contracts.schema_defs.catalog import (
    ExtensionActivationEventsSchema,
    ExtensionCapabilitiesSchema,
    ExtensionContributesAuthenticationSchema,
    ExtensionContributesCommandsSchema,
    ExtensionContributesKeybindingsSchema,
    ExtensionContributesMenusSchema,
    ExtensionContributesSchema,
    ExtensionContributesTerminalSchema,
    ExtensionDetailSchema,
    ExtensionSchema,
    ExtensionScriptsSchema,
    ScanRequest,
    SearchAllExtensionsInfo,
    SearchRequest,
)
from appcore.contracts.schema_defs.common import CapabilitySupportState
from appcore.contracts.schema_defs.marketplace import (
    AnalyzeJobStatusResponse,
    AnalyzeJobStep,
    AnalyzeRequest,
    AnalyzeResponse,
    MarketplaceDownloadRequest,
    MarketplaceDownloadResponse,
    MarketplaceExtension,
)

__all__ = [
    "AnalyzeJobStatusResponse",
    "AnalyzeJobStep",
    "AnalyzeRequest",
    "AnalyzeResponse",
    "CapabilitySupportState",
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
    "MarketplaceDownloadRequest",
    "MarketplaceDownloadResponse",
    "MarketplaceExtension",
    "ScanRequest",
    "SearchAllExtensionsInfo",
    "SearchRequest",
]
