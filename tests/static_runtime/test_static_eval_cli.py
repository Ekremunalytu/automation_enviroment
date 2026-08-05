"""Container-only evaluator CLI boundary and timeout validation."""

from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess

import pytest

from scripts import static_eval
from static_runtime import evaluation


def test_host_launcher_uses_fixed_container_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[list[str]] = []

    def fake_run(argv: list[str], *, check: bool) -> CompletedProcess[str]:
        assert check is False
        captured.append(argv)
        return CompletedProcess(argv, 0)

    monkeypatch.setattr(static_eval, "docker_path", lambda: "/usr/bin/docker")
    monkeypatch.setattr(static_eval.subprocess, "run", fake_run)

    assert static_eval.main(["--split", "holdout", "--timeout-budget-s", "17"]) == 0
    assert captured == [
        [
            "/usr/bin/docker",
            "exec",
            "-e",
            "PYTHONUNBUFFERED=1",
            "automation_static_analyzer",
            "python3",
            "-m",
            "static_runtime.evaluation",
            "--manifest",
            "/evaluation-corpus/manifest.json",
            "--corpus-root",
            "/evaluation-corpus/samples",
            "--output-json",
            "/results/static-evaluation/holdout.json",
            "--output-markdown",
            "/results/static-evaluation/holdout.md",
            "--split",
            "holdout",
            "--timeout-budget-s",
            "17",
        ]
    ]


@pytest.mark.parametrize("budget", ["0", "-1", "4", "601"])
def test_host_launcher_rejects_out_of_bounds_timeout_budget(budget: str) -> None:
    with pytest.raises(SystemExit, match="2"):
        static_eval.main(["--split", "tuning", "--timeout-budget-s", budget])


@pytest.mark.parametrize("budget", ["0", "-1", "4", "601"])
def test_container_runtime_rejects_out_of_bounds_timeout_budget(
    budget: str,
    tmp_path: Path,
) -> None:
    with pytest.raises(SystemExit, match="2"):
        evaluation.main(
            [
                "--manifest",
                str(tmp_path / "manifest.json"),
                "--corpus-root",
                str(tmp_path / "samples"),
                "--output-json",
                str(tmp_path / "result.json"),
                "--output-markdown",
                str(tmp_path / "result.md"),
                "--split",
                "all",
                "--timeout-budget-s",
                budget,
            ]
        )
