"""Regression: the monitor module is importable purely as
``executor.flows.playwright.monitor`` (package mode), without any
``sys.path`` manipulation that would let bare flat names like ``monitor``
or ``signals`` resolve. ADR 0008 codifies the package-mode contract;
this test pins it.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def test_monitor_package_import_works_without_flat_path(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    playwright_dir = repo_root / "executor" / "flows" / "playwright"
    trimmed_path = [
        entry
        for entry in sys.path
        if Path(entry or ".").resolve() != playwright_dir.resolve()
    ]
    monkeypatch.setattr(sys, "path", trimmed_path)

    snapshot_keys = {
        name
        for name in sys.modules
        if name == "executor.flows.playwright"
        or name.startswith("executor.flows.playwright.")
    }
    saved_modules = {name: sys.modules.get(name) for name in snapshot_keys}

    def restore_modules() -> None:
        for name in list(sys.modules):
            if name in saved_modules:
                continue
            if name == "executor.flows.playwright" or name.startswith(
                "executor.flows.playwright."
            ):
                del sys.modules[name]
        for name, original in saved_modules.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original

    try:
        importlib.invalidate_caches()
        module = importlib.import_module("executor.flows.playwright.monitor")

        assert module.ExtensionMonitor is not None
        assert module.ActivationReport is not None
    finally:
        restore_modules()
