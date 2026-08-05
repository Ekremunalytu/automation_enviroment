"""Static evaluation contracts stay framework-agnostic."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "packages" / "analysis_contracts" / "static_evaluation"
FORBIDDEN = ("workflows", "executor", "appcore", "ui", "packages.analysis_engine")


def test_static_evaluation_contracts_do_not_cross_runtime_boundaries() -> None:
    violations: list[str] = []
    for path in CONTRACT_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.startswith(FORBIDDEN):
                    violations.append(f"{path.name}:{node.lineno}:{name}")
    assert not violations, violations
