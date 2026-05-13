"""W14-4 architecture gate: ``complete_analysis_job`` and
``fail_analysis_job`` must acquire ``with_for_update()`` and guard
against the terminal-status frozenset before mutating, mirroring the
W13-3 ``cancel_analysis_job`` / ``finalize_cancelled_analysis_job``
lock discipline.

Closes the CRITICAL race window documented in W13-4.4 (`[FOLLOWUP
analysis-jobs-race]`). Pre-W14-4 both functions read the row via a
plain ``SELECT`` and the concurrent loser silently overwrote the
winner's terminal write; the post-fix lock + terminal guard at
``lifecycle.py:260`` (fail) and ``lifecycle.py:319`` (complete) closes
this surface. The behavioral evidence lives in
``tests/platform/storage/test_analysis_jobs_concurrency.py``
(``test_cancel_vs_complete_…``, ``test_concurrent_complete_vs_fail_…``,
``test_double_complete_…``, ``test_double_fail_…``); this gate keeps a
future refactor from regressing the lock pattern at the AST level.

Pattern modeled on the W14-2
``tests/architecture/test_output_signal_ts_guard.py`` body-invariant
gate and the W13-6
``tests/architecture/test_arguments_preview_redaction.py`` mirror.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LIFECYCLE_MODULE = (
    REPO_ROOT
    / "appcore"
    / "storage"
    / "crud_ops"
    / "analysis_jobs"
    / "lifecycle.py"
)
TERMINAL_STATUSES_NAME = "_TERMINAL_JOB_STATUSES"
LOCK_METHOD = "with_for_update"
GATED_FUNCTIONS = ("complete_analysis_job", "fail_analysis_job")


def _function_body(module_tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(module_tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(
        f"{name}() not found in {LIFECYCLE_MODULE.relative_to(REPO_ROOT)}"
    )


def _has_with_for_update_call(func: ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == LOCK_METHOD
        ):
            return True
    return False


def _has_terminal_status_guard(func: ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        # match `... in _TERMINAL_JOB_STATUSES`
        if isinstance(node, ast.Compare):
            for op, comparator in zip(node.ops, node.comparators, strict=True):
                if isinstance(op, ast.In) and (
                    isinstance(comparator, ast.Name)
                    and comparator.id == TERMINAL_STATUSES_NAME
                ):
                    return True
    return False


def test_complete_and_fail_acquire_row_lock() -> None:
    """Both terminal writers select with ``with_for_update()`` before any
    state mutation, matching the W13-3 cancel / finalize discipline.
    """
    tree = ast.parse(LIFECYCLE_MODULE.read_text(encoding="utf-8"))
    missing = [
        name
        for name in GATED_FUNCTIONS
        if not _has_with_for_update_call(_function_body(tree, name))
    ]
    assert not missing, (
        f"{', '.join(missing)} in "
        f"{LIFECYCLE_MODULE.relative_to(REPO_ROOT)} must acquire a row-level "
        f"exclusive lock via select(...).{LOCK_METHOD}() before the status "
        "check (W14-4 [FOLLOWUP analysis-jobs-race] invariant; W13-3 cancel "
        "lock discipline mirror)."
    )


def test_complete_and_fail_gate_against_terminal_statuses() -> None:
    """Both terminal writers reject when the current row status is already
    in ``_TERMINAL_JOB_STATUSES`` — the second-writer terminal-overwrite
    race is closed under the lock.
    """
    tree = ast.parse(LIFECYCLE_MODULE.read_text(encoding="utf-8"))
    missing = [
        name
        for name in GATED_FUNCTIONS
        if not _has_terminal_status_guard(_function_body(tree, name))
    ]
    assert not missing, (
        f"{', '.join(missing)} in "
        f"{LIFECYCLE_MODULE.relative_to(REPO_ROOT)} must contain a "
        f"`status in {TERMINAL_STATUSES_NAME}` guard so already-terminal rows "
        "raise JobNotCancellableError instead of being silently overwritten "
        "(W14-4 [FOLLOWUP analysis-jobs-race] invariant)."
    )
