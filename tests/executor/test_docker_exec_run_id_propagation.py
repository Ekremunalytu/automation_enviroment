"""W14-5 sub-commit 2 — behavioral coverage for ``EXTRACE_EPOCH_RUN_ID``
propagation across the docker exec boundary.

Closes ``[FOLLOWUP codex-2026-05-10-M5-epoch-docker-exec-propagation]``
as the natural byproduct of run-ID stamping (W14-5 §11.10 GOAL).
Pre-W14-5 the host-side ``EXTRACE_EPOCH_RUN_ID`` env var (consumed by
``executor/flows/playwright/stimulus/attempts.py:452`` for W8-0 harness
staleness checks) never reached the executor container's exec
environment — the container side could not stamp the same run-ID on
its log emit, so operator log correlation across the docker exec
boundary required manual timestamp / pid matching.

The W14-5 fix in ``executor.host._run_docker_exec`` forwards the host
env var as an additional ``-e EXTRACE_EPOCH_RUN_ID=<value>`` entry
when the host process has it set. Empty / unset values are not
forwarded (no spurious ``-e EXTRACE_EPOCH_RUN_ID=`` arg).
"""

from __future__ import annotations

import subprocess
from types import SimpleNamespace
from typing import Any

import pytest

from executor import host as host_module


def _capture_subprocess_run(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Replace ``subprocess.run`` with a recorder that captures the argv
    of every ``_run_docker_exec`` invocation. Returns a list that
    accumulates one entry per call."""
    captured: list[list[str]] = []

    def _fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args")
        captured.append(list(cmd))
        return SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        )  # type: ignore[return-value]

    monkeypatch.setattr(host_module.subprocess, "run", _fake_run)
    monkeypatch.setattr(host_module, "docker_path", lambda: "/usr/local/bin/docker")
    return captured


def _env_pairs_from_argv(argv: list[str]) -> dict[str, str]:
    """Extract every ``-e KEY=VALUE`` pair from a docker exec argv."""
    pairs: dict[str, str] = {}
    i = 0
    while i < len(argv) - 1:
        if argv[i] == "-e":
            key, _, value = argv[i + 1].partition("=")
            pairs[key] = value
            i += 2
            continue
        i += 1
    return pairs


def test_docker_exec_propagates_extrace_epoch_run_id_when_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EXTRACE_EPOCH_RUN_ID", "epoch-2026-05-13-abcdef")
    captured = _capture_subprocess_run(monkeypatch)

    host_module._run_docker_exec(
        ["echo", "hello"],
        timeout=5,
        allow_partial=False,
    )

    assert len(captured) == 1
    env_pairs = _env_pairs_from_argv(captured[0])
    assert env_pairs.get("EXTRACE_EPOCH_RUN_ID") == "epoch-2026-05-13-abcdef"


def test_docker_exec_omits_extrace_epoch_run_id_arg_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("EXTRACE_EPOCH_RUN_ID", raising=False)
    captured = _capture_subprocess_run(monkeypatch)

    host_module._run_docker_exec(
        ["echo", "hello"],
        timeout=5,
        allow_partial=False,
    )

    env_pairs = _env_pairs_from_argv(captured[0])
    assert "EXTRACE_EPOCH_RUN_ID" not in env_pairs


def test_docker_exec_omits_extrace_epoch_run_id_arg_when_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty env var must not produce a spurious ``-e EXTRACE_EPOCH_RUN_ID=``
    arg — the propagation is conditional on a non-empty value."""
    monkeypatch.setenv("EXTRACE_EPOCH_RUN_ID", "")
    captured = _capture_subprocess_run(monkeypatch)

    host_module._run_docker_exec(
        ["echo", "hello"],
        timeout=5,
        allow_partial=False,
    )

    env_pairs = _env_pairs_from_argv(captured[0])
    assert "EXTRACE_EPOCH_RUN_ID" not in env_pairs


def test_docker_exec_propagates_alongside_extra_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run-ID propagation must coexist with the existing W13-11
    ``EXECUTOR_HARNESS_PYTHON_SECRET_VALUE`` plumbing."""
    monkeypatch.setenv("EXTRACE_EPOCH_RUN_ID", "epoch-coexist")
    captured = _capture_subprocess_run(monkeypatch)

    host_module._run_docker_exec(
        ["echo", "hello"],
        timeout=5,
        allow_partial=False,
        extra_env={"EXECUTOR_HARNESS_PYTHON_SECRET_VALUE": "deadbeefcafe" * 4},
    )

    env_pairs = _env_pairs_from_argv(captured[0])
    assert env_pairs.get("EXTRACE_EPOCH_RUN_ID") == "epoch-coexist"
    assert env_pairs.get("EXECUTOR_HARNESS_PYTHON_SECRET_VALUE") == "deadbeefcafe" * 4


def test_docker_exec_run_id_precedes_extra_env_in_argv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deterministic argv ordering: the W14-5 run-ID propagation must
    appear before caller-supplied ``extra_env`` entries, which
    themselves appear after the existing ``PYTHONUNBUFFERED=1`` head.
    This pins the order so downstream log parsers that key off
    position do not silently regress when env keys are reordered.
    """
    monkeypatch.setenv("EXTRACE_EPOCH_RUN_ID", "epoch-ordering")
    captured = _capture_subprocess_run(monkeypatch)

    host_module._run_docker_exec(
        ["echo", "hello"],
        timeout=5,
        allow_partial=False,
        extra_env={"FOO": "1", "BAR": "2"},
    )

    argv = captured[0]
    # Locate the positions of each -e KEY=... value.
    positions: dict[str, int] = {}
    for i, word in enumerate(argv):
        if word == "-e" and i + 1 < len(argv):
            key, _, _value = argv[i + 1].partition("=")
            positions.setdefault(key, i)

    assert positions["PYTHONUNBUFFERED"] < positions["EXTRACE_EPOCH_RUN_ID"]
    assert positions["EXTRACE_EPOCH_RUN_ID"] < positions["FOO"]
    assert positions["EXTRACE_EPOCH_RUN_ID"] < positions["BAR"]


def test_docker_exec_does_not_forward_other_extrace_env_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The propagation is targeted to ``EXTRACE_EPOCH_RUN_ID`` only — a
    future env var named ``EXTRACE_FOO`` must not leak across the
    docker exec boundary unless the caller passes it via ``extra_env``.
    """
    monkeypatch.setenv("EXTRACE_EPOCH_RUN_ID", "epoch-scoped")
    monkeypatch.setenv("EXTRACE_FOO", "should-not-leak")
    monkeypatch.setenv("EXTRACE_BAR_INTERNAL", "should-not-leak")
    captured = _capture_subprocess_run(monkeypatch)

    host_module._run_docker_exec(
        ["echo", "hello"],
        timeout=5,
        allow_partial=False,
    )

    env_pairs = _env_pairs_from_argv(captured[0])
    assert "EXTRACE_EPOCH_RUN_ID" in env_pairs
    assert "EXTRACE_FOO" not in env_pairs
    assert "EXTRACE_BAR_INTERNAL" not in env_pairs
