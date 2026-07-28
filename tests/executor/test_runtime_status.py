"""Read-only Docker runtime status normalization tests."""

from __future__ import annotations

import subprocess
from typing import Any

import pytest

from executor import binary_paths, runtime_status


@pytest.fixture
def fake_docker(monkeypatch: pytest.MonkeyPatch) -> str:
    binary_paths._reset_docker_path_cache()
    fake = "/fake/abs/docker"
    monkeypatch.setattr(binary_paths.shutil, "which", lambda _name: fake)
    return fake


def test_inspect_container_runtime_returns_measured_state(
    fake_docker: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout=(
                '{"Status":"running","Running":true,"OOMKilled":false,'
                '"ExitCode":0,"StartedAt":"2026-07-28T10:00:00Z",'
                '"FinishedAt":"","Health":{"Status":"healthy"}}'
            ),
            stderr="",
        )

    monkeypatch.setattr(runtime_status.subprocess, "run", fake_run)

    state = runtime_status.inspect_container_runtime("automation_executor")

    assert state.status == "running"
    assert state.health == "healthy"
    assert state.running is True
    assert state.exit_code == 0
    assert captured["argv"] == [
        fake_docker,
        "inspect",
        "--format",
        "{{json .State}}",
        "automation_executor",
    ]
    assert captured["kwargs"]["check"] is False
    assert captured["kwargs"].get("shell", False) is False


def test_inspect_container_runtime_degrades_without_exposing_daemon_output(
    fake_docker: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runtime_status.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [],
            1,
            stdout="",
            stderr="sensitive daemon detail",
        ),
    )

    state = runtime_status.inspect_container_runtime("automation_executor")

    assert state.status == "unknown"
    assert state.error == "Container unavailable"
    assert "sensitive" not in str(state)


def test_inspect_container_runtime_marks_missing_healthcheck_as_not_configured(
    fake_docker: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runtime_status.subprocess,
        "run",
        lambda argv, **_kwargs: subprocess.CompletedProcess(
            argv,
            0,
            stdout=(
                '{"Status":"running","Running":true,"OOMKilled":false,'
                '"ExitCode":0,"StartedAt":"2026-07-28T10:00:00Z",'
                '"FinishedAt":""}'
            ),
            stderr="",
        ),
    )

    state = runtime_status.inspect_container_runtime("automation_executor")

    assert state.running is True
    assert state.health == "not-configured"
    assert state.error is None


def test_inspect_container_runtime_normalizes_timeout(
    fake_docker: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def time_out(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["docker", "inspect"], timeout=5)

    monkeypatch.setattr(runtime_status.subprocess, "run", time_out)

    state = runtime_status.inspect_container_runtime("automation_executor")

    assert state.status == "unknown"
    assert state.health == "unknown"
    assert state.error == "Docker inspection timed out"
