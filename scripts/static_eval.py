"""Host launcher for the container-only SMF evaluator."""

from __future__ import annotations

import argparse

# Fixed Docker argv only; no shell or user-selected binary.
import subprocess  # nosec B404

from executor.binary_paths import docker_path
from packages.analysis_contracts.static_detection import (
    STATIC_ANALYSIS_DEFAULT_TIMEOUT_BUDGET_S,
    parse_static_analysis_timeout_budget,
)

_CONTAINER = "automation_static_analyzer"


def _positive_timeout_budget(value: str) -> int:
    try:
        return parse_static_analysis_timeout_budget(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="static-eval")
    parser.add_argument("--split", choices=("tuning", "holdout", "all"), required=True)
    parser.add_argument(
        "--timeout-budget-s",
        type=_positive_timeout_budget,
        default=STATIC_ANALYSIS_DEFAULT_TIMEOUT_BUDGET_S,
    )
    args = parser.parse_args(argv)
    completed = subprocess.run(  # noqa: S603  # nosec B603
        [
            docker_path(),
            "exec",
            "-e",
            "PYTHONUNBUFFERED=1",
            _CONTAINER,
            "python3",
            "-m",
            "static_runtime.evaluation",
            "--manifest",
            "/evaluation-corpus/manifest.json",
            "--corpus-root",
            "/evaluation-corpus/samples",
            "--output-json",
            f"/results/static-evaluation/{args.split}.json",
            "--output-markdown",
            f"/results/static-evaluation/{args.split}.md",
            "--split",
            args.split,
            "--timeout-budget-s",
            str(args.timeout_budget_s),
        ],
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
