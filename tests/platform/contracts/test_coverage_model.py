"""W10-4 contract tests: CoverageSummary typed projection."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.analysis_contracts import CoverageSummary


def test_default_construction_is_empty() -> None:
    summary = CoverageSummary()
    assert summary.covered == 0
    assert summary.partial == 0
    assert summary.missing == 0
    assert summary.attempted == 0
    assert summary.verified == 0
    for field in (
        "covered_capabilities",
        "partial_capabilities",
        "missing_capabilities",
        "attempted_capabilities",
        "verified_capabilities",
    ):
        assert getattr(summary, field) == []


def test_planner_only_subset_validates() -> None:
    """The planner emits 6 fields; the executor's reconcile step adds
    attempted/verified counts. Both shapes must validate."""
    planner_only = {
        "covered": 2,
        "partial": 1,
        "missing": 0,
        "covered_capabilities": ["commands", "window_ui"],
        "partial_capabilities": ["debug"],
        "missing_capabilities": [],
    }
    summary = CoverageSummary.model_validate(planner_only)
    assert summary.covered == 2
    assert summary.attempted == 0
    assert summary.attempted_capabilities == []


def test_full_executor_shape_round_trips() -> None:
    raw = {
        "covered": 7,
        "partial": 5,
        "missing": 6,
        "covered_capabilities": ["commands", "window_ui"],
        "partial_capabilities": ["search_views"],
        "missing_capabilities": ["scm"],
        "attempted": 4,
        "verified": 2,
        "attempted_capabilities": ["commands", "debug"],
        "verified_capabilities": ["commands"],
    }
    summary = CoverageSummary.model_validate(raw)
    assert summary.model_dump() == raw


def test_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        CoverageSummary.model_validate({"covered": 1, "extra_field": "no"})


def test_negative_counts_accepted_but_capabilities_must_be_string_list() -> None:
    """Soft contract: counts are int (no negativity check at this layer);
    capability lists must contain strings only."""
    summary = CoverageSummary.model_validate({"covered": 0})
    assert summary.covered == 0
    with pytest.raises(ValidationError):
        CoverageSummary.model_validate(
            {"covered": 1, "covered_capabilities": [{"not": "a string"}]}
        )
