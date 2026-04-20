"""Rule interface for framework-agnostic detection rules."""

from __future__ import annotations

from typing import Protocol

from packages.analysis_contracts import ActivationReport
from packages.analysis_contracts.detection import (
    AdversaryClass,
    DetectionFinding,
    RuleLifecycle,
    Severity,
)


class DetectionRule(Protocol):
    rule_id: str
    rule_version: str
    lifecycle: RuleLifecycle
    adversary_class: AdversaryClass | None
    severity: Severity
    description: str

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        """Return findings when the rule matches the report."""


__all__ = ["DetectionRule"]
