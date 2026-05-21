"""W13-12 architecture gate: production setup_monitor must mandate fail-closed handshake.

W13-1 closed Codex H6 by routing harness completion-trace verification
through ``_verify_harness_marker_signature`` whenever ``expected_nonce``
is non-empty. The empty-nonce branch was retained for unit-test
construction (pre-W13-1 ``ActivationReport`` fixtures with no
orchestration handshake).

W13-11 (Codex F1) closed the install-window race that allowed a
same-UID target to read the secret file before the executor consumed
it. But ``load_harness_python_secret`` still returns ``""`` on any
read failure (``FileNotFoundError``, ``OSError``, bind-mount race,
eager-consume miss). When that happens the production path silently
falls back to the legacy phase-only check.

W13-12 (Codex F2) introduces an explicit ``harness_handshake_required``
flag on the internal monitor ``ActivationReport`` dataclass.
``setup_monitor`` stamps it ``True`` on every production launch so the
empty-nonce branch fails closed (no verification) rather than
fall-open phase-only. This gate pins three AST-level invariants so a
future refactor cannot silently re-open the gap:

1. ``setup_monitor`` (in ``entrypoint/dispatch.py``) assigns
   ``True`` to ``mon.report.harness_handshake_required`` (or
   equivalent attribute path).
2. ``reconcile_event_attempts`` (in ``health/reconciliation.py``)
   reads ``harness_handshake_required`` off the report via
   ``getattr(report, "harness_handshake_required", ...)``.
3. ``reconcile_event_attempts`` threads the flag into
   ``_attempt_has_harness_completion_trace`` as a keyword argument
   ``handshake_required=...``.

Together they ensure that a missing eager-consume secret + production
path → fail-closed at reconciliation time. The unit-test phase-only
branch is preserved only for fixtures that leave the field at its
``False`` default.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RECONCILIATION_PATH = (
    REPO_ROOT / "executor" / "flows" / "playwright" / "health" / "reconciliation.py"
)
DISPATCH_PATH = (
    REPO_ROOT / "executor" / "flows" / "playwright" / "entrypoint" / "dispatch.py"
)


def _find_function(tree: ast.AST, name: str, source_path: Path) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(
        f"{source_path.relative_to(REPO_ROOT)}: "
        f"function {name!r} missing — W13-12 wiring removed?"
    )


def test_setup_monitor_stamps_harness_handshake_required_true() -> None:
    """``setup_monitor`` must assign ``True`` to ``harness_handshake_required``.

    If a future refactor drops the assignment or flips the literal to
    ``False``, the report field stays at its dataclass default
    (``False``) → ``_attempt_has_harness_completion_trace`` falls
    through to the legacy phase-only check when ``expected_nonce`` is
    empty → Codex F2 is silently re-opened with no other gate failing.
    """
    tree = ast.parse(DISPATCH_PATH.read_text(encoding="utf-8"))
    func = _find_function(tree, "setup_monitor", DISPATCH_PATH)

    stamps_true = False
    for node in ast.walk(func):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and target.attr == "harness_handshake_required"
                and isinstance(node.value, ast.Constant)
                and node.value.value is True
            ):
                stamps_true = True
                break
        if stamps_true:
            break

    assert stamps_true, (
        f"{DISPATCH_PATH.relative_to(REPO_ROOT)}: "
        "setup_monitor must assign ``True`` to "
        "``mon.report.harness_handshake_required`` so reconciliation "
        "fails closed when the eager-consumed secret is unavailable. "
        "Without this stamp the field defaults to False and the empty-"
        "nonce path falls back to legacy phase-only verification, "
        "re-opening Codex F2."
    )


def test_reconcile_event_attempts_reads_harness_handshake_required_from_report() -> (
    None
):
    """``reconcile_event_attempts`` must read the flag via ``getattr(report, ...)``.

    A direct attribute access (``report.harness_handshake_required``)
    would raise ``AttributeError`` on legacy reports that pre-date
    W13-12 (replayed from archive, for example). The ``getattr``
    fallback to ``False`` keeps replays working while still enforcing
    fail-closed for production paths that stamp the field.
    """
    tree = ast.parse(RECONCILIATION_PATH.read_text(encoding="utf-8"))
    func = _find_function(tree, "reconcile_event_attempts", RECONCILIATION_PATH)

    reads_via_getattr = False
    for node in ast.walk(func):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "harness_handshake_required"
        ):
            reads_via_getattr = True
            break

    assert reads_via_getattr, (
        f"{RECONCILIATION_PATH.relative_to(REPO_ROOT)}: "
        "reconcile_event_attempts must read ``harness_handshake_required`` "
        'from the report via ``getattr(report, "harness_handshake_required", '
        "False)``. Without this read the fail-closed branch in "
        "``_attempt_has_harness_completion_trace`` is never reached and "
        "Codex F2 is silently re-opened."
    )


def test_reconcile_event_attempts_threads_handshake_required_kwarg() -> None:
    """The flag must be passed into the helper as ``handshake_required=...``.

    Reading the flag without threading it leaves the helper at its
    default ``handshake_required=False`` → fail-closed branch never
    fires. The kwarg keyword is the structural contract between caller
    and helper.
    """
    tree = ast.parse(RECONCILIATION_PATH.read_text(encoding="utf-8"))
    func = _find_function(tree, "reconcile_event_attempts", RECONCILIATION_PATH)

    threads_kwarg = False
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        if not (
            isinstance(node.func, ast.Name)
            and node.func.id == "_attempt_has_harness_completion_trace"
        ):
            continue
        for keyword in node.keywords:
            if keyword.arg == "handshake_required":
                threads_kwarg = True
                break
        if threads_kwarg:
            break

    assert threads_kwarg, (
        f"{RECONCILIATION_PATH.relative_to(REPO_ROOT)}: "
        "reconcile_event_attempts must thread the report's "
        "``harness_handshake_required`` value into "
        "``_attempt_has_harness_completion_trace`` as the "
        "``handshake_required`` keyword argument. Without it the helper "
        "defaults to False and the fail-closed branch is unreachable."
    )
