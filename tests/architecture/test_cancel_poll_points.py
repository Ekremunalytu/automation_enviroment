"""W13-3 architecture gate: cancel-poll points must precede every major phase.

Codex H4 (`reserve_job` released the single-active lock the moment a job
was cancelled, even though the worker thread still drove the shared
executor) is closed by a two-phase cancel — `running -> cancelling ->
cancelled` — paired with explicit `_raise_if_cancelled(cancel_check)`
points around every major phase boundary in
``workflows.marketplace.analysis_service.execute_analysis_request``.

Without those points cancellation would have to wait for the 5-second
heartbeat tick before propagating; a long-running `_reset_sandbox` or
`_install_extension` would keep burning executor time even after the
user pressed Stop. This gate pins the wiring as a structural invariant
so a future refactor cannot silently drop a poll point and reintroduce
the heartbeat-only gap.

The gate asserts that inside ``execute_analysis_request`` every call to
the five hot-zone helpers (``ensure_vsix_exists``, ``_reset_sandbox``,
``_install_extension``, ``_build_triggers``, ``_run_monitoring``) is
preceded — at the same statement-list level — by an
``_raise_if_cancelled(cancel_check)`` call. Adding a sixth phase
without a poll point fails the gate; renaming the helper requires
updating both the call site and this gate.

Defense-in-depth siblings:

- ``tests/platform/storage/test_analysis_jobs_lifecycle.py`` (W13-3
  CRUD regression: cancel transitions to ``cancelling`` not
  ``cancelled``; ``finalize_cancelled_analysis_job`` rejects any other
  source state).
- ``tests/workflows/marketplace/test_router.py`` (W13-3 router
  regression: cancel endpoint returns 200 with a ``cancelling``
  snapshot; status endpoint surfaces the drain state for polling
  clients).
- ``tests/architecture/test_job_state_invariants.py`` (W13-3 schema
  invariant: ``_TERMINAL_JOB_STATUSES`` excludes ``cancelling``;
  ``ACTIVE_ANALYSIS_JOB_STATUSES`` includes it; partial unique index
  WHERE clause matches).
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_SERVICE_PATH = REPO_ROOT / "workflows" / "marketplace" / "analysis_service.py"

# Order matters only for human readability — the gate accepts any order
# as long as each helper call is preceded by a cancel poll at the same
# statement-list level.
HOT_ZONE_HELPERS: tuple[str, ...] = (
    "ensure_vsix_exists",
    "_reset_sandbox",
    "_install_extension",
    "_build_triggers",
    "_run_monitoring",
)
POLL_HELPER = "_raise_if_cancelled"


def _find_function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
        f"function {name!r} missing — W13-3 wiring removed?"
    )


def _statement_call_name(stmt: ast.stmt) -> str | None:
    """Return the callable name of a bare- or assigned-call statement.

    Captures the two shapes used in ``execute_analysis_request``:

    - ``_raise_if_cancelled(cancel_check)`` (bare Expr/Call)
    - ``install_output = _install_extension(...)`` (Assign(Call))

    Anything else (assignments without a Call rhs, ifs, etc.) returns
    ``None`` and is treated as a non-poll, non-hot-zone statement.
    """
    call: ast.Call | None = None
    if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)) or (
        isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call)
    ):
        call = stmt.value
    if call is None:
        return None
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def test_every_major_phase_is_preceded_by_a_cancel_poll() -> None:
    """W13-3: every hot-zone helper must run after a fresh cancel-poll.

    The gate walks the top-level body of ``execute_analysis_request``,
    pairs each ``HOT_ZONE_HELPERS`` call with its immediately preceding
    poll, and refuses to accept a sequence where the poll is missing.
    """
    source = ANALYSIS_SERVICE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func = _find_function(tree, "execute_analysis_request")

    pending_phases = list(HOT_ZONE_HELPERS)
    last_poll_index: int | None = None
    unmatched_polls: list[int] = []

    for index, stmt in enumerate(func.body):
        name = _statement_call_name(stmt)
        if name == POLL_HELPER:
            last_poll_index = index
            continue
        if name in pending_phases:
            assert last_poll_index is not None, (
                f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
                f"call to {name!r} at body index {index} is not preceded "
                f"by a {POLL_HELPER}(cancel_check) call — Codex H4 cancel-"
                f"poll point regressed."
            )
            assert last_poll_index < index, (
                f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
                f"poll for {name!r} not earlier in the body (last_poll="
                f"{last_poll_index}, phase={index})."
            )
            unmatched_polls.append(last_poll_index)
            pending_phases.remove(name)
            # A poll only "covers" the next phase — force a fresh poll
            # before the subsequent hot zone.
            last_poll_index = None

    assert not pending_phases, (
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
        f"hot-zone helper call(s) missing from execute_analysis_request "
        f"body: {pending_phases!r}. If a phase moved off the helper, "
        f"update HOT_ZONE_HELPERS so the gate keeps catching regressions."
    )
    assert len(unmatched_polls) == len(HOT_ZONE_HELPERS), (
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
        f"expected {len(HOT_ZONE_HELPERS)} cancel-poll points, found "
        f"{len(unmatched_polls)} preceding a hot-zone call."
    )


def test_raise_if_cancelled_helper_is_publicly_named() -> None:
    """W13-3: the helper has to be importable + greppable so this gate
    can pin it. A rename without updating the gate would silently drop
    the assertion — assert the helper's existence as a top-level export
    of analysis_execution.
    """
    execution_path = REPO_ROOT / "workflows" / "marketplace" / "analysis_execution.py"
    source = execution_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    found = any(
        isinstance(node, ast.FunctionDef) and node.name == "raise_if_cancelled"
        for node in ast.walk(tree)
    )
    assert found, (
        f"{execution_path.relative_to(REPO_ROOT)}: "
        "raise_if_cancelled helper missing — W13-3 cancel-poll wiring lost "
        "its public name; this gate cannot pin the import either."
    )

    all_node: ast.Assign | None = None
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
        ):
            all_node = node
            break
    assert all_node is not None, (
        f"{execution_path.relative_to(REPO_ROOT)}: __all__ missing."
    )
    assert isinstance(all_node.value, ast.List)
    exports = {
        elt.value
        for elt in all_node.value.elts
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
    }
    assert "raise_if_cancelled" in exports, (
        f"{execution_path.relative_to(REPO_ROOT)}: __all__ must export "
        "raise_if_cancelled so analysis_service can import it without "
        "name-mangling cycles."
    )
