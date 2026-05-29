"""Framework-agnostic static-detection contracts (ES-1, ADR 0016).

Schema-first landing for the static analysis pre-check stage. Kept as a
dedicated subpackage (not re-exported through the top-level
``packages.analysis_contracts`` facade) so the contracts <-> automation /
coverage circular-import ordering in ``contracts.py`` is left untouched.
"""

from packages.analysis_contracts.static_detection.finding import (
    StaticDetectionFinding,
    StaticEvidenceRef,
    StaticEvidenceType,
)
from packages.analysis_contracts.static_detection.gate import (
    StaticGateDecision,
    StaticGateOutcome,
)
from packages.analysis_contracts.static_detection.report import (
    StaticDetectionReport,
    StaticSeverityCounts,
    StaticTool,
    StaticToolExecutionRecord,
)

__all__ = [
    "StaticDetectionFinding",
    "StaticDetectionReport",
    "StaticEvidenceRef",
    "StaticEvidenceType",
    "StaticGateDecision",
    "StaticGateOutcome",
    "StaticSeverityCounts",
    "StaticTool",
    "StaticToolExecutionRecord",
]
