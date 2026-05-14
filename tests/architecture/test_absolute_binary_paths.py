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
List comprehensions and opaque variable references whose source cannot
be resolved within the local function scope are also skipped — reviewed
by hand.

W14-6 sub-commit 6 extension (`[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]`):
the **variable-indirect form** ``cmd = ["bare", ...]; subprocess.Popen(cmd)``
is now in scope. The detector tracks list-literal assignments inside
each function body and, when ``subprocess.Popen(cmd)`` is invoked
with a Name argument, looks up the most recent enclosing assignment
of that name. If the assignment is a literal list with a bare-name
string head, the call is flagged exactly like the direct form would
be. List literals whose head is a Name reference (e.g. ``cmd = [TSHARK_PATH, ...]``)
or whose head is a non-constant expression are skipped (the resolution
still gates via the absolute-path constants module).

Allowlist:
- ``executor/binary_paths.py`` — the constant module itself.
- ``tests/**`` — not scanned (test fixtures legitimately invoke bare
  binaries to exercise mock subprocess paths).
- File-level pragma ``# arch-allow: bare-binary-path`` placed on the same
  line as the offending call (or the line directly above) for the rare
  case a future site genuinely needs a non-absolute literal.

Pragma'd inline literal sites are caught by this gate and escaped via
``# arch-allow: bare-binary-path``. Pre-W14-6 the variable-indirect
form silently bypassed the detector; sub-commit 6 closes that gap by
migrating the three known sites to ``executor.binary_paths`` constants
(``INOTIFYWAIT_PATH`` / ``TSHARK_PATH`` / ``STRACE_PATH``) and extending
the gate so a future regression cannot reintroduce the pattern.
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


def _list_head_is_bare_constant(list_node: ast.List) -> bool:
    """Return True when ``list_node`` has a bare-name string head: a
    string ``ast.Constant`` whose value does not start with ``/``."""
    if not list_node.elts:
        return False
    head = list_node.elts[0]
    if not (isinstance(head, ast.Constant) and isinstance(head.value, str)):
        return False
    return not head.value.startswith("/")


def _collect_list_assignments(scope: ast.AST) -> dict[str, list[ast.List]]:
    """Walk ``scope`` (typically a function body) and collect every
    ``<name> = [...]`` assignment whose RHS is a list literal. The
    return mapping is name -> list-of-list-literals so a name that
    is reassigned multiple times in the same scope contributes each
    candidate list to the resolver below (any bare-name head among
    them fails the gate)."""
    assignments: dict[str, list[ast.List]] = {}
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(node.value)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and isinstance(node.value, ast.List)
        ):
            assignments.setdefault(node.target.id, []).append(node.value)
    return assignments


def _detects_bare_binary_via_variable_indirect(
    call: ast.Call,
    scope_assignments: dict[str, list[ast.List]],
) -> int | None:
    """Return the call's lineno when ``subprocess.Popen(cmd)`` resolves
    to a ``cmd = ["bare", ...]`` assignment in the enclosing scope.

    Skips:

    - First arg is not a ``Name`` (literal lists go through the direct
      detector; opaque expressions are reviewed by hand).
    - Name resolves to an assignment we cannot see (function arg,
      closure, module-level constant).
    - Resolved list head is a ``Name`` reference (constant from
      ``executor.binary_paths`` — the gate trusts ``test_absolute_paths.py``
      to assert absoluteness of those constants).
    - Resolved list head is a non-string constant or non-constant
      expression.
    """
    if not call.args:
        return None
    first_arg = call.args[0]
    if not isinstance(first_arg, ast.Name):
        return None
    candidate_lists = scope_assignments.get(first_arg.id)
    if not candidate_lists:
        return None
    if any(_list_head_is_bare_constant(lst) for lst in candidate_lists):
        return call.lineno
    return None


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

        # W14-6 sub-commit 6: walk function-scope by function-scope so
        # the variable-indirect resolver has a meaningful local
        # ``cmd = [...]`` map. The direct-literal check still runs on
        # every Call node (so module-level subprocess literals are
        # caught too).
        function_scopes: list[ast.AST] = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        ]
        scope_to_assignments: dict[int, dict[str, list[ast.List]]] = {
            id(scope): _collect_list_assignments(scope) for scope in function_scopes
        }
        scope_membership: dict[int, ast.AST] = {}
        for scope in function_scopes:
            for inner in ast.walk(scope):
                scope_membership.setdefault(id(inner), scope)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not _is_subprocess_invocation(node):
                continue

            offense_line = _detects_bare_binary_literal(node)
            if offense_line is None:
                # Try the variable-indirect resolver next.
                enclosing_scope = scope_membership.get(id(node))
                if enclosing_scope is not None:
                    scope_assignments = scope_to_assignments[id(enclosing_scope)]
                    offense_line = _detects_bare_binary_via_variable_indirect(
                        node, scope_assignments
                    )
            if offense_line is None:
                continue
            if any(line in pragma_at for line in (offense_line, offense_line - 1)):
                continue
            violations.append(f"{rel}:{offense_line}")

    assert not violations, (
        "bare-name binary literal in subprocess invocation detected. "
        "Use the absolute constant from executor.binary_paths (e.g. CODE_PATH, "
        "PYTHON3_PATH, PKILL_PATH, RM_PATH, XDG_OPEN_PATH, INOTIFYWAIT_PATH, "
        "TSHARK_PATH, STRACE_PATH) or docker_path() for the host docker CLI; "
        "or add `# arch-allow: bare-binary-path` if intentional.\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------


def _scan_synthetic_source(source: str) -> list[int]:
    """Mirror the production scan loop body for a synthetic source —
    including the W14-6 sub-commit 6 variable-indirect resolver."""
    pragma_at = _pragma_lines(source)
    tree = ast.parse(source)

    function_scopes: list[ast.AST] = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]
    scope_to_assignments: dict[int, dict[str, list[ast.List]]] = {
        id(scope): _collect_list_assignments(scope) for scope in function_scopes
    }
    scope_membership: dict[int, ast.AST] = {}
    for scope in function_scopes:
        for inner in ast.walk(scope):
            scope_membership.setdefault(id(inner), scope)

    offending: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not _is_subprocess_invocation(node):
            continue
        offense_line = _detects_bare_binary_literal(node)
        if offense_line is None:
            enclosing_scope = scope_membership.get(id(node))
            if enclosing_scope is not None:
                scope_assignments = scope_to_assignments[id(enclosing_scope)]
                offense_line = _detects_bare_binary_via_variable_indirect(
                    node, scope_assignments
                )
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
        'import subprocess\nsubprocess.run(["/usr/bin/code", "--install-extension"])\n'
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


# ---------------------------------------------------------------------------
# W14-6 sub-commit 6 self-tests: variable-indirect form coverage
# ---------------------------------------------------------------------------


def test_variable_indirect_bare_binary_is_detected() -> None:
    """The W14-6.c gate must flag ``cmd = ["bare", ...]`` /
    ``subprocess.Popen(cmd)`` shapes — the form that pre-W14-6 escaped
    the literal-only detector and shipped to production at the
    ``runtime_capture/{filesystem,network}.py`` + ``extension_host_capture.py``
    sites that sub-commit 6 migrated to absolute paths.
    """
    source = (
        "import subprocess\n"
        "def start():\n"
        '    cmd = ["inotifywait", "-m", "/tmp/x"]\n'
        "    subprocess.Popen(cmd)\n"
    )
    assert _scan_synthetic_source(source) == [4]


def test_variable_indirect_absolute_path_is_not_detected() -> None:
    """After migration, ``cmd = [INOTIFYWAIT_PATH, ...]`` resolves
    through ``executor.binary_paths`` constants — the detector must
    skip because the head element is a Name reference, not a string
    constant."""
    source = (
        "import subprocess\n"
        "INOTIFYWAIT_PATH = '/usr/bin/inotifywait'\n"
        "def start():\n"
        "    cmd = [INOTIFYWAIT_PATH, '-m', '/tmp/x']\n"
        "    subprocess.Popen(cmd)\n"
    )
    assert _scan_synthetic_source(source) == []


def test_variable_indirect_opaque_variable_argument_is_skipped() -> None:
    """``cmd`` whose assignment is not a list literal (e.g. derived
    from a helper) cannot be resolved statically — the detector
    skips. Out of gate scope, reviewed by hand. This matches the
    pre-W14-6 ``test_detector_ignores_opaque_variable_argument``
    contract for the direct form."""
    source = (
        "import subprocess\n"
        "def start():\n"
        "    cmd = build_cmd()\n"
        "    subprocess.Popen(cmd)\n"
    )
    assert _scan_synthetic_source(source) == []


def test_variable_indirect_pragma_escapes_violation() -> None:
    """Same pragma escape works on the variable-indirect form when
    placed on the ``subprocess.Popen(cmd)`` line (same-line or
    line-above)."""
    source_same_line = (
        "import subprocess\n"
        "def start():\n"
        '    cmd = ["inotifywait", "-m", "/tmp/x"]\n'
        "    subprocess.Popen(cmd)  # arch-allow: bare-binary-path\n"
    )
    source_line_above = (
        "import subprocess\n"
        "def start():\n"
        '    cmd = ["inotifywait", "-m", "/tmp/x"]\n'
        "    # arch-allow: bare-binary-path\n"
        "    subprocess.Popen(cmd)\n"
    )
    assert _scan_synthetic_source(source_same_line) == []
    assert _scan_synthetic_source(source_line_above) == []


def test_variable_indirect_multiple_reassignments_flag_any_bare_one() -> None:
    """If ``cmd`` is reassigned multiple times in the same function
    and any one of the assignments is a list literal with a bare-name
    head, the gate must fire — a future refactor could leave one
    branch on the absolute path while another silently regressed."""
    source = (
        "import subprocess\n"
        "INOTIFYWAIT_PATH = '/usr/bin/inotifywait'\n"
        "def start(use_abs: bool):\n"
        "    if use_abs:\n"
        "        cmd = [INOTIFYWAIT_PATH, '-m', '/tmp/x']\n"
        "    else:\n"
        '        cmd = ["inotifywait", "-m", "/tmp/x"]\n'
        "    subprocess.Popen(cmd)\n"
    )
    assert _scan_synthetic_source(source) == [8]


def test_variable_indirect_assignment_outside_function_scope_skipped() -> None:
    """Module-level ``cmd = [...]`` is intentionally out of scope:
    the resolver is bounded to function bodies because module-level
    constants belong in ``executor.binary_paths``. If the test
    fixture below ever lands in production code, the architecture
    review should catch it by hand, not via this gate."""
    source = (
        "import subprocess\n"
        'cmd = ["inotifywait", "-m"]\n'
        "subprocess.Popen(cmd)\n"
    )
    # The variable-indirect resolver only walks function bodies, so
    # module-level cmd assignments are not tracked. The Name first-arg
    # gets the "opaque variable" treatment and the gate skips.
    assert _scan_synthetic_source(source) == []
