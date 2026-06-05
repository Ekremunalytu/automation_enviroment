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
    OfflineExtension,
    OfflineIngestRequest,
    VsixExtractionMetrics,
    VsixThresholdBreachDetail,
)
from appcore.contracts.schema_defs.security_settings import (
    ThresholdBoundsResponse,
    ThresholdsResponse,
    ThresholdsUpdateRequest,
)
from appcore.contracts.schema_defs.static_analysis_bundle import (
    CombinedAnalysisBundle,
    StaticAnalysisReport,
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
    "CombinedAnalysisBundle",
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
    "OfflineExtension",
    "OfflineIngestRequest",
    "ScanRequest",
    "SearchAllExtensionsInfo",
    "SearchRequest",
    "StaticAnalysisReport",
    "ThresholdBoundsResponse",
    "ThresholdsResponse",
    "ThresholdsUpdateRequest",
    "VsixExtractionMetrics",
    "VsixThresholdBreachDetail",
]
