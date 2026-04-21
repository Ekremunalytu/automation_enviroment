"""Helpers for resolving the public ``monitor`` facade module."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

_MONITOR_MODULE_NAMES = (
    "monitor",
    "executor.flows.playwright.monitor",
)


def resolve_monitor_api() -> ModuleType:
    """Return the loaded public monitor module.

    The executor imports these helpers both as a flat top-level module inside
    the container and as a package module in tests. Resolving through the
    public facade keeps ``monkeypatch.setattr(monitor, ...)`` behavior intact
    even after the implementation is split across sibling modules.
    """

    for module_name in _MONITOR_MODULE_NAMES:
        module = sys.modules.get(module_name)
        if module is not None:
            return module

    for module_name in _MONITOR_MODULE_NAMES:
        try:
            return importlib.import_module(module_name)
        except ImportError:
            continue

    raise RuntimeError("monitor facade module is unavailable")
