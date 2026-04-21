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
]
