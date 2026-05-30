"""Framework-agnostic typosquat matching primitives (ES-3a, ADR 0016).

Pure-stdlib helpers shared by two call sites that must NOT share a heavier
dependency:

* the dynamic detection rule
  ``packages.analysis_engine.rules.a3_typosquat`` (runs on the host inside the
  full engine), and
* the in-house static rule ``static_runtime.rules.s2_typosquat_static`` (runs
  inside the hardened ``automation_static_analyzer`` image, which copies only
  ``packages/analysis_contracts/`` + ``static_runtime/`` and deliberately NOT
  ``packages/analysis_engine/`` — see ``static_runtime/__init__.py``).

Living under ``packages.analysis_contracts`` keeps a single copy of both the
matcher and the ``popular_extensions.txt`` allowlist in an in-image,
framework-agnostic location (the same reason ``redact_secrets`` lives in
``packages/analysis_contracts/evidence.py``). Imports are confined to the
standard library so importing this leaf never drags the dynamic engine in.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

# The allowlist moved here from packages/analysis_engine/allowlists/ at ES-3a so
# the hardened static image (which carries analysis_contracts/, not
# analysis_engine/) can read it. The dynamic a3 rule reads the same file via
# this module, so there is exactly one curated copy.
_POPULAR_EXTENSION_PATH = (
    Path(__file__).resolve().parent / "data" / "popular_extensions.txt"
)

# Maximum Levenshtein distance at which an identifier is treated as a typosquat
# of a popular extension. Distance 0 (exact match) is the legitimate extension.
MAX_TYPOSQUAT_DISTANCE = 2


@lru_cache(maxsize=1)
def popular_extensions() -> frozenset[str]:
    """Return the curated set of popular marketplace extension identifiers."""
    lines = _POPULAR_EXTENSION_PATH.read_text(encoding="utf-8").splitlines()
    values = {line.strip().lower() for line in lines if line.strip()}
    return frozenset(values)


def levenshtein(left: str, right: str) -> int:
    """Edit distance between two strings (iterative two-row DP)."""
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            substitution_cost = 0 if left_char == right_char else 1
            current.append(
                min(
                    current[j - 1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + substitution_cost,
                )
            )
        previous = current
    return previous[-1]


def nearest_popular_match(identifier: str) -> tuple[str, int] | None:
    """Return the closest popular extension within the typosquat bound.

    Returns ``None`` when ``identifier`` is itself a popular extension (distance
    0) or when nothing falls within ``MAX_TYPOSQUAT_DISTANCE``.
    """
    best: tuple[str, int] | None = None
    for candidate in popular_extensions():
        distance = levenshtein(identifier, candidate)
        if distance == 0:
            return None
        if distance > MAX_TYPOSQUAT_DISTANCE:
            continue
        if best is None or distance < best[1]:
            best = (candidate, distance)
    return best


__all__ = [
    "MAX_TYPOSQUAT_DISTANCE",
    "levenshtein",
    "nearest_popular_match",
    "popular_extensions",
]
