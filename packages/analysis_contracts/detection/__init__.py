"""Framework-agnostic detection contracts governed by ADR 0003."""

from packages.analysis_contracts.detection.enums import (
    AdversaryClass,
    Confidence,
    RuleExecutionStatus,
    RuleLifecycle,
    Severity,
    Verdict,
    quantize_confidence,
)
from packages.analysis_contracts.detection.finding import DetectionFinding, EvidenceRef
from packages.analysis_contracts.detection.report import (
    AutomationHealthStatus,
    DetectionReport,
    ExtensionIdentity,
    RuleExecutionRecord,
)
from packages.analysis_contracts.detection.rollup import compute_verdict

__all__ = [
    "AdversaryClass",
    "AutomationHealthStatus",
    "Confidence",
    "DetectionFinding",
    "DetectionReport",
    "EvidenceRef",
    "ExtensionIdentity",
    "RuleExecutionRecord",
    "RuleExecutionStatus",
    "RuleLifecycle",
    "Severity",
    "Verdict",
    "compute_verdict",
    "quantize_confidence",
]
