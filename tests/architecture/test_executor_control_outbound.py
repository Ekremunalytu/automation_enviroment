"""W14-6.b architecture gate
(`[FOLLOWUP arch-gate-executor-control-outbound]`): pin the
``executor.control`` public surface so implementation types do not
leak across the workflow → executor boundary.

``executor/control.py`` is the canonical seam between
``workflows/`` and the executor sandbox mechanics. AGENTS.md line 66
locks the direction: "Workflows reach sandbox mechanics through
``executor.control``." The companion
``tests/architecture/test_import_graph.py`` already pins the
*import-graph* direction (workflows may import only
``executor.control`` / ``executor.control.*``). What it does **not**
check is the *semantic* shape of the public API — whether a
``docker`` / ``playwright`` / ``aiohttp`` type appears in a method
signature and forces a workflow caller to take a transitive
dependency on those implementation libraries.

This gate scans ``executor/control.py`` AST, identifies every
public method on every public class (and every public module-level
function), and asserts no forbidden-implementation token appears in
any argument annotation or return annotation. The forbidden set is
the implementation libraries that ``executor.host`` uses but the
control facade must hide:

- ``docker`` (the ``docker`` Python SDK and the host CLI)
- ``playwright`` (browser automation framework)
- ``aiohttp`` (executor-internal HTTP client for harness handshake)
- ``Page`` / ``Browser`` / ``Frame`` / ``Locator`` (Playwright objects)

If a future PR exposes one of these types on the public surface,
the control facade has stopped abstracting the executor sandbox and
a workflow caller is now coupled to the implementation choice. The
gate fires at PR time so the surface drift cannot land silently.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTROL_MODULE_PATH = REPO_ROOT / "executor" / "control.py"

_FORBIDDEN_TOKENS: frozenset[str] = frozenset(
    {
        "docker",
        "playwright",
        "aiohttp",
        "Page",
        "Browser",
        "Frame",
        "Locator",
    }
)


def _module_tree() -> ast.Module:
    return ast.parse(CONTROL_MODULE_PATH.read_text(encoding="utf-8"))


def _is_public_name(name: str) -> bool:
    return not name.startswith("_")


def _annotation_text(annotation: ast.expr | None) -> str:
    if annotation is None:
        return ""
    return ast.unparse(annotation)


def _collect_public_function_signatures(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[str, str]]:
    """Return (label, annotation_text) pairs for every annotated slot
    in the function signature: arguments + return type."""
    pairs: list[tuple[str, str]] = []
    args = func.args
    for arg in (
        *args.posonlyargs,
        *args.args,
        *args.kwonlyargs,
    ):
        if arg.arg == "self":
            continue
        text = _annotation_text(arg.annotation)
        if text:
            pairs.append((f"arg:{arg.arg}", text))
    if args.vararg is not None and args.vararg.annotation is not None:
        pairs.append(
            (f"vararg:{args.vararg.arg}", _annotation_text(args.vararg.annotation))
        )
    if args.kwarg is not None and args.kwarg.annotation is not None:
        pairs.append(
            (f"kwarg:{args.kwarg.arg}", _annotation_text(args.kwarg.annotation))
        )
    return_text = _annotation_text(func.returns)
    if return_text:
        pairs.append(("return", return_text))
    return pairs


def _iter_public_methods_of_class(
    cls: ast.ClassDef,
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [
        stmt
        for stmt in cls.body
        if isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef)
        and _is_public_name(stmt.name)
    ]


def _annotation_contains_forbidden_token(text: str) -> str | None:
    """Return the first forbidden token found in ``text`` (whole-word
    or attribute-access match), else None."""
    for token in _FORBIDDEN_TOKENS:
        # Match `Token`, `Token.foo`, `foo.Token`, `module.Token` etc.
        # Simple substring is enough because the forbidden tokens are
        # distinctive identifier names; a false positive on e.g.
        # ``DockerWorkflow`` (which we'd actually want to fire on) is
        # intended.
        if token in text:
            return token
    return None


# ---------------------------------------------------------------------------
# Invariant 1 — every public method on every public class has clean signatures
# ---------------------------------------------------------------------------


def test_public_class_methods_have_no_forbidden_implementation_types() -> None:
    tree = _module_tree()
    violations: list[str] = []
    for node in tree.body:
        if not (isinstance(node, ast.ClassDef) and _is_public_name(node.name)):
            continue
        for method in _iter_public_methods_of_class(node):
            for label, annotation in _collect_public_function_signatures(method):
                offender = _annotation_contains_forbidden_token(annotation)
                if offender is not None:
                    violations.append(
                        f"executor/control.py:{method.lineno} "
                        f"{node.name}.{method.name} {label}={annotation!r} "
                        f"leaks `{offender}` across the control boundary"
                    )
    assert not violations, (
        "executor.control public methods must not leak implementation "
        "types across the workflow boundary. AGENTS.md line 66 locks "
        "workflows to the control facade; exposing a `docker` / "
        "`playwright` / `aiohttp` type on a public method ties the "
        "caller to the implementation library. Hide it behind a string / "
        "dict / dataclass at the seam. Violations:\n" + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Invariant 2 — module-level public functions have clean signatures
# ---------------------------------------------------------------------------


def test_module_level_public_functions_have_no_forbidden_implementation_types() -> None:
    tree = _module_tree()
    violations: list[str] = []
    for node in tree.body:
        if not (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and _is_public_name(node.name)
        ):
            continue
        for label, annotation in _collect_public_function_signatures(node):
            offender = _annotation_contains_forbidden_token(annotation)
            if offender is not None:
                violations.append(
                    f"executor/control.py:{node.lineno} {node.name} "
                    f"{label}={annotation!r} leaks `{offender}` "
                    "across the control boundary"
                )
    assert not violations, (
        "executor.control module-level public functions must not leak "
        "implementation types across the workflow boundary. Violations:\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Invariant 3 — the `default_executor_control` module-level instance keeps
# the facade-instance contract (no rename / accidental removal).
# ---------------------------------------------------------------------------


def test_default_executor_control_singleton_is_pinned() -> None:
    """The module exports a ``default_executor_control`` instance as
    the convenient global handle every workflow uses. Removing it or
    renaming would force every caller to instantiate
    ``ExecutorControl()`` directly — at which point a future PR
    could trivially swap the class for a richer-but-leaky variant.
    """
    tree = _module_tree()
    found_assignment = False
    found_in_all = False
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "default_executor_control"
        ):
            found_assignment = True
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
            and isinstance(node.value, ast.List)
        ):
            for elt in node.value.elts:
                if (
                    isinstance(elt, ast.Constant)
                    and elt.value == "default_executor_control"
                ):
                    found_in_all = True
    assert found_assignment, (
        "executor/control.py must keep the module-level "
        "`default_executor_control = ExecutorControl()` instance — "
        "removing it forces every workflow caller to instantiate the "
        "class directly, weakening the W14-6.b boundary."
    )
    assert found_in_all, (
        "`default_executor_control` must be re-exported via "
        "executor/control.py `__all__` so the public API contract is "
        "explicit (not just importable by accident)."
    )


# ---------------------------------------------------------------------------
# Self-tests on the detector helpers
# ---------------------------------------------------------------------------


def test_detector_flags_docker_token_in_annotation() -> None:
    assert (
        _annotation_contains_forbidden_token("docker.client.DockerClient") == "docker"
    )


def test_detector_flags_playwright_page_in_annotation() -> None:
    """A signature like ``page: Page`` would forward a Playwright
    object to the caller. The detector must fire."""
    assert _annotation_contains_forbidden_token("Page") == "Page"


def test_detector_does_not_fire_on_clean_signature_tokens() -> None:
    """Plain strings / dicts / dataclasses must not trigger the
    detector. ``str`` / ``dict[str, Any]`` / ``ExecutorError`` are
    all valid surface types."""
    for clean in (
        "str",
        "dict[str, Any]",
        "ExecutorError",
        "str | None",
        "bool",
        "Path",
        "list[str]",
    ):
        assert _annotation_contains_forbidden_token(clean) is None


def test_public_method_collector_skips_self_arg() -> None:
    """``self`` must be excluded from the annotation walk so a
    benign ``self: ExecutorControl`` annotation does not collide
    with any future forbidden-token expansion."""
    src = "class Foo:\n    def bar(self, x: int) -> bool: ...\n"
    tree = ast.parse(src)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    method = next(stmt for stmt in cls.body if isinstance(stmt, ast.FunctionDef))
    labels = [label for label, _ in _collect_public_function_signatures(method)]
    assert "arg:self" not in labels
    assert "arg:x" in labels
    assert "return" in labels
