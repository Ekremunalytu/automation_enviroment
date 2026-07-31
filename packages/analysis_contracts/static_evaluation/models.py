"""Schema-first SMF corpus, expectation, metric, and result contracts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from packages.analysis_contracts.contracts import StrictContractModel
from packages.analysis_contracts.static_detection import (
    StaticGateDecision,
    StaticScanCoverage,
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
MetricValue = float | Literal["not_applicable"]
CorpusSplit = Literal["tuning", "holdout"]
CorpusLabel = Literal[
    "malicious_behavior",
    "vulnerable",
    "benign",
    "coverage_control",
]
SafetyState = Literal["declawed", "benign_control"]
NonNegativeMillis = Annotated[int, Field(ge=0)]


def _validate_relative_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:/", normalized)
        or any(part == ".." for part in normalized.split("/"))
        or any(ord(char) < 32 for char in normalized)
    ):
        raise ValueError("relative_path must stay within the corpus root")
    return normalized


class CorpusSample(StrictContractModel):
    schema_version: Literal["1"] = "1"
    sample_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9._-]+$")
    relative_path: str
    sha256: str
    split: CorpusSplit
    label: CorpusLabel
    families: list[str] = Field(min_length=1, max_length=16)
    variant: str = Field(min_length=1, max_length=120)
    platform: Literal["any", "linux", "darwin", "win32"] = "any"
    provenance: str = Field(min_length=1, max_length=500)
    safety_state: SafetyState
    expected_gate: StaticGateDecision
    must_fire: list[str] = Field(default_factory=list, max_length=64)
    may_fire: list[str] = Field(default_factory=list, max_length=64)
    must_not_fire: list[str] = Field(default_factory=list, max_length=64)
    expected_coverage: list[str] = Field(default_factory=list, max_length=64)
    expected_inconclusive_reasons: list[str] = Field(
        default_factory=list, max_length=64
    )
    notes: str = Field(default="", max_length=1000)

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        return _validate_relative_path(value)

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        if not _SHA256.fullmatch(value):
            raise ValueError("sha256 must be canonical lowercase SHA-256")
        return value

    @field_validator(
        "families",
        "must_fire",
        "may_fire",
        "must_not_fire",
        "expected_coverage",
        "expected_inconclusive_reasons",
    )
    @classmethod
    def validate_unique_values(cls, value: list[str]) -> list[str]:
        if any(not item for item in value):
            raise ValueError("list values must be non-empty")
        if len(value) != len(set(value)):
            raise ValueError("list values must be unique")
        return sorted(value)

    @model_validator(mode="after")
    def validate_expectations(self) -> CorpusSample:
        required = set(self.must_fire)
        optional = set(self.may_fire)
        forbidden = set(self.must_not_fire)
        if required & optional or required & forbidden or optional & forbidden:
            raise ValueError("rule expectations must not contradict each other")
        if self.expected_gate is StaticGateDecision.INCONCLUSIVE:
            if not self.expected_inconclusive_reasons:
                raise ValueError(
                    "inconclusive samples require expected_inconclusive_reasons"
                )
        elif self.expected_inconclusive_reasons:
            raise ValueError(
                "expected_inconclusive_reasons require expected_gate=inconclusive"
            )
        return self


class CorpusManifest(StrictContractModel):
    schema_version: Literal["1"] = "1"
    corpus_id: str = Field(min_length=1, max_length=80)
    samples: list[CorpusSample] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_unique_samples(self) -> CorpusManifest:
        ids = [sample.sample_id for sample in self.samples]
        paths = [sample.relative_path for sample in self.samples]
        if len(ids) != len(set(ids)):
            raise ValueError("sample_id values must be unique")
        if len(paths) != len(set(paths)):
            raise ValueError("sample relative_path values must be unique")
        return self

    def validate_rule_ids(self, known_rule_ids: set[str]) -> None:
        referenced = {
            rule_id
            for sample in self.samples
            for rule_id in (*sample.must_fire, *sample.may_fire, *sample.must_not_fire)
        }
        unknown = sorted(referenced - known_rule_ids)
        if unknown:
            raise ValueError(f"unknown rule ids in corpus manifest: {unknown}")


class FindingFingerprint(StrictContractModel):
    rule_id: str
    rule_version: str
    normalized_relative_path: str
    evidence_type: str
    normalized_match_shape: str

    @field_validator("normalized_relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        return _validate_relative_path(value)


class SampleEvaluation(StrictContractModel):
    sample_id: str
    split: CorpusSplit
    label: CorpusLabel
    observed_gate: StaticGateDecision
    expected_gate: StaticGateDecision
    fired_rule_ids: list[str] = Field(default_factory=list)
    missing_rule_ids: list[str] = Field(default_factory=list)
    unexpected_rule_ids: list[str] = Field(default_factory=list)
    finding_fingerprints: list[FindingFingerprint] = Field(default_factory=list)
    coverage: StaticScanCoverage = Field(default_factory=StaticScanCoverage)
    tool_duration_ms: dict[str, NonNegativeMillis] = Field(default_factory=dict)
    duration_ms: int = Field(ge=0)
    passed: bool
    errors: list[str] = Field(default_factory=list, max_length=64)

    @field_validator("tool_duration_ms")
    @classmethod
    def validate_tool_durations(cls, value: dict[str, int]) -> dict[str, int]:
        if len(value) > 8 or any(not key or len(key) > 40 for key in value):
            raise ValueError("tool duration accounting must be bounded")
        return dict(sorted(value.items()))


class RuleMetric(StrictContractModel):
    key: str
    true_positive: int = Field(default=0, ge=0)
    false_positive: int = Field(default=0, ge=0)
    false_negative: int = Field(default=0, ge=0)
    true_negative: int = Field(default=0, ge=0)
    precision: MetricValue
    recall: MetricValue
    false_positive_rate: MetricValue
    noise: MetricValue


class EvaluationResult(StrictContractModel):
    schema_version: Literal["1"] = "1"
    evaluation_id: str = Field(min_length=1, max_length=120)
    rules_bundle_fingerprint: str
    corpus_manifest_sha256: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    sample_results: list[SampleEvaluation]
    sample_metric: RuleMetric
    rule_metrics: list[RuleMetric] = Field(default_factory=list)
    family_metrics: list[RuleMetric] = Field(default_factory=list)
    coverage_summary: StaticScanCoverage = Field(default_factory=StaticScanCoverage)
    runtime_summary: dict[str, int | float | str] = Field(default_factory=dict)
    determinism_summary: dict[str, int | bool | str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list, max_length=128)

    @field_validator("rules_bundle_fingerprint", "corpus_manifest_sha256")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        if not _SHA256.fullmatch(value):
            raise ValueError("evaluation fingerprints must be lowercase SHA-256")
        return value

    def normalized_payload(self) -> dict[str, object]:
        """Return the stable comparison payload without audit-only values."""

        dumped = self.model_dump(mode="json")
        dumped.pop("evaluation_id", None)
        dumped.pop("started_at", None)
        dumped.pop("completed_at", None)
        dumped.pop("runtime_summary", None)
        for sample in dumped.get("sample_results", []):
            if isinstance(sample, dict):
                sample.pop("duration_ms", None)
                sample.pop("tool_duration_ms", None)
        return dumped
