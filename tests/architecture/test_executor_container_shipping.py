"""Architecture regression gate: every ``executor.<root>`` module imported by
container-shipped code must itself be COPY'd into the executor container.

W14-6.c (`e42a448`) added ``executor/binary_paths.py`` and migrated four
``executor/flows/playwright/runtime_capture/**`` sites to import
``INOTIFYWAIT_PATH`` / ``TSHARK_PATH`` / ``STRACE_PATH`` from it. W14-5.3
(`db25d5f`) added ``executor/runtime_fingerprint.py`` and wired
``executor/flows/playwright/report_builder.py`` to call
``executor.runtime_fingerprint.executor_fingerprint`` at automation-output
emit. Both commits shipped on `week14` without updating
``executor/container/Dockerfile`` — the COPY directives only ship
``executor/flows/`` and ``packages/``, so the new root modules were
absent from the running container. Result: ``python3 -m
executor.flows.playwright.entrypoint --monitor`` raised
``ModuleNotFoundError: No module named 'executor.binary_paths'`` at first
import, the automation subprocess exited non-zero, and the analysis job
failed at the ``run_monitoring`` step (UI showed stale "Installing
extension in sandbox / 5%" because the close-out evidence path never
reached scenario dispatch).

This gate parses ``executor/container/Dockerfile`` for the canonical
``COPY [--chown=...] executor/<name>.py /home/executor/<name>.py``
pattern and for the directory-level ``COPY executor/flows
/home/executor/flows``, then walks every Python file that the container
imports (``executor/flows/**/*.py`` plus the shipped root modules
themselves, transitively) and asserts that every absolute
``from executor.<name>`` import resolves to either:

  - ``executor.flows.*`` — shipped as a directory, OR
  - ``executor.<name>`` whose root file ``executor/<name>.py`` is
    explicitly COPY'd into the container.

The check is read-only and AST-based; it does not require Docker.

A future addition of an ``executor/<X>.py`` root module that
``executor/flows/**`` imports must add the matching COPY line in
``executor/container/Dockerfile``. Conversely, dropping a root file the
container relies on (or renaming it without updating both the import and
the COPY) will fail this gate before the regression reaches a build.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTOR_ROOT = REPO_ROOT / "executor"
DOCKERFILE = EXECUTOR_ROOT / "container" / "Dockerfile"
FLOWS_DIR = EXECUTOR_ROOT / "flows"

_ROOT_COPY_PATTERN = re.compile(
    r"^\s*COPY(?:\s+--chown=\S+)?\s+executor/(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\.py\s+"
    r"/home/executor/(?P=name)\.py\s*$",
    re.MULTILINE,
)
_FLOWS_DIR_COPY_PATTERN = re.compile(
    r"^\s*COPY(?:\s+--chown=\S+)?\s+executor/flows\s+/home/executor/flows\s*$",
    re.MULTILINE,
)


def _shipped_root_modules() -> set[str]:
    """Names of executor-root .py modules COPY'd into the container."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    return {m.group("name") for m in _ROOT_COPY_PATTERN.finditer(text)}


def _flows_shipped_as_directory() -> bool:
    text = DOCKERFILE.read_text(encoding="utf-8")
    return _FLOWS_DIR_COPY_PATTERN.search(text) is not None


def _imported_executor_root_modules(scan_files: list[Path]) -> dict[str, list[Path]]:
    """Collect ``from executor.<X> import ...`` references where X is a
    single-segment root submodule (not ``flows`` or a deeper dotted path).

    Returns a mapping ``{name: [files that import it]}`` so the failure
    message can point an operator at every site to update.
    """
    refs: dict[str, list[Path]] = {}
    for path in scan_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            module = node.module or ""
            if not module.startswith("executor."):
                continue
            parts = module.split(".")
            if len(parts) != 2:
                continue
            name = parts[1]
            if name == "flows":
                continue
            refs.setdefault(name, []).append(path)
    return refs


def _files_to_scan(shipped_root: set[str]) -> list[Path]:
    """Container-imported Python files: every ``executor/flows/**/*.py``
    plus the shipped root modules themselves (so transitive imports
    between root modules — e.g. ``runtime_fingerprint`` ->
    ``binary_paths`` — are also covered).
    """
    files: list[Path] = sorted(FLOWS_DIR.rglob("*.py"))
    for name in sorted(shipped_root):
        candidate = EXECUTOR_ROOT / f"{name}.py"
        if candidate.is_file():
            files.append(candidate)
    return files


def test_executor_flows_imports_are_shipped_into_container() -> None:
    assert (
        _flows_shipped_as_directory()
    ), "executor/container/Dockerfile must `COPY executor/flows /home/executor/flows`."
    shipped = _shipped_root_modules()
    scan_files = _files_to_scan(shipped)
    references = _imported_executor_root_modules(scan_files)
    missing = {name: paths for name, paths in references.items() if name not in shipped}
    if missing:
        rendered = "\n".join(
            f"  - executor.{name}  (used by: {', '.join(str(p.relative_to(REPO_ROOT)) for p in sorted(set(paths)))})"
            for name, paths in sorted(missing.items())
        )
        raise AssertionError(
            "The following `executor.<root>` modules are imported by code "
            "that ships into the executor container but are NOT COPY'd by "
            "`executor/container/Dockerfile`. Add a `COPY --chown=executor:executor "
            "executor/<name>.py /home/executor/<name>.py` line, or rewrite "
            "the import to use a relative `from .<sibling>` path inside "
            "`executor/flows/`.\n"
            f"{rendered}"
        )


def test_shipped_root_modules_exist_on_host() -> None:
    """Every COPY directive must reference a file that actually exists on
    the host filesystem; otherwise the docker build fails with a far less
    obvious error than ``ModuleNotFoundError``.
    """
    shipped = _shipped_root_modules()
    missing_on_host = {
        name for name in shipped if not (EXECUTOR_ROOT / f"{name}.py").is_file()
    }
    assert not missing_on_host, (
        "executor/container/Dockerfile COPY directives reference files "
        f"that do not exist on the host: {sorted(missing_on_host)}. Either "
        "create the file or remove the COPY directive."
    )
