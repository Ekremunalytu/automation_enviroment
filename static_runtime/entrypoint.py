"""Static analysis pre-check container entrypoint (ES-3a runner, ADR 0016).

Runs INSIDE the hardened ``automation_static_analyzer`` container, invoked as
``python -m static_runtime`` (see ``__main__``). ES-3a wires the in-house rule
runner (``static_runtime.static_runner.run_static_detection_engine``) behind the
ES-2 flag surface + on-disk JSON contract, both frozen at the container boundary
so the host-orchestration call site (``executor/static_host.py``) is unchanged.

Imports are intentionally confined to ``packages.analysis_contracts`` +
``static_runtime`` — the hardened image carries ``packages/analysis_contracts/``
+ ``static_runtime/`` and NOT the dynamic ``packages.analysis_engine`` engine.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from packages.analysis_contracts.static_detection import StaticDetectionReport
from static_runtime.static_runner import run_static_detection_engine


def build_parser() -> argparse.ArgumentParser:
    """Build the static-runtime CLI parser.

    The four flags form the stable invocation contract that the host
    orchestration (``executor/static_host.py``) drives the container with;
    ES-3a fills in the runner behind them without reshaping the surface.
    """
    parser = argparse.ArgumentParser(
        prog="static_runtime",
        description="Static analysis pre-check runner (ES-2 stub).",
    )
    parser.add_argument(
        "--vsix-dir",
        required=True,
        help="Container-side path to the decompressed VSIX extraction root.",
    )
    parser.add_argument(
        "--report-path",
        required=True,
        help="Container-side path to write the StaticDetectionReport JSON.",
    )
    parser.add_argument(
        "--rules-version",
        required=True,
        help="Version string for the static rule set (recorded in the report).",
    )
    parser.add_argument(
        "--timeout-budget-s",
        required=True,
        type=int,
        help="Soft wall-clock budget (seconds) for the static pass.",
    )
    # W26 / Stream 3 (B5, ADR 0016 amendment): additive 5th flag — the SHA-256 of
    # the analyzed .vsix archive, recorded in the StaticDetectionReport so the
    # static output is bound to the same bytes the dynamic report carries.
    # Optional/defaulted ("") so the frozen 4-flag invocation stays callable.
    parser.add_argument(
        "--vsix-sha256",
        required=False,
        default="",
        help="SHA-256 of the analyzed .vsix archive (B5 provenance).",
    )
    return parser


def run_static_detection(
    *,
    vsix_dir: str,
    report_path: str,
    rules_version: str,
    timeout_budget_s: int,
    vsix_sha256: str = "",
) -> StaticDetectionReport:
    """Produce a static detection report and persist it to ``report_path``.

    Runs the in-house rule engine over ``vsix_dir`` and writes the resulting
    ``StaticDetectionReport`` JSON to ``report_path`` (parent dirs created). The
    signature + on-disk JSON shape are the ES-2 contract; ES-3a swapped in the
    real runner; W26 adds the additive ``vsix_sha256`` provenance (ADR 0016).
    """
    report = run_static_detection_engine(
        vsix_dir=vsix_dir,
        rules_version=rules_version,
        timeout_budget_s=timeout_budget_s,
        vsix_sha256=vsix_sha256,
    )
    destination = Path(report_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report.model_dump_json(), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_static_detection(
        vsix_dir=args.vsix_dir,
        report_path=args.report_path,
        rules_version=args.rules_version,
        timeout_budget_s=args.timeout_budget_s,
        vsix_sha256=args.vsix_sha256,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
