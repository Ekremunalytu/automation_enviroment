"""Baseline VS Code settings seeded by the executor container entrypoint.

``start.sh`` writes ``/home/executor/.vscode/User/settings.json`` from a
heredoc. W22 added two coverage/stability settings that must survive refactors:

* ``files.watcherExclude`` for ``**/.extrace-harness/**`` — stops VS Code (and
  the language server) from watching harness bookkeeping artifacts, which
  otherwise flood ``didChangeWatchedFiles`` once the planner synthesizes an
  ``onCommand`` attempt per contributed command.
* ``window.dialogStyle: custom`` + ``files.simpleDialog.enable`` — render
  Save As / Open dialogs inside the workbench DOM so Playwright can dismiss
  them, instead of a native GTK dialog that blocks the harness.

The test parses the heredoc block as JSON, so it also guards the settings
against accidental JSON corruption.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
START_SH = ROOT / "executor" / "container" / "start.sh"


def _baseline_settings() -> dict[str, Any]:
    """Extract and parse the settings.json heredoc block from ``start.sh``."""
    lines = START_SH.read_text(encoding="utf-8").splitlines()
    start = next(
        index
        for index, line in enumerate(lines)
        if "settings.json" in line and "<<'SETTINGS'" in line
    )
    end = next(
        index
        for index in range(start + 1, len(lines))
        if lines[index].strip() == "SETTINGS"
    )
    block = "\n".join(lines[start + 1 : end])
    return json.loads(block)


def test_baseline_settings_is_valid_json() -> None:
    assert isinstance(_baseline_settings(), dict)


def test_baseline_settings_excludes_harness_artifacts_from_watch() -> None:
    watcher_exclude = _baseline_settings().get("files.watcherExclude", {})
    assert watcher_exclude.get("**/.extrace-harness/**") is True


def test_baseline_settings_uses_custom_in_renderer_dialogs() -> None:
    settings = _baseline_settings()
    assert settings.get("window.dialogStyle") == "custom"
    assert settings.get("files.simpleDialog.enable") is True


def test_baseline_settings_preserves_existing_hardening_keys() -> None:
    # The W22 additions must not drop the pre-existing hardening settings.
    settings = _baseline_settings()
    assert settings.get("security.workspace.trust.enabled") is False
    assert settings.get("telemetry.telemetryLevel") == "off"
    assert settings.get("extensions.autoUpdate") is False
