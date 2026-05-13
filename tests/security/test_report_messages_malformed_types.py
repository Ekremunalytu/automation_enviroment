"""W14-2 (M11): build_report_messages malformed-type regression.

Closes [`FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types`].

``workflows/marketplace/analysis_reports.py::build_report_messages`` previously
called ``int(automation_health.get("target_activation_count", 0) or 0)``
without a type guard. ``automation_health`` is parsed from JSON the analyzed
extension writes inside the sandbox; a malicious extension can place a
non-numeric string, list, dict, ``NaN``, or out-of-range value where the
report builder expects an integer. ``int("not-an-int")`` raises ``ValueError``
and aborts the enclosing analysis job.

The fix (`workflows/marketplace/analysis_reports.py::_safe_int_coerce`)
defaults to ``0`` on every coercion failure and keeps the report builder
total. The parametrize matrix below pins both the happy-path numeric inputs
and the adversarial shapes the M11 audit called out.
"""

from __future__ import annotations

import pytest

from workflows.marketplace.analysis_reports import (
    _safe_int_coerce,
    build_report_messages,
)


# ---------------------------------------------------------------------------
# _safe_int_coerce matrix
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "vector_id,value,expected",
    [
        # Happy-path numerics
        ("int_zero", 0, 0),
        ("int_positive", 42, 42),
        ("int_negative", -3, -3),
        ("float_positive", 3.7, 3),
        ("float_negative", -2.4, -2),
        # Numeric strings
        ("str_integer", "5", 5),
        ("str_float", "5.7", 5),
        ("str_scientific", "1e2", 100),
        ("str_with_whitespace", "  9  ", 9),
        # Boolean (Python int subclass)
        ("bool_true", True, 1),
        ("bool_false", False, 0),
        # Adversarial shapes — all collapse to default=0
        ("none", None, 0),
        ("empty_string", "", 0),
        ("whitespace_only_string", "   ", 0),
        ("non_numeric_string", "not-an-int", 0),
        ("list", [1, 2, 3], 0),
        ("dict", {"k": "v"}, 0),
        ("nan", float("nan"), 0),
        ("infinity", float("inf"), 0),
        ("negative_infinity", float("-inf"), 0),
        ("dos_1e999_str", "1e999", 0),
    ],
)
def test_safe_int_coerce_matrix(vector_id: str, value: object, expected: int) -> None:
    """W14-2: every adversarial ``automation_health`` scalar lands at the
    safe default; happy-path numerics are preserved.
    """
    result = _safe_int_coerce(value, default=0)
    assert result == expected, (
        f"{vector_id}: _safe_int_coerce({value!r}, default=0) "
        f"returned {result!r}, expected {expected}"
    )


def test_safe_int_coerce_honors_non_zero_default() -> None:
    """W14-2: callers must be able to opt into a non-zero default for the
    failure path so a downstream metric can encode 'absent / malformed'
    distinctly from 'present-and-zero' if needed.
    """
    assert _safe_int_coerce("malformed", default=-1) == -1
    assert _safe_int_coerce(None, default=42) == 42


# ---------------------------------------------------------------------------
# build_report_messages malformed automation_health regression
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "vector_id,malformed_target_count",
    [
        ("string_non_numeric", "not-an-int"),
        ("nan", float("nan")),
        ("list", [1, 2, 3]),
        ("dict", {"nested": 1}),
        ("none", None),
        ("dos_1e999_str", "1e999"),
    ],
)
def test_build_report_messages_survives_malformed_target_activation_count(
    vector_id: str, malformed_target_count: object
) -> None:
    """W14-2: build_report_messages must NOT raise when
    ``automation_health.target_activation_count`` is adversarial.

    The fix coerces the value through ``_safe_int_coerce`` and falls back
    to 0 on failure; the function returns a tuple of two strings and the
    enclosing analysis job continues.
    """
    payload = {
        "automation_health": {
            "status": "ok",
            "trigger_requested": True,
            "trigger_loaded": True,
            "trigger_applied": True,
            "target_activation_count": malformed_target_count,
            "failed_scenarios": [],
            "skipped_scenarios": [],
        },
        "summary": {"scenarios_run": ["s1"]},
    }
    monitoring, finalize = build_report_messages("report.json", payload=payload)
    assert isinstance(monitoring, str) and monitoring
    assert isinstance(finalize, str) and finalize
    # The neutral count surfaces in the finalize message text
    assert "target activations=0" in finalize, (
        f"{vector_id}: malformed target_activation_count must collapse to 0; "
        f"finalize_message={finalize!r}"
    )


def test_build_report_messages_preserves_valid_target_count() -> None:
    """W14-2 regression guard: a valid integer target_activation_count must
    pass through unchanged — the M11 fix is a guard, not a normalizer.
    """
    payload = {
        "automation_health": {
            "status": "ok",
            "target_activation_count": 7,
            "failed_scenarios": [],
            "skipped_scenarios": [],
        },
        "summary": {"scenarios_run": []},
    }
    _monitoring, finalize = build_report_messages("report.json", payload=payload)
    assert "target activations=7" in finalize
