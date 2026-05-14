"""Executor runtime build fingerprint emitted at the automation output
boundary (W14-5 sub-commit 3, closes
``[FOLLOWUP codex-automation-5]``).

Operators reviewing an activation report need to know **which executor
revision produced it** — version, build date, commit SHA — without
having to cross-reference a CI build log. The fingerprint stamps the
report at write time and the log emit pipeline (via
``LogContextFilter`` / ``LogRecord`` factory wiring in
``appcore.logging``) so a single scan's logs and report share the same
correlation key.

Sources, in priority order:

1. Build-time env var ``EXTRACE_BUILD_COMMIT_SHA`` (set by the
   Dockerfile ``ARG`` / ``ENV`` pair when the executor image is built
   in CI). This is the authoritative value when present — it survives
   the host → container boundary without any runtime ``git`` access.
2. Runtime ``git rev-parse HEAD`` (host context, defense-in-depth).
   Only used when the build-time env var is missing — e.g. local
   developer ``make exec-up`` boots that did not bake the SHA in.
3. ``"unknown"`` final fallback. The fingerprint never raises; an
   unresolvable commit collapses to the empty string so observability
   wiring (W14-5 sub-commit 2's ``LogContextFilter``) cannot break
   the emit pipeline.

Cached as a module-level immutable mapping. The first
``executor_fingerprint()`` call resolves once, subsequent calls return
the cached dict. ``_reset_fingerprint_cache()`` is a test-only hook.
"""

from __future__ import annotations

import datetime as _dt
import os
import subprocess
from pathlib import Path
from typing import Final

from executor.binary_paths import HostBinaryNotFoundError

# Python 3.10 executor compatibility: `datetime.UTC` arrived in Python 3.11.
# `getattr` keeps the import site valid on the older runtime, mirroring the
# established pattern in `packages/analysis_engine/runner.py`.
datetime = _dt.datetime
UTC = getattr(_dt, "UTC", _dt.timezone.utc)  # noqa: UP017

_BUILD_COMMIT_ENV_VAR: Final[str] = "EXTRACE_BUILD_COMMIT_SHA"
_BUILD_DATE_ENV_VAR: Final[str] = "EXTRACE_BUILD_DATE"
_BUILD_VERSION_ENV_VAR: Final[str] = "EXTRACE_BUILD_VERSION"
_UNKNOWN: Final[str] = "unknown"
_DEFAULT_VERSION: Final[str] = "extrace"
_REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

_cached_fingerprint: dict[str, str] | None = None


def _resolve_commit_sha_from_env() -> str | None:
    value = os.environ.get(_BUILD_COMMIT_ENV_VAR, "")
    return value.strip() or None


def _resolve_commit_sha_from_git() -> str | None:
    """Best-effort runtime ``git rev-parse HEAD`` against the repo root.

    Returns the short SHA (7 chars) on success, ``None`` on any
    failure mode: ``git`` binary missing, repo root is not a git
    checkout (e.g. inside the container image where ``.git`` is not
    copied), non-zero exit, or non-utf8 output. The fingerprint never
    raises — observability wiring must not crash on a missing SHA.
    """
    try:
        import shutil

        git_path = shutil.which("git")
    except (HostBinaryNotFoundError, OSError):
        return None
    if not git_path:
        return None
    try:
        result = subprocess.run(
            [git_path, "rev-parse", "--short", "HEAD"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    return sha or None


def _resolve_build_date() -> str:
    value = os.environ.get(_BUILD_DATE_ENV_VAR, "").strip()
    if value:
        return value
    return datetime.now(tz=UTC).date().isoformat()


def _resolve_version() -> str:
    return os.environ.get(_BUILD_VERSION_ENV_VAR, "").strip() or _DEFAULT_VERSION


def _build_fingerprint() -> dict[str, str]:
    commit = _resolve_commit_sha_from_env() or _resolve_commit_sha_from_git() or _UNKNOWN
    return {
        "commit_sha": commit,
        "build_date": _resolve_build_date(),
        "version": _resolve_version(),
    }


def executor_fingerprint() -> dict[str, str]:
    """Return the cached executor build fingerprint dict.

    First call resolves the sources and caches the result; subsequent
    calls return the cached mapping (cheap, no subprocess on the hot
    path).
    """
    global _cached_fingerprint
    if _cached_fingerprint is None:
        _cached_fingerprint = _build_fingerprint()
    return dict(_cached_fingerprint)


def executor_fingerprint_short() -> str:
    """Return the short fingerprint for ``LogContextFilter`` stamping —
    the commit SHA (already 7 chars from ``git rev-parse --short``
    when sourced runtime-side; up to first 7 chars when sourced from
    the env var)."""
    sha = executor_fingerprint()["commit_sha"]
    return sha[:7]


def _reset_fingerprint_cache() -> None:
    """Test-only hook: clear the lazily resolved fingerprint cache."""
    global _cached_fingerprint
    _cached_fingerprint = None


__all__ = [
    "executor_fingerprint",
    "executor_fingerprint_short",
]
