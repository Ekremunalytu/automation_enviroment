"""W8-4 architecture regression gate: forbid bare-name binary in subprocess invocations.

The W8-4 helper module ``executor.binary_paths`` is the canonical home for
absolute paths to every binary invoked by ``executor/``. This test scans
``executor/`` for ``subprocess.run([...])`` and ``subprocess.Popen([...])``
calls whose first argument is a *literal* string starting with anything
other than ``/`` — exactly the PATH-hijack vector ``binary_paths`` exists
to close.

Identifier references (``subprocess.run([CODE_PATH, ...])``) are skipped:
they resolve to absolute strings via the constant module, whose own
absoluteness is pinned by ``tests/executor/test_absolute_paths.py``.
Variable references and list comprehensions are also skipped — opaque
forms are out of scope and reviewed by hand.

Allowlist:
- ``executor/binary_paths.py`` — the constant module itself.
- ``tests/**`` — not scanned (test fixtures legitimately invoke bare
  binaries to exercise mock subprocess paths).
- File-level pragma ``# arch-allow: bare-binary-path`` placed on the same
  line as the offending call (or the line directly above) for the rare
  case a future site genuinely needs a non-absolute literal.

Out of W8-4 scope (POST_POC follow-up):
- ``executor/flows/playwright/editor.py`` (xdotool)
- ``executor/flows/playwright/reset_state.py`` (pgrep, bash)
- ``executor/flows/playwright/monitor_runtime.py`` (ps)
- ``executor/flows/playwright/runtime_capture/extension_host.py``
  (inotifywait at :602 — pragma'd; strace at :504 — variable-indirect,
  see note below)
- ``executor/flows/playwright/runtime_capture/{filesystem,network}.py``
  (inotifywait, tshark — both via ``cmd = [...]; subprocess.Popen(cmd)``
  variable-indirect form, see note below)

Pragma'd inline literal sites are caught by this gate and escaped via
``# arch-allow: bare-binary-path``. Variable-indirect sites
(``cmd = ["bare", ...]; subprocess.Popen(cmd)``) are intentionally
skipped by ``_detects_bare_binary_literal`` (opaque first-arg) and
therefore *cannot* be enforced here — they are tracked under the same
follow-up so that the broader migration covers both forms.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SCANNED_DIR = "executor"
EXCLUDED_PATHS = ("executor/binary_paths.py",)
PRAGMA = "arch-allow: bare-binary-path"


def _module_label(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _is_subprocess_invocation(call: ast.Call) -> bool:
    """Return True if ``call`` is ``subprocess.run`` or ``subprocess.Popen``."""
    func = call.func
    if isinstance(func, ast.Attribute) and func.attr in {"run", "Popen"}:
        value = func.value
        if isinstance(value, ast.Name) and value.id == "subprocess":
            return True
    return False


def _detects_bare_binary_literal(call: ast.Call) -> int | None:
    """Return the call's lineno if arg[0] is a literal list whose head is a
    bare-name string (not starting with ``/``), else None.

    Identifier references and opaque variable arguments are intentionally
    skipped — those resolve through ``binary_paths`` constants which are
    asserted absolute by ``test_absolute_paths.py``.
    """
    if not call.args:
        return None
    first_arg = call.args[0]
    if not isinstance(first_arg, ast.List) or not first_arg.elts:
        return None
    head = first_arg.elts[0]
    if not (isinstance(head, ast.Constant) and isinstance(head.value, str)):
        return None
    if head.value.startswith("/"):
        return None
    return call.lineno


def _pragma_lines(source: str) -> set[int]:
    return {
        lineno
        for lineno, line in enumerate(source.splitlines(), start=1)
        if PRAGMA in line
    }


def _iter_python_files() -> list[Path]:
    return sorted((REPO_ROOT / SCANNED_DIR).rglob("*.py"))


def test_no_bare_binary_in_subprocess_invocations() -> None:
    violations: list[str] = []

    for module_path in _iter_python_files():
        rel = _module_label(module_path)
        if rel in EXCLUDED_PATHS:
            continue

        source = module_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        pragma_at = _pragma_lines(source)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not _is_subprocess_invocation(node):
                continue
            offense_line = _detects_bare_binary_literal(node)
            if offense_line is None:
                continue
            if any(line in pragma_at for line in (offense_line, offense_line - 1)):
                continue
            violations.append(f"{rel}:{offense_line}")

    assert not violations, (
        "bare-name binary literal in subprocess invocation detected. "
        "Use the absolute constant from executor.binary_paths (e.g. CODE_PATH, "
        "PYTHON3_PATH, PKILL_PATH, RM_PATH, XDG_OPEN_PATH) or docker_path() "
        "for the host docker CLI; or add `# arch-allow: bare-binary-path` if "
        "intentional.\n" + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------


def _scan_synthetic_source(source: str) -> list[int]:
    """Mirror the production scan loop body for a synthetic source."""
    pragma_at = _pragma_lines(source)
    tree = ast.parse(source)
    offending: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not _is_subprocess_invocation(node):
            continue
        offense_line = _detects_bare_binary_literal(node)
        if offense_line is None:
            continue
        if any(line in pragma_at for line in (offense_line, offense_line - 1)):
            continue
        offending.append(offense_line)
    return offending


def test_detector_flags_bare_binary_literal() -> None:
    """Self-test: confirm the detector fires on the canonical
    ``subprocess.run(["bare", ...])`` pattern."""
    source = 'import subprocess\nsubprocess.run(["bare", "arg"])\n'
    assert _scan_synthetic_source(source) == [2]


def test_detector_flags_bare_binary_in_popen() -> None:
    source = 'import subprocess\nsubprocess.Popen(["bash", "script.sh"])\n'
    assert _scan_synthetic_source(source) == [2]


def test_detector_ignores_absolute_binary_literal() -> None:
    source = (
        "import subprocess\n"
        'subprocess.run(["/usr/bin/code", "--install-extension"])\n'
    )
    assert _scan_synthetic_source(source) == []


def test_detector_ignores_identifier_reference() -> None:
    """``subprocess.run([CODE_PATH, ...])`` is safe via constant resolution;
    detector must not false-fire on Name references."""
    source = (
        "import subprocess\n"
        "from executor.binary_paths import CODE_PATH\n"
        'subprocess.run([CODE_PATH, "--install-extension"])\n'
    )
    assert _scan_synthetic_source(source) == []


def test_detector_ignores_opaque_variable_argument() -> None:
    """When arg[0] is an opaque variable (not a literal list), the detector
    cannot resolve absoluteness; out of gate scope, reviewed by hand."""
    source = "import subprocess\nsubprocess.run(cmd)\n"
    assert _scan_synthetic_source(source) == []


def test_detector_ignores_unrelated_subprocess_attributes() -> None:
    """``subprocess.PIPE`` and similar are not invocations; detector must
    only fire on ``run`` / ``Popen``."""
    source = (
        "import subprocess\n"
        "stream = subprocess.PIPE\n"
        'subprocess.check_output(["bare", "arg"])\n'
    )
    # subprocess.check_output is NOT in the gate scope — only run/Popen.
    assert _scan_synthetic_source(source) == []


def test_pragma_escapes_violation_on_same_line() -> None:
    source = (
        "import subprocess\n"
        'subprocess.run(["bare", "arg"])  # arch-allow: bare-binary-path\n'
    )
    assert _scan_synthetic_source(source) == []


def test_pragma_escapes_violation_on_line_above() -> None:
    source = (
        "import subprocess\n"
        "# arch-allow: bare-binary-path\n"
        'subprocess.run(["bare", "arg"])\n'
    )
    assert _scan_synthetic_source(source) == []


def test_pragma_two_lines_above_does_not_escape() -> None:
    source = (
        "import subprocess\n"
        "# arch-allow: bare-binary-path\n"
        "# unrelated intervening comment\n"
        'subprocess.run(["bare", "arg"])\n'
    )
    assert _scan_synthetic_source(source) == [4]
