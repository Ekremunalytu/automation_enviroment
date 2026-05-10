"""CLI parsing helpers for the Playwright executor entrypoint."""

from __future__ import annotations

import argparse


def build_parser(*, default_report_path: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VS Code automation via Playwright")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--demo", action="store_true", help="Run quick demo only")
    group.add_argument("--scenario", type=str, help="Run a single scenario by name")
    group.add_argument("--list", action="store_true", help="List available scenarios")
    parser.add_argument(
        "--shuffle", action="store_true", help="Randomize scenario order"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Enable Extension Host activation monitoring and generate report",
    )
    parser.add_argument(
        "--report-path",
        type=str,
        default=default_report_path,
        help="Path for the monitoring report (default: unique file under /results)",
    )
    parser.add_argument(
        "--triggers",
        type=str,
        default=None,
        help="Path to trigger payload JSON (written by host-side scanner.triggers)",
    )
    parser.add_argument(
        "--reload-before-run",
        action="store_true",
        help="Reload the VS Code window after monitoring starts.",
    )
    parser.add_argument(
        "--target-extension-id",
        type=str,
        default="",
        help="Publisher.name identifier for the extension under analysis.",
    )
    parser.add_argument(
        "--skip-automation",
        action="store_true",
        help="Start monitoring but intentionally skip scenario execution.",
    )
    parser.add_argument(
        "--retry-on-crash",
        action="store_true",
        help=(
            "Reload the VS Code workbench after a fatal UI crash and continue. "
            "Default is fail-fast: a renderer crash aborts the scenario sequence."
        ),
    )
    return parser
