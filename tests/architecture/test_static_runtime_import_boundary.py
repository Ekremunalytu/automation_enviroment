"""ES-3a import boundary: ``static_runtime`` must stay shippable in the minimal image.

The hardened ``automation_static_analyzer`` image (ADR 0016 §Decision 2) copies
only ``packages/analysis_contracts/`` + ``static_runtime/`` — deliberately NOT
``packages/analysis_engine/`` (whose ``__init__`` eagerly imports
``run_detection`` and would drag the whole dynamic engine in), and not
``workflows``/``executor``/``appcore``/``ui`` either. This gate fails any PR that
makes ``static_runtime`` import the dynamic engine, ``workflows``, ``executor``,
``appcore``, or ``ui`` — none of which are present in the image, so the import
would break ``import static_runtime`` inside the container at runtime (covered
live by ``tests/smoke/test_static_container_smoke.py``).
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]

# Top-level import roots that are NOT present in the hardened static image
# (it copies only packages/analysis_contracts/ + static_runtime/), so importing
# any of them would break `import static_runtime` inside the container.
_BANNED_IMPORT_ROOTS = ("workflows", "executor", "appcore", "ui")
_BANNED_PACKAGE_PREFIX = "packages.analysis_engine"


def _iter_imports(module_path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    references: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            references.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            references.append((node.lineno, node.module))
    return references


def test_static_runtime_imports_stay_within_hardened_image() -> None:
    violations: list[str] = []
    for module_path in sorted((REPO_ROOT / "static_runtime").rglob("*.py")):
        for lineno, module in _iter_imports(module_path):
            head = module.split(".", 1)[0]
            crosses_engine = module == _BANNED_PACKAGE_PREFIX or module.startswith(
                _BANNED_PACKAGE_PREFIX + "."
            )
            if head in _BANNED_IMPORT_ROOTS or crosses_engine:
                label = module_path.relative_to(REPO_ROOT).as_posix()
                violations.append(f"{label}:{lineno} imports {module}")

    assert not violations, (
        "static_runtime must import only the standard library + "
        "packages.analysis_contracts (and itself) so it stays shippable in the "
        "minimal hardened image. Forbidden imports found:\n" + "\n".join(violations)
    )
