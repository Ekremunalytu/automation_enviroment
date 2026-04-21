from __future__ import annotations

import importlib
import sys
from pathlib import Path


def test_monitor_package_import_does_not_require_flat_module_names(
    monkeypatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    playwright_dir = repo_root / "executor" / "flows" / "playwright"
    trimmed_path = [
        entry
        for entry in sys.path
        if Path(entry or ".").resolve() != playwright_dir.resolve()
    ]
    monkeypatch.setattr(sys, "path", trimmed_path)

    for module_name in (
        "monitor",
        "annotation",
        "capture",
        "health",
        "health_reconciliation",
        "health_summary",
        "signal_policy",
        "signals",
        "runtime_capture",
        "executor.flows.playwright.capture",
        "executor.flows.playwright.health",
        "executor.flows.playwright.health_reconciliation",
        "executor.flows.playwright.health_summary",
        "executor.flows.playwright.signal_policy",
        "executor.flows.playwright.signals",
        "executor.flows.playwright.monitor",
    ):
        sys.modules.pop(module_name, None)

    importlib.invalidate_caches()
    module = importlib.import_module("executor.flows.playwright.monitor")

    assert module.ExtensionMonitor is not None
    assert module.ActivationReport is not None
