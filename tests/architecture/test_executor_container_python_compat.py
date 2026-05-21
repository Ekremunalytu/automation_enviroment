"""Architecture regression gate: forbid Python 3.11+ APIs in code that
ships into the executor container.

W14-5.3 (`db25d5f`) added ``executor/runtime_fingerprint.py`` with
``from datetime import UTC`` — a Python 3.11+ API. The executor
container ships ``ubuntu:22.04`` + ``python3`` (3.10), where
``datetime.UTC`` does not exist. The W14-7.a hotfix (`df925f8`) swapped
the import for the established
``getattr(_dt, "UTC", _dt.timezone.utc)`` shim aligned with
``packages/analysis_engine/runner.py:26``. The companion W14-7.b gate
[tests/architecture/test_executor_container_shipping.py](test_executor_container_shipping.py)
caught the **missing-COPY** half of the regression but did NOT catch
the **incompatible-API** half — because tests run on the host's
Python 3.11+, where the import succeeds.

This gate closes the second loop: AST-scan every container-shipped
Python file for Python 3.11+ imports and fail if any non-allowlisted
usage appears. The shipped-file list is derived from
``executor/container/Dockerfile`` COPY directives (single source of
truth — same parser as ``test_executor_container_shipping.py``).

Forbidden imports (Python 3.11+, ordered by surface area observed in
real codebases):

- ``from datetime import UTC``               (Python 3.11)
- ``from typing import Self``                (Python 3.11)
- ``from typing import NotRequired``         (Python 3.11)
- ``from typing import Required``            (Python 3.11)
- ``from typing import LiteralString``       (Python 3.11)
- ``from typing import TypeVarTuple``        (Python 3.11)
- ``from typing import Unpack``              (Python 3.11)
- ``from typing import ExceptionGroup``      (Python 3.11)
- ``from typing import BaseExceptionGroup``  (Python 3.11)
- ``import tomllib``                         (Python 3.11)
- ``from tomllib import ...``                (Python 3.11)

Allowlist:

- File-level: container-shipped status — only files that the executor
  container actually imports are scanned. Sibling host-only modules
  (``executor/host.py``, ``executor/config.py``, ``executor/control.py``)
  run in the API container's Python 3.11+ and are out of scope.
- Per-import: pragma ``# arch-allow: py311-api`` on the same line as
  (or directly above) the offending import. Mirrors the
  ``# arch-allow: bare-binary-path`` pattern from W14-6. Use only when
  a compat shim has been installed elsewhere and the import is
  guaranteed-safe in the target runtime.

The detector is import-only. Attribute access of the form
``import datetime; datetime.UTC`` is not detected — wrapping the import
form catches every actual W14 regression we have seen, and a stricter
attribute walker is left for a future iteration if a real attribute
regression surfaces.
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

_ALLOW_PRAGMA = "arch-allow: py311-api"

# Python 3.11+ symbols banned in container-shipped code.
_FORBIDDEN_FROM_IMPORT: dict[str, set[str]] = {
    "datetime": {"UTC"},
    "typing": {
        "Self",
        "NotRequired",
        "Required",
        "LiteralString",
        "TypeVarTuple",
        "Unpack",
        "ExceptionGroup",
        "BaseExceptionGroup",
    },
}
_FORBIDDEN_TOPLEVEL_IMPORT: set[str] = {"tomllib"}


def _shipped_root_modules() -> set[str]:
    text = DOCKERFILE.read_text(encoding="utf-8")
    return {m.group("name") for m in _ROOT_COPY_PATTERN.finditer(text)}


def _shipped_python_files() -> list[Path]:
    """Every Python file the executor container actually imports."""
    files: list[Path] = sorted(FLOWS_DIR.rglob("*.py"))
    for name in sorted(_shipped_root_modules()):
        candidate = EXECUTOR_ROOT / f"{name}.py"
        if candidate.is_file():
            files.append(candidate)
    return files


def _line_or_prev_line_has_pragma(source_lines: list[str], lineno: int) -> bool:
    """Mirror the W14-6 ``arch-allow: bare-binary-path`` pragma lookup —
    the pragma can sit on the offending line or the line directly above.
    """
    if lineno <= 0 or lineno > len(source_lines):
        return False
    target = source_lines[lineno - 1]
    above = source_lines[lineno - 2] if lineno >= 2 else ""
    return _ALLOW_PRAGMA in target or _ALLOW_PRAGMA in above


def _scan_file(path: Path) -> list[str]:
    """Return a list of human-readable violation messages found in ``path``."""
    source = path.read_text(encoding="utf-8")
    source_lines = source.splitlines()
    tree = ast.parse(source)
    rel = path.relative_to(REPO_ROOT)
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            banned = _FORBIDDEN_FROM_IMPORT.get(module, set())
            for alias in node.names:
                if alias.name not in banned:
                    continue
                if _line_or_prev_line_has_pragma(source_lines, node.lineno):
                    continue
                violations.append(
                    f"{rel}:{node.lineno}  from {module} import {alias.name}  "
                    "(Python 3.11+ API; executor container ships Python 3.10)"
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in _FORBIDDEN_TOPLEVEL_IMPORT:
                    continue
                if _line_or_prev_line_has_pragma(source_lines, node.lineno):
                    continue
                violations.append(
                    f"{rel}:{node.lineno}  import {alias.name}  "
                    "(Python 3.11+ API; executor container ships Python 3.10)"
                )
    return violations


def test_executor_container_shipped_code_avoids_python_311_apis() -> None:
    violations: list[str] = []
    for path in _shipped_python_files():
        violations.extend(_scan_file(path))
    if violations:
        rendered = "\n".join(f"  - {line}" for line in violations)
        raise AssertionError(
            "The following Python 3.11+ imports appear in code that ships "
            "into the executor container (Python 3.10). Replace with a compat "
            "shim — the established pattern is at "
            "`packages/analysis_engine/runner.py:26` "
            '(`UTC = getattr(_dt, "UTC", _dt.timezone.utc)  # noqa: UP017`). '
            "If a specific call site is genuinely safe at runtime in 3.10 "
            "(e.g., guarded by a version check), tag the import with "
            "`# arch-allow: py311-api`.\n"
            f"{rendered}"
        )
