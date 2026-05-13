"""W14-5 sub-commit 3 — behavioral coverage for
``executor.runtime_fingerprint``.

Closes ``[FOLLOWUP codex-automation-5]`` (executor runtime fingerprint
in automation output). Pins source priority (env var primary, runtime
``git`` fallback, ``unknown`` final fallback), caching idempotency,
and the short-form shape used by the W14-5 log emit filter.
"""

from __future__ import annotations

import subprocess
from types import SimpleNamespace
from typing import Any

import pytest

from executor import runtime_fingerprint as rf


@pytest.fixture(autouse=True)
def _clear_fingerprint_cache():
    rf._reset_fingerprint_cache()
    yield
    rf._reset_fingerprint_cache()


# ---------------------------------------------------------------------------
# Source priority
# ---------------------------------------------------------------------------


def test_commit_sha_resolves_from_env_var_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(rf._BUILD_COMMIT_ENV_VAR, "deadbeef")
    fp = rf.executor_fingerprint()
    assert fp["commit_sha"] == "deadbeef"


def test_commit_sha_falls_back_to_git_when_env_var_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(rf._BUILD_COMMIT_ENV_VAR, raising=False)

    def _fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return SimpleNamespace(
            returncode=0, stdout="cafebabe\n", stderr=""
        )  # type: ignore[return-value]

    monkeypatch.setattr(rf.subprocess, "run", _fake_run)
    fp = rf.executor_fingerprint()
    assert fp["commit_sha"] == "cafebabe"


def test_commit_sha_falls_back_to_unknown_when_git_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(rf._BUILD_COMMIT_ENV_VAR, raising=False)

    def _fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("git not on PATH")

    monkeypatch.setattr(rf.subprocess, "run", _fake_run)

    def _fake_which(_name: str) -> str | None:
        return "/usr/bin/git"

    monkeypatch.setattr(rf, "executor_fingerprint", rf.executor_fingerprint)
    import shutil as _shutil

    monkeypatch.setattr(_shutil, "which", _fake_which)
    fp = rf.executor_fingerprint()
    assert fp["commit_sha"] == rf._UNKNOWN


def test_commit_sha_falls_back_to_unknown_when_git_returns_nonzero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(rf._BUILD_COMMIT_ENV_VAR, raising=False)

    def _fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return SimpleNamespace(
            returncode=128, stdout="", stderr="fatal: not a git repo"
        )  # type: ignore[return-value]

    monkeypatch.setattr(rf.subprocess, "run", _fake_run)
    fp = rf.executor_fingerprint()
    assert fp["commit_sha"] == rf._UNKNOWN


def test_commit_sha_falls_back_to_unknown_when_git_times_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(rf._BUILD_COMMIT_ENV_VAR, raising=False)

    def _fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=5)

    monkeypatch.setattr(rf.subprocess, "run", _fake_run)
    fp = rf.executor_fingerprint()
    assert fp["commit_sha"] == rf._UNKNOWN


# ---------------------------------------------------------------------------
# Shape + cache
# ---------------------------------------------------------------------------


def test_fingerprint_dict_has_three_required_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(rf._BUILD_COMMIT_ENV_VAR, "abc1234")
    fp = rf.executor_fingerprint()
    assert set(fp.keys()) == {"commit_sha", "build_date", "version"}


def test_build_date_resolves_from_env_var_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(rf._BUILD_COMMIT_ENV_VAR, "abc1234")
    monkeypatch.setenv(rf._BUILD_DATE_ENV_VAR, "2026-05-13")
    fp = rf.executor_fingerprint()
    assert fp["build_date"] == "2026-05-13"


def test_version_resolves_from_env_var_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(rf._BUILD_COMMIT_ENV_VAR, "abc1234")
    monkeypatch.setenv(rf._BUILD_VERSION_ENV_VAR, "extrace-1.0-rc4")
    fp = rf.executor_fingerprint()
    assert fp["version"] == "extrace-1.0-rc4"


def test_version_defaults_to_extrace_when_env_var_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(rf._BUILD_COMMIT_ENV_VAR, "abc1234")
    monkeypatch.delenv(rf._BUILD_VERSION_ENV_VAR, raising=False)
    fp = rf.executor_fingerprint()
    assert fp["version"] == rf._DEFAULT_VERSION


def test_fingerprint_caches_after_first_resolve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The first call resolves; subsequent calls return the cached
    dict without re-running git."""
    monkeypatch.setenv(rf._BUILD_COMMIT_ENV_VAR, "first-sha")
    first = rf.executor_fingerprint()
    monkeypatch.setenv(rf._BUILD_COMMIT_ENV_VAR, "second-sha")
    second = rf.executor_fingerprint()
    assert first["commit_sha"] == "first-sha"
    assert second["commit_sha"] == "first-sha", (
        "cached fingerprint must not pick up env changes after the "
        "first resolve; explicit cache reset is required."
    )


def test_fingerprint_returns_copy_so_caller_cannot_mutate_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(rf._BUILD_COMMIT_ENV_VAR, "abc1234")
    fp = rf.executor_fingerprint()
    fp["commit_sha"] = "tampered"
    fresh = rf.executor_fingerprint()
    assert fresh["commit_sha"] == "abc1234"


# ---------------------------------------------------------------------------
# Short-form
# ---------------------------------------------------------------------------


def test_executor_fingerprint_short_returns_seven_chars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(rf._BUILD_COMMIT_ENV_VAR, "deadbeefcafebabe1234567890")
    short = rf.executor_fingerprint_short()
    assert short == "deadbee"


def test_executor_fingerprint_short_collapses_unknown_to_seven_chars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``"unknown"`` is 7 chars exactly — short-form preserves it."""
    monkeypatch.delenv(rf._BUILD_COMMIT_ENV_VAR, raising=False)

    def _fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return SimpleNamespace(returncode=128, stdout="", stderr="")  # type: ignore[return-value]

    monkeypatch.setattr(rf.subprocess, "run", _fake_run)
    short = rf.executor_fingerprint_short()
    assert short == rf._UNKNOWN[:7]
