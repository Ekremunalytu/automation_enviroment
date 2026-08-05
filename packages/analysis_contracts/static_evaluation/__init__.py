"""Provider-free contracts for deterministic static-analysis evaluation."""

from packages.analysis_contracts.static_evaluation.models import (
    CorpusManifest,
    CorpusSample,
    EvaluationArtifactSummary,
    EvaluationCapability,
    EvaluationDeltaResult,
    EvaluationResult,
    FindingFingerprint,
    IntegerDelta,
    MetricValue,
    RuleMetric,
    RuntimeDelta,
    SampleEvaluation,
    SampleEvaluationDelta,
    SplitEvaluationDelta,
)

__all__ = [
    "CorpusManifest",
    "CorpusSample",
    "EvaluationArtifactSummary",
    "EvaluationCapability",
    "EvaluationDeltaResult",
    "EvaluationResult",
    "FindingFingerprint",
    "IntegerDelta",
    "MetricValue",
    "RuleMetric",
    "RuntimeDelta",
    "SampleEvaluation",
    "SampleEvaluationDelta",
    "SplitEvaluationDelta",
]
