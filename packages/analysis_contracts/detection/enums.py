"""Detection contract enums defined by ADR 0003."""
# mypy: disable-error-code=no-redef

from __future__ import annotations

from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python 3.10 executor compatibility

    class StrEnum(str, Enum):
        """Minimal stdlib-compatible fallback for Python < 3.11."""

        def __str__(self) -> str:
            return str(self.value)


class ContractStrEnum(StrEnum):
    """Shared string enum base for detection contracts."""


class Severity(ContractStrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Confidence(ContractStrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


_CONFIDENCE_HIGH_THRESHOLD = 0.85
_CONFIDENCE_MEDIUM_THRESHOLD = 0.65


def quantize_confidence(value: float) -> Confidence:
    """Map a numeric attribution confidence to the contract enum tier.

    Used so activation-layer risk signals and detection-layer findings
    share a single confidence vocabulary (ADR 0003 §4).
    """

    if value >= _CONFIDENCE_HIGH_THRESHOLD:
        return Confidence.HIGH
    if value >= _CONFIDENCE_MEDIUM_THRESHOLD:
        return Confidence.MEDIUM
    return Confidence.LOW


class Verdict(ContractStrEnum):
    MALICIOUS = "malicious"
    SUSPICIOUS = "suspicious"
    CLEAN_WITH_NOTES = "clean_with_notes"
    CLEAN = "clean"
    INCONCLUSIVE = "inconclusive"


class AdversaryClass(ContractStrEnum):
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"
    A6 = "A6"
    A7 = "A7"
    # A8: interactive reverse shell / remote command execution — a spawned OS
    # shell whose stdio is bridged to an outbound socket (extrace.a8.reverse_shell;
    # static counterpart extrace.s10.reverse_shell).
    A8 = "A8"


class RuleLifecycle(ContractStrEnum):
    DRAFT = "draft"
    FIXTURE_VALIDATED = "fixture_validated"
    SMOKE_VALIDATED = "smoke_validated"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"


class RuleExecutionStatus(ContractStrEnum):
    FIRED = "fired"
    SILENT = "silent"
    ERROR = "error"


__all__ = [
    "AdversaryClass",
    "Confidence",
    "RuleExecutionStatus",
    "RuleLifecycle",
    "Severity",
    "Verdict",
    "quantize_confidence",
]
