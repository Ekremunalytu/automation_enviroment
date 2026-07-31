"""Deterministic confusion-matrix helpers for SMF evaluation."""

from __future__ import annotations

from packages.analysis_contracts.static_evaluation.models import MetricValue, RuleMetric


def _ratio(numerator: int, denominator: int) -> MetricValue:
    if denominator == 0:
        return "not_applicable"
    return numerator / denominator


def build_metric(
    *,
    key: str,
    true_positive: int,
    false_positive: int,
    false_negative: int,
    true_negative: int,
) -> RuleMetric:
    return RuleMetric(
        key=key,
        true_positive=true_positive,
        false_positive=false_positive,
        false_negative=false_negative,
        true_negative=true_negative,
        precision=_ratio(true_positive, true_positive + false_positive),
        recall=_ratio(true_positive, true_positive + false_negative),
        false_positive_rate=_ratio(false_positive, false_positive + true_negative),
        noise=_ratio(false_positive, true_positive + false_positive),
    )


__all__ = ["build_metric"]
