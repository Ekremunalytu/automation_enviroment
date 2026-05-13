"""W14-5 sub-commit 3 architecture gate: the executor runtime
fingerprint must be:

1. Defined as a closed-API module ``executor/runtime_fingerprint.py``
   exporting the ``executor_fingerprint`` callable.
2. Emitted at the automation output boundary
   (``executor/flows/playwright/report_builder.py``
   ``_assemble_report_payload``).
3. Pinned in the ``ActivationReport`` contract
   (``packages/analysis_contracts/contracts.py``) as the
   ``executor_fingerprint`` field so downstream consumers see a
   stable shape regardless of the fingerprint provider.

Closes the gate-side of ``[FOLLOWUP codex-automation-5]`` so a
future refactor cannot silently drop the emit boundary while
keeping the fingerprint module importable.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FINGERPRINT_MODULE_PATH = REPO_ROOT / "executor" / "runtime_fingerprint.py"
REPORT_BUILDER_PATH = (
    REPO_ROOT / "executor" / "flows" / "playwright" / "report_builder.py"
)
CONTRACTS_PATH = REPO_ROOT / "packages" / "analysis_contracts" / "contracts.py"


def _module_tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Invariant 1 — runtime_fingerprint module exists with the canonical exports.
# ---------------------------------------------------------------------------


def test_executor_runtime_fingerprint_module_exists_with_canonical_exports() -> None:
    assert FINGERPRINT_MODULE_PATH.exists(), (
        "executor/runtime_fingerprint.py must exist — "
        "W14-5 sub-commit 3 owns the fingerprint source. "
        "[FOLLOWUP codex-automation-5]"
    )
    tree = _module_tree(FINGERPRINT_MODULE_PATH)
    function_names = {
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    assert "executor_fingerprint" in function_names, (
        "executor/runtime_fingerprint.py must export "
        "`executor_fingerprint() -> dict[str, str]` as the canonical "
        "fingerprint source. W14-5 sub-commit 3."
    )
    assert "executor_fingerprint_short" in function_names, (
        "executor/runtime_fingerprint.py must export "
        "`executor_fingerprint_short() -> str` for the LogContextFilter "
        "stamping path. W14-5 sub-commit 3."
    )


# ---------------------------------------------------------------------------
# Invariant 2 — report_builder._assemble_report_payload invokes
# executor_fingerprint().
# ---------------------------------------------------------------------------


def test_report_builder_emit_path_invokes_executor_fingerprint() -> None:
    tree = _module_tree(REPORT_BUILDER_PATH)

    imports_fingerprint = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module == "executor.runtime_fingerprint":
            for alias in node.names:
                if alias.name == "executor_fingerprint":
                    imports_fingerprint = True
                    break
    assert imports_fingerprint, (
        "executor/flows/playwright/report_builder.py must import "
        "`executor_fingerprint` from executor.runtime_fingerprint so "
        "the automation output boundary carries the W14-5 fingerprint. "
        "[FOLLOWUP codex-automation-5]"
    )

    call_count = 0
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "executor_fingerprint"
        ):
            call_count += 1
    assert call_count >= 1, (
        "executor/flows/playwright/report_builder.py must call "
        "`executor_fingerprint()` at the automation output boundary "
        "(`_assemble_report_payload`). [FOLLOWUP codex-automation-5]"
    )


# ---------------------------------------------------------------------------
# Invariant 3 — ActivationReport contract pins the executor_fingerprint field.
# ---------------------------------------------------------------------------


def test_activation_report_contract_pins_executor_fingerprint_field() -> None:
    tree = _module_tree(CONTRACTS_PATH)
    activation_report: ast.ClassDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ActivationReport":
            activation_report = node
            break
    assert activation_report is not None, (
        "ActivationReport class must exist in "
        "packages/analysis_contracts/contracts.py."
    )

    found = False
    for stmt in activation_report.body:
        if (
            isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and stmt.target.id == "executor_fingerprint"
        ):
            found = True
            break
    assert found, (
        "ActivationReport must carry `executor_fingerprint: dict[str, str]` "
        "as the W14-5 sub-commit 3 contract field "
        "([FOLLOWUP codex-automation-5]). Without this field the "
        "fingerprint emitted by report_builder is stripped at the "
        "Pydantic validation boundary."
    )
