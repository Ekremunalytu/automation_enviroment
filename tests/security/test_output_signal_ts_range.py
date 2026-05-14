"""W14-2 (M4 + M7): output signal ``ts`` range/finite validation regression.

Closes [`FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation`].

Extension-controlled ``ts`` fields are consumed by both
``parse_output_signal_events()`` (harness-marker JSON source) and
``read_output_channel_logs()`` (file-backed VS Code 1.105+ source) at
``executor/flows/playwright/signals/output.py``; both feed
``_format_epoch_ms`` which now sanitizes the epoch through
``_coerce_safe_epoch_s`` before invoking ``datetime.fromtimestamp()``.

Without the guard a malicious VSIX writing ``ts: 1e999`` (becomes
``float("inf")``), ``NaN``, or values outside the platform ``time_t``
ceiling would raise ``OverflowError`` / ``OSError`` / ``ValueError`` and
abort the final report build.

The parametrize matrix covers the same regression shapes the W13-6
pattern uses for redaction regression coverage:

* numeric inside the safe window (1970-01-01 ≤ ts ≤ 3000-01-01) → unchanged
* finite outside the window → coerced to epoch 0
* ``float("inf")`` / ``float("-inf")`` → coerced to epoch 0
* ``float("nan")`` → coerced to epoch 0
* negative finite → coerced to epoch 0

Each row asserts that ``_coerce_safe_epoch_s`` returns the expected
canonical value AND that ``_format_epoch_ms`` (the actual public-facing
call) returns a parseable ISO timestamp instead of raising.
"""

from __future__ import annotations

import math

import pytest

from executor.flows.playwright.signals.output import (
    _MAX_SAFE_EPOCH_S,
    _coerce_safe_epoch_s,
    _format_epoch_ms,
)


# ---------------------------------------------------------------------------
# Coercion matrix: (vector_id, input_epoch_s, expected_after_coerce)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "vector_id,input_epoch_s,expected",
    [
        ("safe_now", 1700000000.0, 1700000000.0),
        ("safe_unix_epoch", 0.0, 0.0),
        ("safe_max_window", _MAX_SAFE_EPOCH_S, _MAX_SAFE_EPOCH_S),
        ("overflow_above_max", _MAX_SAFE_EPOCH_S + 1.0, 0.0),
        ("negative_finite", -1.0, 0.0),
        ("positive_infinity", float("inf"), 0.0),
        ("negative_infinity", float("-inf"), 0.0),
        ("nan", float("nan"), 0.0),
        ("dos_1e999_promoted_to_inf", float("1e999"), 0.0),
    ],
)
def test_coerce_safe_epoch_s(
    vector_id: str, input_epoch_s: float, expected: float
) -> None:
    """W14-2: every extension-controlled epoch lands inside the safe window."""
    result = _coerce_safe_epoch_s(input_epoch_s)
    assert result == expected, (
        f"{vector_id}: _coerce_safe_epoch_s({input_epoch_s!r}) "
        f"returned {result!r}, expected {expected!r}"
    )


@pytest.mark.parametrize(
    "vector_id,input_ms",
    [
        ("safe_window_ms", 1_700_000_000_000.0),
        ("overflow_inf_ms", float("inf")),
        ("dos_1e999_ms", 1e999),
        ("nan_ms", float("nan")),
        ("negative_ms", -5000.0),
        ("zero_ms", 0.0),
    ],
)
def test_format_epoch_ms_never_raises_on_adversarial_ts(
    vector_id: str, input_ms: float
) -> None:
    """W14-2: ``_format_epoch_ms`` must produce a valid ISO timestamp for
    every adversarial ``ts`` shape; ``datetime.fromtimestamp`` must not
    raise.

    Together with the coercion matrix above this pins the M4-M7 invariant
    end-to-end: input → coerce → fromtimestamp → ISO string. No exception
    surface escapes ``_format_epoch_ms``.
    """
    timestamp, rel_time_s = _format_epoch_ms(input_ms, monitoring_start=0.0)
    assert isinstance(timestamp, str)
    assert timestamp  # non-empty
    # `T` separates date and time in datetime.isoformat output
    assert "T" in timestamp, f"{vector_id}: malformed timestamp {timestamp!r}"
    # rel_time_s is None when monitoring_start is 0 by contract
    assert rel_time_s is None


def test_format_epoch_ms_preserves_normal_ts_alignment() -> None:
    """W14-2 regression guard: the sanitizer must NOT shift normal in-range
    timestamps. A safe ts of 1.7e12 ms (around 2023-11-14 in local time) must
    still appear as a 2023-shaped ISO string — the M4-M7 fix is a guard, not
    a normalizer.
    """
    timestamp, _rel = _format_epoch_ms(1_700_000_000_000.0, monitoring_start=0.0)
    assert timestamp.startswith("2023-"), (
        f"Normal ts must not be coerced; got {timestamp!r}"
    )


def test_coerce_safe_epoch_s_is_idempotent_on_safe_values() -> None:
    """W14-2: applying the coercion twice on a safe value must be a no-op."""
    safe = 1_700_000_000.0
    once = _coerce_safe_epoch_s(safe)
    twice = _coerce_safe_epoch_s(once)
    assert once == twice == safe


def test_coerce_safe_epoch_s_safe_boundary_inclusive() -> None:
    """W14-2: the lower bound (0.0) and upper bound (_MAX_SAFE_EPOCH_S) must
    both be accepted as-is — the window is closed, not half-open.
    """
    assert _coerce_safe_epoch_s(0.0) == 0.0
    assert _coerce_safe_epoch_s(_MAX_SAFE_EPOCH_S) == _MAX_SAFE_EPOCH_S
    # Sanity: math.isfinite stays True on boundary values
    assert math.isfinite(_MAX_SAFE_EPOCH_S)
