"""Static analysis pre-check container entrypoint (ES-2 stub, ADR 0016).

Runs INSIDE the hardened ``automation_static_analyzer`` container, invoked as
``python -m static_runtime`` (see ``__main__``). ES-2 is **scaffold only**: it
writes an *empty* ``StaticDetectionReport`` to ``--report-path``. The real
in-house rules + runner land at ES-3a (mirroring
``packages.analysis_engine.runner.run_detection``) behind this same flag
surface and on-disk JSON contract, so the container boundary and the
host-orchestration call site can be stood up and smoke-tested first.

Imports are intentionally confined to
``packages.analysis_contracts.static_detection`` (pydantic-only closure) — the
hardened image carries ``packages/analysis_contracts/`` + ``static_runtime/``
and NOT the dynamic ``packages.analysis_engine`` engine.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from packages.analysis_contracts.static_detection import StaticDetectionReport


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
    return parser


def run_static_detection(
    *,
    vsix_dir: str,
    report_path: str,
    rules_version: str,
    timeout_budget_s: int,
) -> StaticDetectionReport:
    """Produce a static detection report and persist it to ``report_path``.

    ES-2 stub: emits an *empty* ``StaticDetectionReport`` (no findings, no
    tool executions). ES-3a replaces the body with the in-house rule runner
    while keeping this signature + the on-disk JSON contract stable.

    ``vsix_dir`` / ``rules_version`` / ``timeout_budget_s`` are accepted now so
    the invocation contract is frozen at the container boundary; the stub does
    not yet read them.
    """
    report = StaticDetectionReport()
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
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
