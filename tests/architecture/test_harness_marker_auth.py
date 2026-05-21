"""W13-1 architecture gate: harness completion-trace check must verify the HMAC nonce.

Codex H6 (`automation_trace` could be forged by a same-UID target
extension writing `[extrace-harness] {phase:"complete"}` to stdout) is
closed by routing every harness completion-trace check through
``_verify_harness_marker_signature``. This gate pins the wiring as a
structural invariant so a future refactor cannot reintroduce a
phase-only acceptance path on the production side.

The gate asserts three AST-level facts:

1. ``_attempt_has_harness_completion_trace`` (in ``reconciliation.py``)
   calls ``_verify_harness_marker_signature`` somewhere in its body.
2. ``reconcile_event_attempts`` (in ``reconciliation.py``) reads
   ``expected_harness_nonce`` off the report (via
   ``getattr(report, "expected_harness_nonce", ...)``) and threads it
   into ``_attempt_has_harness_completion_trace``.
3. ``setup_monitor`` (in ``entrypoint/dispatch.py``) calls
   ``load_harness_python_secret`` and stamps the result onto
   ``report.expected_harness_nonce``. Without this stamp the report
   field stays empty default and reconciliation silently falls back
   to the legacy phase-only check, re-opening Codex H6 with no other
   gate failing.

Together they ensure no ``phase=="complete"`` trace can satisfy
``automation_trace`` without a verified signature when the
orchestration handshake is in place.

Defense-in-depth siblings:

- ``tests/executor/test_playwright_health_reconciliation.py``
  (W13-1 RED -> GREEN: forged-marker rejection regression).
- ``executor/container/launch_vscode.sh`` (per-launch secret
  generation; harness-side consume in
  ``executor/flows/harness_extension/extension.js``).
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RECONCILIATION_PATH = (
    REPO_ROOT / "executor" / "flows" / "playwright" / "health" / "reconciliation.py"
)
# W16-4: ``_attempt_has_harness_completion_trace`` moved to handshake.py
# alongside the W13-1 security primitives in security.py. The gate paths
# below are re-targeted; ``RECONCILIATION_PATH`` is kept for the
# ``reconcile_event_attempts`` invariant that still lives there.
HANDSHAKE_PATH = (
    REPO_ROOT / "executor" / "flows" / "playwright" / "health" / "handshake.py"
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
        f"function {name!r} missing — W13-1 wiring removed?"
    )


def _function_calls(func: ast.FunctionDef) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            names.add(node.func.id)
    return names


def test_attempt_has_harness_completion_trace_calls_verifier() -> None:
    """W13-1: phase-only acceptance was the spoofing surface; signature is mandatory.

    W16-4 re-target: ``_attempt_has_harness_completion_trace`` lives in
    ``handshake.py`` alongside the W13-12 fail-closed dispatch logic;
    ``_verify_harness_marker_signature`` lives in ``security.py`` and is
    imported into handshake.py. The AST walk now parses handshake.py and
    asserts the verifier call survives the import boundary.
    """
    tree = ast.parse(HANDSHAKE_PATH.read_text(encoding="utf-8"))
    func = _find_function(tree, "_attempt_has_harness_completion_trace", HANDSHAKE_PATH)
    calls = _function_calls(func)
    assert "_verify_harness_marker_signature" in calls, (
        f"{HANDSHAKE_PATH.relative_to(REPO_ROOT)}: "
        "_attempt_has_harness_completion_trace must call "
        "_verify_harness_marker_signature so harness completion traces "
        "are authenticated against the per-launch HMAC nonce. "
        "A bare phase==complete check reopens Codex H6."
    )


def test_reconcile_event_attempts_threads_expected_harness_nonce() -> None:
    """W13-1: the secret stamped onto the report by setup_monitor must reach the verifier."""
    tree = ast.parse(RECONCILIATION_PATH.read_text(encoding="utf-8"))
    func = _find_function(tree, "reconcile_event_attempts", RECONCILIATION_PATH)

    reads_field = False
    for node in ast.walk(func):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "expected_harness_nonce"
        ):
            reads_field = True
            break

    assert reads_field, (
        f"{RECONCILIATION_PATH.relative_to(REPO_ROOT)}: "
        "reconcile_event_attempts must read ``expected_harness_nonce`` from "
        "the report (via getattr to keep unit-test ActivationReport "
        "construction without the field working) and thread it into "
        "_attempt_has_harness_completion_trace."
    )

    threaded = False
    for node in ast.walk(func):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_attempt_has_harness_completion_trace"
        ):
            arg_names: list[str] = []
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    arg_names.append(arg.id)
            kw_values: list[str] = []
            for kw in node.keywords:
                if isinstance(kw.value, ast.Name):
                    kw_values.append(kw.value.id)
            if "expected_harness_nonce" in arg_names + kw_values:
                threaded = True
                break

    assert threaded, (
        f"{RECONCILIATION_PATH.relative_to(REPO_ROOT)}: "
        "the ``expected_harness_nonce`` local read off the report must be "
        "passed into _attempt_has_harness_completion_trace as either a "
        "positional or keyword argument so the verifier sees the secret."
    )


def test_setup_monitor_loads_and_stamps_harness_python_secret() -> None:
    """W13-1: dispatch.setup_monitor must load the per-launch secret and stamp it.

    The reconciliation-side gates above ensure the verifier is invoked *iff*
    ``report.expected_harness_nonce`` is non-empty. The orchestration side
    (``setup_monitor``) is what actually populates that field by calling
    ``load_harness_python_secret()`` (which reads + unlinks the file
    ``launch_vscode.sh`` wrote) and assigning to ``report.expected_harness_nonce``.

    If a future refactor drops either the call or the assignment, the
    report's ``expected_harness_nonce`` stays at its dataclass default
    (empty string) → ``_attempt_has_harness_completion_trace`` short-
    circuits to the legacy phase-only check → Codex H6 is silently
    re-opened with no other test failing. This gate locks the wiring.
    """
    tree = ast.parse(DISPATCH_PATH.read_text(encoding="utf-8"))
    func = _find_function(tree, "setup_monitor", DISPATCH_PATH)

    calls = _function_calls(func)
    assert "load_harness_python_secret" in calls, (
        f"{DISPATCH_PATH.relative_to(REPO_ROOT)}: "
        "setup_monitor must call load_harness_python_secret() to pull the "
        "per-launch HMAC secret out of /results before the analyzed "
        "extension installs. Without this call, reconciliation falls back "
        "to the spoofable phase-only check (Codex H6)."
    )

    stamps_field = False
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and target.attr == "expected_harness_nonce"
                ):
                    stamps_field = True
                    break
            if stamps_field:
                break

    assert stamps_field, (
        f"{DISPATCH_PATH.relative_to(REPO_ROOT)}: "
        "setup_monitor must assign the loaded secret to "
        "``report.expected_harness_nonce`` (or equivalent attribute path) "
        "so reconciliation has the value to verify HMAC nonces against. "
        "An unstamped field reopens Codex H6."
    )
