"""SMF confusion-matrix metric semantics."""

from packages.analysis_contracts.static_evaluation.metrics import build_metric


def test_metric_uses_not_applicable_for_zero_denominators() -> None:
    metric = build_metric(
        key="empty",
        true_positive=0,
        false_positive=0,
        false_negative=0,
        true_negative=0,
    )
    assert metric.precision == "not_applicable"
    assert metric.recall == "not_applicable"
    assert metric.false_positive_rate == "not_applicable"
    assert metric.noise == "not_applicable"


def test_metric_calculates_precision_recall_and_false_positive_rate() -> None:
    metric = build_metric(
        key="rule",
        true_positive=3,
        false_positive=1,
        false_negative=1,
        true_negative=5,
    )
    assert metric.precision == 0.75
    assert metric.recall == 0.75
    assert metric.false_positive_rate == 1 / 6
    assert metric.noise == 0.25
