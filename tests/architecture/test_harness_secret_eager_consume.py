"""W13-11 architecture gate: secret consume precedes install_extension; env-priority load.

Codex F1 close-pass for W13-1 H6. The HMAC python secret at
``/results/_extrace_harness_python_secret`` (0600 executor:executor) was
consumed by ``setup_monitor`` only AFTER ``install_extension`` admitted the
target VSIX. A same-UID target could read the file during the
install -> setup_monitor window and forge HMAC-signed harness completion
markers, bypassing the W13-1 nonce gate.

W13-11 closes this by:

1. ``workflows/marketplace/analysis_service.py::execute_analysis_request``
   calling ``executor_control.consume_harness_python_secret()`` between
   ``_reset_sandbox()`` and ``_install_extension()`` — host-side read +
   unlink of the bind-mounted secret file before the target VSIX is admitted.
2. ``executor/host.py::run_playwright_automation`` threading the consumed
   secret through ``docker exec -e EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=<hex>``
   so the container-side entrypoint receives it via env var.
3. ``executor/flows/playwright/health/reconciliation.py::load_harness_python_secret``
   reading ``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE`` first; the legacy file
   fallback is preserved for unit-test paths that construct ``ActivationReport``
   directly.

This gate pins the three structural invariants as AST facts so a future
refactor cannot reintroduce the install -> setup_monitor race window with
no other test failing.

Defense-in-depth siblings:

- ``tests/executor/test_harness_secret_eager_consume.py``
  (W13-11 RED -> GREEN: behavioral race + env threading regression).
- ``tests/executor/test_playwright_health_reconciliation.py``
  (env-priority unit cases).
- ``tests/security/test_executor_host_error_redaction.py``
  (E4 mitigation: env var value masked in ExecutorError messages).
- ``tests/architecture/test_harness_marker_auth.py``
  (W13-1: phase-only acceptance closed; setup_monitor stamps the nonce).
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_SERVICE_PATH = REPO_ROOT / "workflows" / "marketplace" / "analysis_service.py"
HOST_PATH = REPO_ROOT / "executor" / "host.py"
# W16-4: ``load_harness_python_secret`` moved from reconciliation.py to
# security.py alongside the W13-1 HMAC primitives. Gate 3 below now
# parses security.py instead.
SECURITY_PATH = (
    REPO_ROOT / "executor" / "flows" / "playwright" / "health" / "security.py"
)


def _find_function(tree: ast.AST, name: str, source_path: Path) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(
        f"{source_path.relative_to(REPO_ROOT)}: "
        f"function {name!r} missing — W13-11 wiring removed?"
    )


def test_execute_analysis_request_consumes_secret_before_install() -> None:
    """W13-11 Gate 1: secret consume call site must appear after reset_sandbox and before install_extension."""
    tree = ast.parse(ANALYSIS_SERVICE_PATH.read_text(encoding="utf-8"))
    func = _find_function(tree, "execute_analysis_request", ANALYSIS_SERVICE_PATH)

    reset_line: int | None = None
    consume_line: int | None = None
    install_line: int | None = None

    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        # ``executor_control.consume_harness_python_secret()`` — Attribute call.
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "consume_harness_python_secret"
        ):
            consume_line = node.lineno
            continue
        # ``_install_extension(...)`` and ``_reset_sandbox(...)`` — bare Name calls.
        if isinstance(node.func, ast.Name):
            if node.func.id == "_install_extension":
                install_line = node.lineno
            elif node.func.id == "_reset_sandbox":
                reset_line = node.lineno

    assert reset_line is not None, (
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
        "execute_analysis_request must call _reset_sandbox so launch_vscode.sh "
        "runs and writes the per-launch HMAC secret."
    )
    assert consume_line is not None, (
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
        "execute_analysis_request must call executor_control."
        "consume_harness_python_secret() so the secret is read+unlinked on "
        "the host BEFORE the analyzed VSIX is admitted. Without this call "
        "the install -> setup_monitor window remains open and Codex F1 "
        "(target reads /results/_extrace_harness_python_secret same-UID) "
        "re-opens W13-1 H6."
    )
    assert install_line is not None, (
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
        "execute_analysis_request must call _install_extension."
    )
    assert reset_line < consume_line < install_line, (
        f"{ANALYSIS_SERVICE_PATH.relative_to(REPO_ROOT)}: "
        f"sequence invariant broken — reset_sandbox at line {reset_line}, "
        f"consume_harness_python_secret at line {consume_line}, "
        f"install_extension at line {install_line}. "
        "The secret must be consumed AFTER reset (so launch_vscode.sh has "
        "written the file) and BEFORE install (so target VSIX cannot read "
        "the file during its activation window). This call ordering is the "
        "core W13-11 close-pass."
    )


def test_run_playwright_automation_threads_secret_env_var() -> None:
    """W13-11 Gate 2: run_playwright_automation must thread harness_python_secret via EXECUTOR_HARNESS_PYTHON_SECRET_VALUE env var."""
    tree = ast.parse(HOST_PATH.read_text(encoding="utf-8"))
    func = _find_function(tree, "run_playwright_automation", HOST_PATH)

    has_env_var_literal = False
    reads_secret_param = False
    for node in ast.walk(func):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value == "EXECUTOR_HARNESS_PYTHON_SECRET_VALUE"
        ):
            has_env_var_literal = True
        if isinstance(node, ast.Name) and node.id == "harness_python_secret":
            reads_secret_param = True

    assert has_env_var_literal, (
        f"{HOST_PATH.relative_to(REPO_ROOT)}: "
        "run_playwright_automation body must reference the string literal "
        '"EXECUTOR_HARNESS_PYTHON_SECRET_VALUE" — this is the env var the '
        "entrypoint container reads to receive the eager-consumed secret. "
        "Without this literal, the secret never reaches the harness HMAC "
        "verifier and the W13-11 close-pass is incomplete."
    )
    assert reads_secret_param, (
        f"{HOST_PATH.relative_to(REPO_ROOT)}: "
        "run_playwright_automation must read its ``harness_python_secret`` "
        "parameter — the host-side consume result must flow through this "
        "kw-arg into the docker exec env var."
    )


def test_load_harness_python_secret_prefers_env_var_over_file() -> None:
    """W13-11 Gate 3: load_harness_python_secret reads EXECUTOR_HARNESS_PYTHON_SECRET_VALUE before any file read.

    W16-4 re-target: the function moved to ``security.py`` alongside the
    W13-1 HMAC verifier. AST walk now parses the new module path.
    """
    tree = ast.parse(SECURITY_PATH.read_text(encoding="utf-8"))
    func = _find_function(tree, "load_harness_python_secret", SECURITY_PATH)

    env_read_line: int | None = None
    file_read_line: int | None = None
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        # ``os.environ.get("EXECUTOR_HARNESS_PYTHON_SECRET_VALUE", ...)``.
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "environ"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "EXECUTOR_HARNESS_PYTHON_SECRET_VALUE"
        ):
            env_read_line = node.lineno
        # ``path.read_text(...)``.
        if isinstance(node.func, ast.Attribute) and node.func.attr == "read_text":
            file_read_line = node.lineno

    assert env_read_line is not None, (
        f"{SECURITY_PATH.relative_to(REPO_ROOT)}: "
        "load_harness_python_secret must read EXECUTOR_HARNESS_PYTHON_SECRET_VALUE "
        "from os.environ — this is how the host-side eager-consumed secret "
        "reaches the container-side verifier. Without it the function falls "
        "back to reading /results/_extrace_harness_python_secret which the "
        "target VSIX may have already consumed (Codex F1)."
    )
    assert file_read_line is not None, (
        f"{SECURITY_PATH.relative_to(REPO_ROOT)}: "
        "load_harness_python_secret must still support the legacy file "
        "fallback for unit-test paths that construct ActivationReport "
        "directly without going through host-side eager-consume."
    )
    assert env_read_line < file_read_line, (
        f"{SECURITY_PATH.relative_to(REPO_ROOT)}: "
        f"env-priority broken — env read at line {env_read_line}, "
        f"file read at line {file_read_line}. The env var must be checked "
        "first so the host-supplied secret wins over any stale file that "
        "may have leaked into the next launch cycle."
    )
