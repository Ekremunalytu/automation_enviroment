"""Public schema facade for ExTrace."""

from appcore.contracts.schema_defs.activation_reports import (
    ActivationReportMetadata,
    ActivationReportResponse,
)
from appcore.contracts.schema_defs.analysis_bundle import AnalysisBundle
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
    VsixExtractionMetrics,
    VsixThresholdBreachDetail,
)
from appcore.contracts.schema_defs.security_settings import (
    ThresholdBoundsResponse,
    ThresholdsResponse,
    ThresholdsUpdateRequest,
)

__all__ = [
    "ActivationReportMetadata",
    "ActivationReportResponse",
    "AnalysisBundle",
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
    "ThresholdBoundsResponse",
    "ThresholdsResponse",
    "ThresholdsUpdateRequest",
    "VsixExtractionMetrics",
    "VsixThresholdBreachDetail",
]
