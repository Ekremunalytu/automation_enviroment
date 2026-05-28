"""W19-6 architecture gate: executor/flows/playwright/ hotspot modules
must stay under post-W19-5 LOC ceiling.

The 8 modules listed below all crossed 500 LOC by W19-X close-out and
absorbed further growth during the W19-4 + W19-5 producer-arm work in
``health/reconciliation.py``. Without a ratchet, growth in any of them
is invisible until a future bug forces re-investigation of a too-large
module.

The ceiling is current LOC * 1.05 (5% slack). Intentional growth must
explicitly bump the baseline in this file — a forcing-function PR
moment that makes the reviewer think about whether the new
responsibility could live in a sibling module instead of being
re-inlined into the hotspot.

Pattern follows W12-4
[`test_runner_main_under_loc_budget`](test_runner_main_loc_budget.py):
structural ratchet that fails before the readability hotspot worsens.
This gate is whole-file rather than function-level (those hotspots
have multiple top-level functions; the relevant signal is total file
size, which is what reviewers see first).

Baselines captured at W19-6 close (post W19-5 source change at
``executor/flows/playwright/health/reconciliation.py:347-365``;
W19-4 already-landed growth from ``7d44b0e`` folds into the
W19-5-tip baseline per the §17 plan).

To raise a baseline:
  - Investigate whether the growth is necessary (could the new
    responsibility live in a sibling module?).
  - If yes: bump the ceiling here in the same PR that adds the lines,
    with a short rationale comment.
  - If no: split the helper out instead. The split itself usually
    makes the test pass without any baseline change.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_HOTSPOT_BASE = REPO_ROOT / "executor" / "flows" / "playwright"

# Per-module ceilings = current LOC + ~5% slack. Updated as part of
# W19-6 close-out (`week19 -> main` PR). Sort key: relative path under
# ``executor/flows/playwright/``.
_HOTSPOT_LOC_CEILINGS: dict[str, int] = {
    "attribution/events.py": 527,  # base 502 (W19-X tip)
    "attribution/links.py": 643,  # base 613 (W19-X tip)
    "health/reconciliation.py": 597,  # base 569 (W19-5 +15 LOC from elif arm)
    "health/summary.py": 552,  # base 512 (W19-X tip) + W22-3 +30 LOC (count_target_process_events + count_target_output_events; mirrors count_target_activations W17-1 paterni)
    "monitor/runtime.py": 591,  # base 563 (W19-X tip)
    "monitor/scenario_accountant.py": 680,  # base 648 (W19-X tip)
    "monitor/types.py": 544,  # base 519 (W19-X tip)
    "stimulus/attempts.py": 569,  # base 542 (W19-X tip)
}


def _count_lines(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def test_executor_hotspot_modules_under_loc_ceiling() -> None:
    """All 8 ``executor/flows/playwright/`` hotspots must stay under their ceiling."""
    over_budget: list[str] = []
    for relative_path, ceiling in sorted(_HOTSPOT_LOC_CEILINGS.items()):
        module_path = _HOTSPOT_BASE / relative_path
        loc = _count_lines(module_path)
        if loc > ceiling:
            over_budget.append(
                f"  {relative_path}: {loc} LoC (ceiling {ceiling}, "
                f"over by {loc - ceiling})"
            )
    assert not over_budget, (
        "Hotspot module LoC ceiling breached:\n"
        + "\n".join(over_budget)
        + "\n\nEither split the new responsibility into a sibling module "
        "(preferred) or bump the per-module ceiling in "
        "`tests/architecture/test_executor_hotspot_loc_ratchet.py` with "
        "explicit rationale in the same PR. Do not raise the ceiling without "
        "thinking through whether the hotspot can be reshaped instead."
    )


def test_all_listed_hotspot_paths_exist() -> None:
    """Sanity guard: every key in ``_HOTSPOT_LOC_CEILINGS`` must point to a real file.

    If a future refactor renames or moves one of these modules without
    updating this test, ``test_executor_hotspot_modules_under_loc_ceiling``
    would silently pass with 0 LoC for the missing file. This guard
    catches that drift.
    """
    missing = [
        relative_path
        for relative_path in _HOTSPOT_LOC_CEILINGS
        if not (_HOTSPOT_BASE / relative_path).is_file()
    ]
    assert not missing, (
        f"Hotspot paths no longer exist: {missing}. "
        "Update `_HOTSPOT_LOC_CEILINGS` keys to match the rename/move."
    )
