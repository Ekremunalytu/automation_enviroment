"""Framework-agnostic static-detection contracts (ES-1, ADR 0016).

Schema-first landing for the static analysis pre-check stage. Kept as a
dedicated subpackage (not re-exported through the top-level
``packages.analysis_contracts`` facade) so the contracts <-> automation /
coverage circular-import ordering in ``contracts.py`` is left untouched.
"""

from packages.analysis_contracts.static_detection.artifact import (
    StaticArtifactDisposition,
    StaticArtifactDispositionReason,
    StaticArtifactEntrypointReachability,
    StaticArtifactFormat,
    StaticArtifactInventoryEntry,
    StaticArtifactReachabilityConfidence,
    StaticArtifactReachabilityEdgeKind,
    StaticArtifactRole,
)
from packages.analysis_contracts.static_detection.budget import (
    STATIC_ANALYSIS_DEFAULT_TIMEOUT_BUDGET_S,
    STATIC_ANALYSIS_MAX_TIMEOUT_BUDGET_S,
    STATIC_ANALYSIS_MIN_TIMEOUT_BUDGET_S,
    STATIC_ANALYZER_EXEC_GRACE_S,
    parse_static_analysis_timeout_budget,
    validate_static_analysis_timeout_budget,
)
from packages.analysis_contracts.static_detection.deduplication import (
    StaticFindingDeduplicationReason,
    StaticFindingDeduplicationRecord,
)
from packages.analysis_contracts.static_detection.finding import (
    StaticDetectionFinding,
    StaticEvidenceRef,
    StaticEvidenceType,
)
from packages.analysis_contracts.static_detection.gate import (
    StaticGateDecision,
    StaticGateOutcome,
)
from packages.analysis_contracts.static_detection.reachability import (
    StaticReachabilityLimitReason,
    StaticReachabilitySummary,
    StaticReachabilityUnresolvedReference,
)
from packages.analysis_contracts.static_detection.report import (
    StaticCoverageReason,
    StaticDetectionReport,
    StaticManifestStatus,
    StaticScanCoverage,
    StaticSeverityCounts,
    StaticTool,
    StaticToolExecutionRecord,
)

__all__ = [
    "STATIC_ANALYSIS_DEFAULT_TIMEOUT_BUDGET_S",
    "STATIC_ANALYSIS_MAX_TIMEOUT_BUDGET_S",
    "STATIC_ANALYSIS_MIN_TIMEOUT_BUDGET_S",
    "STATIC_ANALYZER_EXEC_GRACE_S",
    "StaticArtifactDisposition",
    "StaticArtifactDispositionReason",
    "StaticArtifactEntrypointReachability",
    "StaticArtifactFormat",
    "StaticArtifactInventoryEntry",
    "StaticArtifactReachabilityConfidence",
    "StaticArtifactReachabilityEdgeKind",
    "StaticArtifactRole",
    "StaticCoverageReason",
    "StaticDetectionFinding",
    "StaticDetectionReport",
    "StaticEvidenceRef",
    "StaticEvidenceType",
    "StaticFindingDeduplicationReason",
    "StaticFindingDeduplicationRecord",
    "StaticGateDecision",
    "StaticGateOutcome",
    "StaticManifestStatus",
    "StaticReachabilityLimitReason",
    "StaticReachabilitySummary",
    "StaticReachabilityUnresolvedReference",
    "StaticScanCoverage",
    "StaticSeverityCounts",
    "StaticTool",
    "StaticToolExecutionRecord",
    "parse_static_analysis_timeout_budget",
    "validate_static_analysis_timeout_budget",
]
