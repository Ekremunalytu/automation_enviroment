"""Rule interface for in-house static rules (ES-3a, ADR 0016).

Mirrors ``packages.analysis_engine.rules.base.DetectionRule`` but evaluates a
``StaticAnalysisContext`` (a parsed VSIX tree) into ``StaticDetectionFinding``s
rather than an ``ActivationReport`` into ``DetectionFinding``s.
"""

from __future__ import annotations

from typing import Protocol

from packages.analysis_contracts.detection.enums import (
    AdversaryClass,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.static_detection import StaticDetectionFinding
from static_runtime.context import StaticAnalysisContext


class StaticRule(Protocol):
    rule_id: str
    rule_version: str
    lifecycle: RuleLifecycle
    adversary_class: AdversaryClass | None
    severity: Severity
    description: str

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        """Return findings when the rule matches the decompressed extension."""


__all__ = ["StaticRule"]
