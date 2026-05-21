"""Import-graph architectural tests — cross-package isolation + runtime invocation patterns.

Split from tests/architecture/test_import_graph.py during W16-6 to reduce single-file size.
Covers: monitor/stimulus cross-import, playwright flat-file count limit, attribution eager-import,
python -m playwright invocations, runtime_capture extension_host facade.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]

_PACKAGES_BANNED_ROOTS = {"appcore", "executor", "ui", "workflows"}
_EXECUTOR_BANNED_ROOTS = {"appcore", "workflows"}
_WORKFLOW_ALLOWED_ROOTS = {"appcore", "packages", "workflows"}
_REPO_LOCAL_ROOTS = {
    path.name
    for path in REPO_ROOT.iterdir()
    if path.is_dir() and any(path.rglob("*.py"))
}.union({path.stem for path in REPO_ROOT.glob("*.py") if path.name != "__init__.py"})


def _iter_python_files(top_level_dir: str) -> list[Path]:
    return sorted((REPO_ROOT / top_level_dir).rglob("*.py"))


def _import_references(module_path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    references: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                references.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.level:
                continue
            for alias in node.names:
                references.append((node.lineno, f"{node.module}.{alias.name}"))
    return references


def _module_label(module_path: Path) -> str:
    return module_path.relative_to(REPO_ROOT).as_posix()


def test_monitor_and_stimulus_subpackages_do_not_cross_import() -> None:
    """W12-1: ``monitor/`` and ``stimulus/`` must not import from each other.

    The W12-1 subpackaging draws an explicit topology line: monitor
    observes runtime state, stimulus drives interactions; they share
    only via flat helpers (``automation``, ``triggers``, ...) at the
    parent level. A direct ``from ..stimulus import X`` inside
    ``monitor/`` (or vice versa) collapses that boundary and lets
    runtime-driver logic leak into the observer surface (or vice
    versa). This gate fails any PR that introduces such an import.
    """
    pairs = (
        ("executor/flows/playwright/monitor", "stimulus"),
        ("executor/flows/playwright/stimulus", "monitor"),
    )
    violations: list[str] = []
    for subpkg_dir, banned in pairs:
        for module_path in _iter_python_files(subpkg_dir):
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                if node.level == 2 and node.module == banned:
                    violations.append(
                        f"{_module_label(module_path)}:{node.lineno} "
                        f"imports from ..{banned}"
                    )
                # Also detect `from ..banned.sub import ...` forms.
                if (
                    node.level == 2
                    and node.module is not None
                    and node.module.split(".", 1)[0] == banned
                ):
                    violations.append(
                        f"{_module_label(module_path)}:{node.lineno} "
                        f"imports from ..{node.module}"
                    )

    # De-duplicate (a single ImportFrom can match both branches above).
    deduped = sorted(set(violations))
    assert not deduped, (
        "monitor/ and stimulus/ subpackages must not import each other "
        "(W12-1 topology). Share via flat parent helpers instead:\n"
        + "\n".join(deduped)
    )


def test_executor_playwright_flat_file_count_limit() -> None:
    """W12-1: ``executor/flows/playwright/`` must keep at most 10 flat ``.py``.

    The W12-1 refactor exit criterion is "≤10 flat files at the top of the
    playwright tree". The current 10 are: ``__init__``, ``annotation``,
    ``automation``, ``capture``, ``reload_vscode``, ``report_builder``,
    ``reset_state``, ``triggers``, ``uri_validation``, ``wait_helpers``.
    ``reload_vscode`` and ``reset_state`` are intentionally flat because
    ``appcore/api/config.py`` and ``executor/config.py`` reference them as
    subprocess module paths (string-based). New additions belong in a
    subpackage (monitor/, stimulus/, workspace/, health/, entrypoint/,
    vscode/, signals/, attribution/), not at the top level — this gate
    fails any PR that grows the flat budget past 10.
    """
    flat_files = sorted(
        path.name for path in (REPO_ROOT / "executor/flows/playwright").glob("*.py")
    )
    assert len(flat_files) <= 10, (
        f"executor/flows/playwright/ flat .py count exceeded the W12-1 budget "
        f"({len(flat_files)} > 10). Move new modules into a subpackage. "
        f"Current flat files: {flat_files}"
    )


def test_attribution_does_not_eagerly_import_monitor() -> None:
    """W12-1: ``attribution/__init__.py`` must defer ``monitor`` imports.

    The symmetric counterpart to
    ``test_monitor_facade_does_not_eagerly_import_attribution``. Attribution
    needs ``RiskSignal`` (defined in ``monitor.records``) at runtime inside
    ``build_risk_signals``; if that import is hoisted to the module top
    level it re-creates the cycle (``attribution`` → ``monitor.records`` →
    ``monitor/__init__`` → attribution proxy lookup), since
    ``monitor/__init__.py`` runs eagerly when any ``monitor.<sub>`` module
    is loaded. This gate scans only ``tree.body`` so the lazy import inside
    ``build_risk_signals`` (a nested ``ImportFrom`` reachable via
    ``ast.walk`` but not via direct ``tree.body`` iteration) is correctly
    ignored. Any future PR that moves ``from ..monitor[...] import ...`` to
    the top level fails here.
    """
    facade = REPO_ROOT / "executor/flows/playwright/attribution/__init__.py"
    tree = ast.parse(facade.read_text(encoding="utf-8"))

    violations: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level != 2 or node.module is None:
            continue
        # Ignore TYPE_CHECKING blocks: those are nested under an ast.If, not
        # at tree.body — they won't reach this loop.
        head = node.module.split(".", 1)[0]
        if head == "monitor":
            violations.append(f"line {node.lineno}: from ..{node.module} import ...")

    assert not violations, (
        "attribution/__init__.py imports from monitor at module top level — "
        "this re-creates the W12-1 attribution↔monitor cycle. Keep the "
        "RiskSignal (and any other monitor.records) import inside the "
        "_build_risk_signals function body, or guard it with TYPE_CHECKING "
        "for type-only references:\n" + "\n".join(violations)
    )


def test_python_m_playwright_invocations_have_main_module() -> None:
    """W12-1: every ``python -m executor.flows.playwright.<X>`` target must
    resolve to a runnable module.

    The W12-1 flat→package conversion silently broke
    ``executor/container/start.sh:89``: the container boot ran
    ``python3 -m executor.flows.playwright.workspace``, but after the
    conversion ``workspace`` is a package without a ``__main__.py``, and
    Python's ``-m`` semantics look for ``__main__.py`` (the
    ``if __name__ == "__main__"`` block in ``__init__.py`` is dead under
    ``-m``). The container failed to boot with ``No module named
    ...workspace.__main__`` — caught only after W12-1 landed.

    This gate scans every ``python -m executor.flows.playwright.<X>``
    invocation in the runtime tree (start.sh, settings defaults, host
    wrappers) and asserts each ``<X>`` is either:

    1. A flat module ``executor/flows/playwright/<X>.py``, **or**
    2. A package ``executor/flows/playwright/<X>/__main__.py``.

    A future PR that converts another flat module to a package without
    adding ``__main__.py`` fails this gate before it can break boot.
    """
    playwright_root = REPO_ROOT / "executor/flows/playwright"

    targets: set[tuple[str, str]] = set()  # (module_name, source_label)

    # 1. start.sh and any other shell script in the container tree.
    for shell_script in (REPO_ROOT / "executor/container").rglob("*.sh"):
        text = shell_script.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in re.finditer(
                r"python[0-9.]*\s+-m\s+executor\.flows\.playwright\.([A-Za-z_][A-Za-z_0-9]*)",
                line,
            ):
                targets.add(
                    (match.group(1), f"{shell_script.relative_to(REPO_ROOT)}:{line_no}")
                )

    # 2. Settings module defaults (`appcore/api/config.py`,
    #    `executor/config.py`). These literals get fed to
    #    `subprocess.run([..., "-m", value, ...])` at runtime in
    #    `executor/host.py`, so the same -m semantics apply.
    for settings_file in (
        REPO_ROOT / "appcore/api/config.py",
        REPO_ROOT / "executor/config.py",
    ):
        text = settings_file.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in re.finditer(
                r'"executor\.flows\.playwright\.([A-Za-z_][A-Za-z_0-9]*)"',
                line,
            ):
                targets.add(
                    (
                        match.group(1),
                        f"{settings_file.relative_to(REPO_ROOT)}:{line_no}",
                    )
                )

    assert targets, (
        "test scaffolding regression: scan found zero `python -m "
        "executor.flows.playwright.<X>` targets. Either the patterns are "
        "too narrow or the runtime tree no longer drives the executor "
        "this way."
    )

    violations: list[str] = []
    for module_name, source_label in sorted(targets):
        flat_path = playwright_root / f"{module_name}.py"
        package_main = playwright_root / module_name / "__main__.py"
        if flat_path.exists():
            continue
        if package_main.exists():
            continue
        violations.append(
            f"{source_label} runs `python -m executor.flows.playwright."
            f"{module_name}` but neither {module_name}.py nor "
            f"{module_name}/__main__.py exists. Add {module_name}/"
            "__main__.py (a one-line shim that delegates to the package's "
            "entry function), or change the invocation."
        )

    assert not violations, (
        "executor/flows/playwright/ has `python -m` targets that won't "
        "boot — Python's -m semantics need __main__.py for packages, not "
        'the __init__.py-level `if __name__ == "__main__"` guard:\n'
        + "\n".join(violations)
    )


def test_runtime_capture_extension_host_stays_a_thin_facade() -> None:
    """W12-5: ``runtime_capture/extension_host.py`` must remain re-export only.

    The original 679-LoC module bundled three responsibilities — log parsing,
    strace parsing, and capture orchestration. After the W12-5 split those
    live in ``extension_host_log_parse.py``, ``extension_host_strace_parse.py``,
    and ``extension_host_capture.py``. The facade survives because:

    - ``monitor/__init__.py`` re-exports 7 names from this path
    - ``monitor/sources.py`` imports 2 names from this path
    - the 23-case W11 precursor suite
      (``tests/executor/test_playwright_extension_host.py``) accesses
      9 names via attribute lookup on the imported module.

    Future logic must land in the focused modules, not here.
    """
    facade = REPO_ROOT / "executor/flows/playwright/runtime_capture/extension_host.py"
    tree = ast.parse(facade.read_text(encoding="utf-8"))

    allowed_node_types: tuple[type[ast.AST], ...] = (
        ast.Import,
        ast.ImportFrom,
    )
    violations: list[str] = []
    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
        ):
            continue
        if isinstance(node, allowed_node_types):
            continue
        violations.append(f"line {node.lineno}: {type(node).__name__}")

    assert not violations, (
        "executor/flows/playwright/runtime_capture/extension_host.py must stay "
        "a thin re-export facade (W12-5 ahtapot closure invariant). Move new "
        "logic into extension_host_log_parse.py, extension_host_strace_parse.py, "
        "or extension_host_capture.py:\n" + "\n".join(violations)
    )


def test_runtime_capture_extension_host_reexports_match_canonical_modules() -> None:
    """W12-5: every name in ``extension_host.__all__`` must come from the focused modules.

    Pins the contract that the facade's re-exported set is exactly what
    ``extension_host_log_parse.py``, ``extension_host_strace_parse.py``,
    ``extension_host_capture.py`` and ``_shared.py`` provide — no orphan
    re-exports, no shim-wrapped versions of public symbols.
    """
    from executor.flows.playwright.runtime_capture import (
        _shared,
        extension_host,
        extension_host_capture,
        extension_host_log_parse,
        extension_host_strace_parse,
    )

    expected_in_log_parse = {
        "_ACTIVATION_PATTERNS",
        "_LIFECYCLE_MARKER_PATTERNS",
        "_TIMESTAMP_RE",
        "_activation_within_monitoring_window",
        "_parse_activation_lines",
        "find_exthost_logs",
        "parse_activations_from_log",
        "parse_activations_from_output",
        "parse_all_exthost_logs",
        "read_extension_host_output",
    }
    expected_in_strace_parse = {
        "_PROCESS_EVENT_RE",
        "parse_strace_process_event_line",
    }
    expected_in_capture = {
        "ExtensionHostFileCapture",
        "_poll_exthost_log",
        "watch_exthost_log",
    }
    expected_in_shared = {
        "VSCODE_LOGS_DIR",
        "_parse_iso_timestamp",
    }

    union = (
        expected_in_log_parse
        | expected_in_strace_parse
        | expected_in_capture
        | expected_in_shared
    )
    assert set(extension_host.__all__) == union, (
        "extension_host.__all__ must equal the union of the canonical modules' "
        f"public sets. Got: {set(extension_host.__all__)}, expected: {union}"
    )

    for name in expected_in_log_parse:
        assert getattr(extension_host, name) is getattr(
            extension_host_log_parse, name
        ), (
            f"extension_host.{name} must be the same object as "
            f"extension_host_log_parse.{name} (W12-5 re-export invariant)."
        )
    for name in expected_in_strace_parse:
        assert getattr(extension_host, name) is getattr(
            extension_host_strace_parse, name
        ), (
            f"extension_host.{name} must be the same object as "
            f"extension_host_strace_parse.{name} (W12-5 re-export invariant)."
        )
    for name in expected_in_capture:
        assert getattr(extension_host, name) is getattr(extension_host_capture, name), (
            f"extension_host.{name} must be the same object as "
            f"extension_host_capture.{name} (W12-5 re-export invariant)."
        )
    for name in expected_in_shared:
        assert getattr(extension_host, name) is getattr(_shared, name), (
            f"extension_host.{name} must be the same object as "
            f"_shared.{name} (W12-5 re-export invariant)."
        )
