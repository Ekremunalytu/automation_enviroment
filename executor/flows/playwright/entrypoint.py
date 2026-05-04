"""Entrypoint for Playwright-based VS Code automation."""

from __future__ import annotations

import sys
from uuid import uuid4

from playwright.sync_api import (
    Browser,
    Page,
    sync_playwright,  # noqa: F401
)
from playwright.sync_api import Error as PlaywrightError  # noqa: F401

from . import (
    automation,  # noqa: F401
    commands,  # noqa: F401
    editor,  # noqa: F401
    monitor,
    panel,  # noqa: F401
    sidebar,  # noqa: F401
    stimulus,  # noqa: F401
    terminal,  # noqa: F401
    vscode,  # noqa: F401
    workspace,  # noqa: F401
)
from . import triggers as trigger_loader
from .entrypoint_runner import create_bait_files
from .entrypoint_runner import main as run_main
from .entrypoint_runner import run_demo as run_demo_impl
from .entrypoint_triggers import (
    reload_window_under_monitoring,
    resolve_execution_plan,
    run_extra_triggers,
)


def run_demo(page: Page) -> None:
    run_demo_impl(page, deps=sys.modules[__name__])


def _create_bait_files(filenames: list[str]) -> list[str]:
    return create_bait_files(filenames, deps=sys.modules[__name__])


def _resolve_execution_plan(
    skip_automation: bool,
    scenario: str | None,
    trigger_payload: trigger_loader.TriggerPayload | None,
) -> tuple[str, list[str]]:
    return resolve_execution_plan(skip_automation, scenario, trigger_payload)


def _default_report_path() -> str:
    return f"/results/activation_report_{uuid4().hex}.json"


def _run_extra_triggers(
    page: Page,
    payload: trigger_loader.TriggerPayload,
    automation_event_recorder=None,
    verification_monitor: monitor.ExtensionMonitor | None = None,
) -> list[str]:
    return run_extra_triggers(
        page,
        payload,
        deps=sys.modules[__name__],
        automation_event_recorder=automation_event_recorder,
        verification_monitor=verification_monitor,
    )


def _reload_window_under_monitoring(browser: Browser, page: Page) -> Page:
    return reload_window_under_monitoring(browser, page, deps=sys.modules[__name__])


def main() -> None:
    run_main(deps=sys.modules[__name__])


if __name__ == "__main__":
    main()
