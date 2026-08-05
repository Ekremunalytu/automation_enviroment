"""Schema-first SMF corpus, expectation, metric, and result contracts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from packages.analysis_contracts.contracts import StrictContractModel
from packages.analysis_contracts.static_detection import (
    StaticGateDecision,
    StaticReachabilitySummary,
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
EvaluationCapability = Literal[
    "artifact_inventory",
    "finding_deduplication",
    "reachability",
]


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


class EvaluationArtifactSummary(StrictContractModel):
    """Bounded SAP-6 measurement extracted from one production static report."""

    retained_finding_count: int = Field(default=0, ge=0)
    suppressed_findings_by_reason: dict[str, int] = Field(default_factory=dict)
    artifact_dispositions: dict[str, int] = Field(default_factory=dict)
    artifact_reachability: dict[str, int] = Field(default_factory=dict)
    reachability: StaticReachabilitySummary = Field(
        default_factory=StaticReachabilitySummary
    )
    capabilities: list[EvaluationCapability] = Field(default_factory=list)

    @field_validator(
        "suppressed_findings_by_reason",
        "artifact_dispositions",
        "artifact_reachability",
    )
    @classmethod
    def validate_bounded_count_maps(cls, value: dict[str, int]) -> dict[str, int]:
        if len(value) > 32:
            raise ValueError("evaluation count maps are limited to 32 keys")
        if any(not key or len(key) > 80 or count < 0 for key, count in value.items()):
            raise ValueError("evaluation count maps require bounded keys and counts")
        return dict(sorted(value.items()))

    @field_validator("capabilities")
    @classmethod
    def normalize_capabilities(
        cls, value: list[EvaluationCapability]
    ) -> list[EvaluationCapability]:
        return sorted(set(value))


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
    artifact_summary: EvaluationArtifactSummary = Field(
        default_factory=EvaluationArtifactSummary
    )
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


class IntegerDelta(StrictContractModel):
    baseline: int
    candidate: int
    delta: int

    @model_validator(mode="after")
    def validate_delta(self) -> IntegerDelta:
        if self.delta != self.candidate - self.baseline:
            raise ValueError("integer delta must equal candidate minus baseline")
        return self


class RuntimeDelta(StrictContractModel):
    baseline_median_ms: int = Field(ge=0)
    candidate_median_ms: int = Field(ge=0)
    delta_ms: int

    @model_validator(mode="after")
    def validate_delta(self) -> RuntimeDelta:
        if self.delta_ms != self.candidate_median_ms - self.baseline_median_ms:
            raise ValueError("runtime delta must equal candidate minus baseline")
        return self


class SampleEvaluationDelta(StrictContractModel):
    sample_id: str
    split: CorpusSplit
    baseline_label: CorpusLabel
    candidate_label: CorpusLabel
    baseline_expected_gate: StaticGateDecision
    candidate_expected_gate: StaticGateDecision
    baseline_observed_gate: StaticGateDecision
    candidate_observed_gate: StaticGateDecision
    added_rule_ids: list[str] = Field(default_factory=list)
    removed_rule_ids: list[str] = Field(default_factory=list)
    retained_findings: IntegerDelta
    suppressed_findings: IntegerDelta
    candidate_passed: bool

    @field_validator("added_rule_ids", "removed_rule_ids")
    @classmethod
    def normalize_rule_ids(cls, value: list[str]) -> list[str]:
        return sorted(set(value))


class SplitEvaluationDelta(StrictContractModel):
    split: Literal["tuning", "holdout", "all"]
    sample_count: int = Field(ge=1)
    baseline_sample_metric: RuleMetric
    candidate_sample_metric: RuleMetric
    coverage_counts: dict[str, IntegerDelta] = Field(default_factory=dict)
    artifact_dispositions: dict[str, IntegerDelta] = Field(default_factory=dict)
    artifact_reachability: dict[str, IntegerDelta] = Field(default_factory=dict)
    suppression_counts: dict[str, IntegerDelta] = Field(default_factory=dict)
    runtime: dict[str, RuntimeDelta] = Field(default_factory=dict)
    sample_deltas: list[SampleEvaluationDelta]


class EvaluationDeltaResult(StrictContractModel):
    schema_version: Literal["1"] = "1"
    baseline_ref: str = Field(min_length=1, max_length=120)
    candidate_ref: str = Field(min_length=1, max_length=120)
    baseline_rules_bundle_fingerprint: str
    candidate_rules_bundle_fingerprint: str
    baseline_corpus_manifest_sha256: str
    candidate_corpus_manifest_sha256: str
    baseline_capabilities: list[EvaluationCapability] = Field(default_factory=list)
    candidate_capabilities: list[EvaluationCapability] = Field(default_factory=list)
    splits: list[SplitEvaluationDelta] = Field(min_length=3, max_length=3)
    acceptance_checks: dict[str, bool]
    errors: list[str] = Field(default_factory=list, max_length=128)
    passed: bool

    @field_validator(
        "baseline_rules_bundle_fingerprint",
        "candidate_rules_bundle_fingerprint",
        "baseline_corpus_manifest_sha256",
        "candidate_corpus_manifest_sha256",
    )
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        if not _SHA256.fullmatch(value):
            raise ValueError("evaluation delta fingerprints must be lowercase SHA-256")
        return value

    @field_validator("acceptance_checks")
    @classmethod
    def normalize_acceptance_checks(cls, value: dict[str, bool]) -> dict[str, bool]:
        if not value or len(value) > 64 or any(not key for key in value):
            raise ValueError("evaluation delta requires bounded acceptance checks")
        return dict(sorted(value.items()))

    @field_validator("baseline_capabilities", "candidate_capabilities")
    @classmethod
    def normalize_capabilities(
        cls, value: list[EvaluationCapability]
    ) -> list[EvaluationCapability]:
        return sorted(set(value))

    @model_validator(mode="after")
    def validate_result(self) -> EvaluationDeltaResult:
        if self.passed != (not self.errors and all(self.acceptance_checks.values())):
            raise ValueError("delta passed state must agree with errors and checks")
        if {item.split for item in self.splits} != {"tuning", "holdout", "all"}:
            raise ValueError(
                "evaluation delta requires tuning, holdout, and all splits"
            )
        return self


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
