"""W12-4 architecture gate: ``runner.main`` body must stay under the
≤200 LoC readability budget.

After W12-4 the dispatch logic moved to ``entrypoint/dispatch.py`` and
``runner.main`` shrank from 324 to ~100 LoC. This gate is a regression
ratchet: any future addition that pushes ``main()`` back over budget
must split a new helper into ``dispatch.py`` (or a sibling module)
rather than re-inlining behavior into the orchestrator.

Pattern follows W12-1 ``test_executor_playwright_flat_file_count_limit``:
a structural ratchet that fails before the readability hotspot
re-emerges.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = (
    REPO_ROOT / "executor" / "flows" / "playwright" / "entrypoint" / "runner.py"
)

# W12-4 budget. Lower is better — tighten the ratchet (toward the actual
# observed value) when ``main()`` shrinks further; never raise without an
# explicit W-window decision recorded in REFACTOR_STATUS.md.
MAIN_LOC_LIMIT = 200


def _find_function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function {name!r} not found in {RUNNER_PATH}")


def test_runner_main_under_loc_budget() -> None:
    """``runner.main`` must stay within ``MAIN_LOC_LIMIT`` lines."""
    source = RUNNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    main_fn = _find_function(tree, "main")
    span = main_fn.end_lineno - main_fn.lineno + 1
    assert span <= MAIN_LOC_LIMIT, (
        f"runner.main is {span} LoC (limit {MAIN_LOC_LIMIT}). "
        "Move the new logic into entrypoint/dispatch.py (or a sibling) "
        "instead of re-inlining behavior into the orchestrator."
    )


def test_runner_main_dispatch_helpers_remain_imported() -> None:
    """Sanity guard: ``runner.py`` still imports the dispatch helpers.

    If a future refactor inlines a helper back into ``runner.main`` and
    drops the dispatch import, ``main()`` would silently grow without
    triggering the LoC test if other compensations are made. This guard
    pins the contract that dispatch.py owns the heavy lifting.
    """
    source = RUNNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    expected = {
        "PageRef",
        "apply_extra_triggers_if_needed",
        "dispatch_execution",
        "finalize_monitor_report",
        "setup_monitor",
        "summarize_skipped_scenarios_if_needed",
    }
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "dispatch":
            imported.update(alias.name for alias in node.names)
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.endswith(".dispatch")
        ):
            imported.update(alias.name for alias in node.names)
    missing = expected - imported
    assert not missing, (
        f"runner.py is missing imports from .dispatch: {sorted(missing)}. "
        "If a helper was renamed, update this gate together with the rename."
    )
