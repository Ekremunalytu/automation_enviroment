"""Architecture gate: AGENTS rule 6 — no generic ``except Exception`` (or bare
``except``) in production code.

AGENTS hard-rule 6 forbids broad exception swallowing in production paths;
narrow exception types (or letting the exception propagate) are required.
This gate codifies the rule by walking ``ast.ExceptHandler`` nodes across
``appcore/``, ``workflows/``, ``executor/``, ``packages/`` and rejecting any
handler whose ``type`` is ``None`` (bare ``except:``) or ``Name(id="Exception")``
(``except Exception:``).

Allowlist:
- ``tests/`` — not scanned (test fixtures legitimately use broad excepts to
  exercise error paths).
- ``scripts/`` — not scanned (one-off operator tooling, not on the production
  request/job paths).
- ``alembic/versions/`` — not scanned (auto-generated migration scaffolding).
- File-level pragma ``# arch-allow: thread-supervisor`` placed on the same
  line as the offending ``except`` for the future ``[FOLLOWUP
  analysis-thread-supervisor]`` landing site, where a daemon-thread
  ``BaseException`` supervisor is intentional and documented at the call
  site. Reserved for that one site only — do not sprinkle it elsewhere.

The only ``except Exception`` text inside production roots today lives
inside the module docstring at ``appcore/db/session.py`` (sample SQLAlchemy
session usage). That literal is invisible to ``ast.parse`` because it sits
inside a string node, so the gate naturally ignores it.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SCANNED_DIRS = ("appcore", "workflows", "executor", "packages", "static_runtime")
EXCLUDED_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
PRAGMA = "arch-allow: thread-supervisor"


def _module_label(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _is_bare_or_exception(handler: ast.ExceptHandler) -> bool:
    """True if the handler matches ``except:`` or ``except Exception:``.

    Both forms swallow the entire exception hierarchy below ``BaseException``
    (modulo ``KeyboardInterrupt`` / ``SystemExit`` for bare). AGENTS rule 6
    bans both in production code.
    """
    if handler.type is None:
        return True
    return isinstance(handler.type, ast.Name) and handler.type.id == "Exception"


def _pragma_lines(source: str) -> set[int]:
    return {
        lineno
        for lineno, line in enumerate(source.splitlines(), start=1)
        if PRAGMA in line
    }


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for top in SCANNED_DIRS:
        root = REPO_ROOT / top
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
                continue
            files.append(path)
    return files


def test_no_bare_except_exception_in_production_code() -> None:
    """No bare ``except`` or ``except Exception`` in production roots
    (AGENTS rule 6)."""
    violations: list[str] = []

    for module_path in _iter_python_files():
        rel = _module_label(module_path)
        source = module_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(module_path))
        except SyntaxError:
            continue

        pragma_at = _pragma_lines(source)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            if not _is_bare_or_exception(node):
                continue
            if node.lineno in pragma_at:
                continue
            violations.append(f"{rel}:{node.lineno}")

    assert not violations, (
        "AGENTS rule 6 violation — generic 'except:' or 'except Exception:' "
        "in production code. Use narrow exception types or let the exception "
        "propagate. Allow-list via '# arch-allow: thread-supervisor' is "
        "reserved for the planned [FOLLOWUP analysis-thread-supervisor] "
        "landing site only.\n  - " + "\n  - ".join(violations)
    )


def test_detector_flags_bare_except() -> None:
    """Self-test: bare ``except:`` must be flagged."""
    source = "try:\n    do_thing()\nexcept:\n    pass\n"
    tree = ast.parse(source)
    handlers = [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)]
    assert handlers and _is_bare_or_exception(handlers[0])


def test_detector_flags_except_exception() -> None:
    """Self-test: ``except Exception:`` must be flagged."""
    source = "try:\n    do_thing()\nexcept Exception:\n    pass\n"
    tree = ast.parse(source)
    handlers = [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)]
    assert handlers and _is_bare_or_exception(handlers[0])


def test_detector_ignores_narrow_exception_types() -> None:
    """False-positive guard: narrow exception types must NOT trigger."""
    benign_sources = [
        "try:\n    do_thing()\nexcept ValueError:\n    pass\n",
        "try:\n    do_thing()\nexcept (KeyError, TypeError):\n    pass\n",
        "try:\n    do_thing()\nexcept FileNotFoundError as exc:\n    raise\n",
    ]
    for src in benign_sources:
        tree = ast.parse(src)
        handlers = [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)]
        assert handlers, f"no ExceptHandler in synthetic source: {src!r}"
        assert not _is_bare_or_exception(handlers[0]), (
            f"detector false-fired on narrow except: {src!r}"
        )


def test_pragma_escapes_violation_on_same_line() -> None:
    """A ``# arch-allow: thread-supervisor`` pragma on the same line as the
    offending ``except`` must skip the violation. Without this the gate
    has no escape hatch for the planned daemon-thread supervisor site."""
    source = (
        "try:\n"
        "    run_thread()\n"
        "except Exception:  # arch-allow: thread-supervisor\n"
        "    log.exception('thread crashed')\n"
    )
    tree = ast.parse(source)
    pragma_at = _pragma_lines(source)
    offending: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not _is_bare_or_exception(node):
            continue
        if node.lineno in pragma_at:
            continue
        offending.append(node.lineno)
    assert offending == []


def test_pragma_two_lines_above_does_not_escape() -> None:
    """A pragma further than the same line must NOT skip the violation —
    only same-line annotations escape, otherwise an unrelated earlier
    comment could accidentally silence a real finding."""
    source = (
        "# arch-allow: thread-supervisor\n"
        "# unrelated intervening comment\n"
        "try:\n"
        "    run_thread()\n"
        "except Exception:\n"
        "    pass\n"
    )
    tree = ast.parse(source)
    pragma_at = _pragma_lines(source)
    offending: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not _is_bare_or_exception(node):
            continue
        if node.lineno in pragma_at:
            continue
        offending.append(node.lineno)
    assert offending == [5]
