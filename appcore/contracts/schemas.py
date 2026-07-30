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
from appcore.contracts.schema_defs.executor_settings import (
    ExecutorPreferencesResponse,
    ExecutorPreferencesUpdateRequest,
)
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
from appcore.contracts.schema_defs.system_health import (
    SystemHealthResponse,
    SystemInventoryItem,
    SystemMetric,
    SystemServiceHealth,
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
    "ExecutorPreferencesResponse",
    "ExecutorPreferencesUpdateRequest",
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
    "SystemHealthResponse",
    "SystemInventoryItem",
    "SystemMetric",
    "SystemServiceHealth",
    "ThresholdBoundsResponse",
    "ThresholdsResponse",
    "ThresholdsUpdateRequest",
    "VsixExtractionMetrics",
    "VsixThresholdBreachDetail",
]
