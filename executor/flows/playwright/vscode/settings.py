"""VS Code settings helpers.

Covers activation events: onConfiguration:*
Modifying settings triggers configuration change events that some
extensions listen to.

`write_settings_batch` / `toggle_setting_via_json` update the user
`settings.json` by rewriting the on-disk file atomically (temp + rename)
instead of driving the Monaco buffer via keyboard navigation. The older
cursor-based append produced invalid JSON (new keys landed after the
closing brace), which crashed the VS Code renderer
(`CodeWindow: renderer process gone`) and cascade-failed every
subsequent Playwright scenario. The filesystem path is a documented
VS Code affordance: the settings file watcher re-reads the file and
dispatches `onDidChangeConfiguration` exactly as it would for a buffer
save, without any risk of mid-write corruption.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from ..vscode import keyboard
from .commands import run_command, wait_for_quick_input_hidden

_SETTINGS_SEARCH_SELECTORS = [
    "input.settings-search-input",
    "input[aria-label='Search Settings']",
    ".settings-editor .search-container input",
]

_DEFAULT_SETTINGS_JSON_PATH = Path("/home/executor/.vscode/User/settings.json")


def _settings_json_path() -> Path:
    override = os.environ.get("EXTRACE_VSCODE_SETTINGS_JSON")
    return Path(override) if override else _DEFAULT_SETTINGS_JSON_PATH


def _load_current_settings(path: Path) -> dict[str, Any] | None:
    """Parse the existing settings.json.

    Returns the parsed mapping, `{}` if the file is missing or blank,
    or `None` when the existing file is unreadable / malformed — in
    that case callers must skip the write rather than compound the
    damage by overwriting with partial data.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError:
        return None
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def _parse_setting_value(value_literal: str) -> Any:
    """Interpret the stringified JSON value; keep the raw string on parse error."""
    try:
        return json.loads(value_literal)
    except json.JSONDecodeError:
        return value_literal


def _atomic_write_settings(path: Path, data: dict[str, Any]) -> None:
    """Write `data` to `path` atomically (tmp + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp_path, path)


def open_settings(page: Page) -> None:
    """Open the Settings UI (Ctrl+,)."""
    page.keyboard.press(keyboard.OPEN_SETTINGS)
    page.wait_for_timeout(1000)


def open_settings_json(page: Page) -> None:
    """Open settings.json directly via Command Palette."""
    run_command(page, "Preferences: Open User Settings (JSON)")
    page.wait_for_timeout(1000)


def search_setting(page: Page, query: str) -> None:
    """Search for a setting in the Settings UI.

    The Settings UI must already be open.
    """
    for selector in _SETTINGS_SEARCH_SELECTORS:
        try:
            search_box = page.wait_for_selector(selector, state="visible", timeout=1200)
            if search_box is None:
                continue
            search_box.click()
            page.keyboard.press(keyboard.SELECT_ALL)
            page.keyboard.type(query, delay=30)
            page.wait_for_timeout(500)
            return
        except PlaywrightTimeoutError:
            continue

    # Fallback: focus local find box without reopening Settings.
    page.keyboard.press("Control+KeyF")
    page.wait_for_timeout(300)
    page.keyboard.press(keyboard.SELECT_ALL)
    page.keyboard.type(query, delay=30)
    page.wait_for_timeout(500)


def change_theme(page: Page, theme_name: str = "Default Dark Modern") -> None:
    """Change the color theme via Command Palette.

    Triggers workbench.colorTheme configuration change.

    Opens the theme picker, types the theme name, and confirms selection.
    Waits for the quick-input widget to fully close before returning.
    """
    run_command(
        page,
        "Preferences: Color Theme",
        expect_followup_quick_input=True,
    )

    # Theme picker is now open — type to filter and select
    page.keyboard.type(theme_name, delay=30)
    page.wait_for_timeout(800)
    page.keyboard.press("Enter")
    wait_for_quick_input_hidden(page, timeout_ms=3000)
    page.wait_for_timeout(1000)


def toggle_setting_via_json(page: Page, key: str, value: str) -> None:
    """Merge `{key: value}` into settings.json atomically.

    Args:
        key: The setting key (e.g. "editor.fontSize").
        value: The setting value as a JSON string (e.g. "16", '"on"',
            "true"). Unparseable strings are stored verbatim.
    """
    write_settings_batch(page, [(key, value)])


def write_settings_batch(page: Page, settings: list[tuple[str, str]]) -> None:
    """Merge multiple settings into settings.json in a single atomic write.

    Reads the current file, overlays the new keys (preserving everything
    else), and rewrites the full document via tmp + rename. VS Code's
    user-settings file watcher picks up the change and dispatches
    `onDidChangeConfiguration`.

    Guarantees: the on-disk settings.json is always valid JSON, so the
    renderer never crashes on a malformed buffer. If the file is
    currently unreadable or already corrupted we skip the write rather
    than compound the damage.

    Args:
        settings: List of (key, json_value_literal) tuples.
    """
    if not settings:
        return

    path = _settings_json_path()
    current = _load_current_settings(path)
    if current is None:
        print(
            f"[settings] skipping write: {path} is unreadable or malformed; "
            "leaving the file untouched to avoid compounding corruption."
        )
        page.wait_for_timeout(500)
        return

    for key, value_literal in settings:
        current[key] = _parse_setting_value(value_literal)

    _atomic_write_settings(path, current)

    # Let the settings file watcher re-read and fan out
    # onDidChangeConfiguration before the next scenario step.
    page.wait_for_timeout(1000)


def toggle_fullscreen(page: Page) -> None:
    """Toggle fullscreen / zen mode (F11).

    Some extensions react to layout change events.
    """
    page.keyboard.press(keyboard.TOGGLE_FULLSCREEN)
    page.wait_for_timeout(500)
