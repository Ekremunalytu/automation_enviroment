"""Tests for executor risk-signal confidence-tier vocabulary.

These tests lock the invariant that the executor-side
``signal_policy._confidence_tier`` produces the same tier string as the
canonical ``packages.analysis_contracts.detection.enums.quantize_confidence``
function. The executor and the platform must share one confidence vocabulary
so that ``RiskSignal.confidence_tier`` and ``DetectionFinding.confidence``
agree for the same numeric input (ADR 0003 §4).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import signal_policy  # noqa: E402

from packages.analysis_contracts.detection.enums import (  # noqa: E402
    Confidence,
    quantize_confidence,
)


@pytest.mark.parametrize(
    "value",
    [
        0.0,
        0.1,
        0.5,
        0.6499,
        0.65,
        0.6500001,
        0.7,
        0.8499,
        0.85,
        0.85000001,
        0.95,
        1.0,
    ],
)
def test_executor_confidence_tier_matches_platform_quantize(value: float) -> None:
    """Executor `_confidence_tier` must equal `str(quantize_confidence(value))`.

    Without this, the executor could silently drift to a different threshold
    set than the platform's `DetectionFinding.confidence` vocabulary, and
    `RiskSignal.confidence_tier` would no longer be a faithful peer.
    """

    assert signal_policy._confidence_tier(value) == str(quantize_confidence(value))


def test_executor_confidence_tier_returns_canonical_enum_strings() -> None:
    """The tier output must be one of the `Confidence` enum string values."""

    valid_tiers = {str(member) for member in Confidence}
    sampled = [0.0, 0.5, 0.65, 0.85, 1.0]
    for value in sampled:
        assert signal_policy._confidence_tier(value) in valid_tiers


def test_make_signal_populates_tier_via_quantize_confidence() -> None:
    """`_make_signal` must wire `confidence_tier` through the shared function.

    Build a minimal RiskSignal-shaped object via a dataclass-like factory and
    assert the resulting `confidence_tier` string matches the canonical
    contract output for the same float.
    """

    captured: dict[str, object] = {}

    def fake_signal_type(**fields: object) -> dict[str, object]:
        captured.update(fields)
        return fields

    confidence = 0.9
    signal_policy._make_signal(
        fake_signal_type,
        confidence=confidence,
        kind="example",
    )

    assert captured["confidence"] == confidence
    assert captured["confidence_tier"] == str(quantize_confidence(confidence))
    assert captured["kind"] == "example"
