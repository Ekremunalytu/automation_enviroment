"""Unit tests for the shared typosquat matcher (ES-3a/ES-4, ADR 0016).

``packages.analysis_contracts.typosquat_match`` is the single stdlib-only leaf
imported by both the dynamic ``a3_typosquat`` rule and the static
``s2_typosquat_static`` rule, so its edit-distance core and its
adversarial-input length-band bound are exercised here directly rather than only
through either rule. The allowlist is monkeypatched to keep distance assertions
independent of the curated ``popular_extensions.txt`` contents.
"""

from __future__ import annotations

import pytest

from packages.analysis_contracts import typosquat_match
from packages.analysis_contracts.typosquat_match import (
    MAX_TYPOSQUAT_DISTANCE,
    levenshtein,
    nearest_popular_match,
    popular_extensions,
)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("abc", "abc", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("kitten", "sitting", 3),
        ("flaw", "lawn", 2),
        ("ab", "ba", 2),
    ],
)
def test_levenshtein_known_distances(left: str, right: str, expected: int) -> None:
    assert levenshtein(left, right) == expected


def test_levenshtein_is_symmetric() -> None:
    assert levenshtein("kitten", "sitting") == levenshtein("sitting", "kitten")


def test_nearest_match_is_none_for_exact_popular_extension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Distance 0 is the legitimate extension, not a typosquat.
    monkeypatch.setattr(
        typosquat_match, "popular_extensions", lambda: frozenset({"alpha"})
    )
    assert nearest_popular_match("alpha") is None


def test_nearest_match_returns_closest_within_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        typosquat_match, "popular_extensions", lambda: frozenset({"alpha"})
    )
    # "alpha" -> "alpla": one substitution (h->l) == distance 1.
    assert nearest_popular_match("alpla") == ("alpha", 1)


def test_nearest_match_is_none_beyond_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        typosquat_match, "popular_extensions", lambda: frozenset({"abcde"})
    )
    # "abcde" -> "abxyz": three substitutions == distance 3 > MAX (2).
    assert MAX_TYPOSQUAT_DISTANCE == 2
    assert nearest_popular_match("abxyz") is None


def test_nearest_match_picks_strictly_closest_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Both candidates are within the bound; the distance-1 one must win
    # regardless of (unordered) frozenset iteration order.
    monkeypatch.setattr(
        typosquat_match, "popular_extensions", lambda: frozenset({"abcd", "abxy"})
    )
    # "abce": distance 1 to "abcd", distance 2 to "abxy".
    assert nearest_popular_match("abce") == ("abcd", 1)


def test_length_band_skips_dp_for_pathologically_long_identifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Adversarial input: a very long identifier whose length differs from every
    # candidate by more than MAX_TYPOSQUAT_DISTANCE must be rejected in O(1)
    # *before* paying for the O(n*m) edit-distance DP. Proven by making
    # levenshtein explode if it is ever reached.
    monkeypatch.setattr(
        typosquat_match, "popular_extensions", lambda: frozenset({"abcd"})
    )

    def _boom(*_args: object, **_kwargs: object) -> int:
        raise AssertionError("levenshtein must not run for out-of-band lengths")

    monkeypatch.setattr(typosquat_match, "levenshtein", _boom)
    assert nearest_popular_match("a" * 50) is None


def test_curated_allowlist_loads_lowercased_and_nonempty() -> None:
    # Guards the data-file load path (popular_extensions.txt) the rules depend on.
    extensions = popular_extensions()
    assert extensions
    assert all(value == value.lower() for value in extensions)
