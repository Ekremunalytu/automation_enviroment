"""Public control boundary for sandbox executor operations."""

from __future__ import annotations

from dataclasses import dataclass

from executor.host import (
    ExecutorError,
    cleanup_trigger_file,
)
from executor.host import (
    install_extension_in_executor as _install_extension_in_executor,
)
from executor.host import reload_vscode_window as _reload_vscode_window
from executor.host import reset_executor_sandbox_state as _reset_executor_sandbox_state
from executor.host import run_playwright_automation as _run_playwright_automation


@dataclass(slots=True)
class ExecutorControl:
    """Single public surface that workflows use for sandbox control."""

    def install_extension(self, publisher: str, name: str, version: str) -> str:
        return _install_extension_in_executor(publisher, name, version)

    def reload_window(self) -> str:
        return _reload_vscode_window()

    def reset_sandbox(self, reload_window: bool = True) -> str:
        return _reset_executor_sandbox_state(reload_window=reload_window)

    def run_automation(
        self,
        *,
        report_path: str,
        scenario: str | None = None,
        trigger_container_path: str | None = None,
        skip_automation: bool = False,
        reload_before_run: bool = False,
        target_extension_id: str | None = None,
    ) -> str:
        return _run_playwright_automation(
            report_path=report_path,
            scenario=scenario,
            trigger_container_path=trigger_container_path,
            skip_automation=skip_automation,
            reload_before_run=reload_before_run,
            target_extension_id=target_extension_id,
        )

    def cleanup_trigger(self, trigger_container_path: str | None) -> None:
        cleanup_trigger_file(trigger_container_path)


default_executor_control = ExecutorControl()


__all__ = [
    "ExecutorControl",
    "ExecutorError",
    "default_executor_control",
]
