"""VS Code settings helpers.

Covers activation events: onConfiguration:*
Modifying settings triggers configuration change events that some extensions listen to.
"""

import keyboard
from commands import run_command
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

_SETTINGS_SEARCH_SELECTORS = [
    "input.settings-search-input",
    "input[aria-label='Search Settings']",
    ".settings-editor .search-container input",
]


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

    The theme picker is a quick-pick that stays open for live preview.
    We open it via Command Palette, type the theme name, press Enter
    to confirm, then Escape to ensure the picker is closed.
    """
    page.keyboard.press(keyboard.COMMAND_PALETTE)
    page.wait_for_timeout(500)
    page.keyboard.type("Color Theme", delay=30)
    page.wait_for_timeout(600)
    page.keyboard.press("Enter")
    page.wait_for_timeout(800)

    # Theme picker is now open - type to filter
    page.keyboard.type(theme_name, delay=30)
    page.wait_for_timeout(600)
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)

    # Ensure picker is closed
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)


def toggle_setting_via_json(page: Page, key: str, value: str) -> None:
    """Open settings.json and insert a setting key-value pair.

    This triggers onConfiguration change events for extensions watching the key.

    Args:
        key: The setting key (e.g. "editor.fontSize").
        value: The setting value as a JSON string (e.g. "16").
    """
    open_settings_json(page)
    page.wait_for_timeout(500)

    # Navigate to end of the JSON object to add setting
    page.keyboard.press(keyboard.FOCUS_EDITOR)
    page.wait_for_timeout(200)

    # Use Command Palette to go to end of file
    run_command(page, "Go to End of File")
    page.wait_for_timeout(300)

    # Move before the closing brace and add the setting
    page.keyboard.press("ArrowUp")
    page.keyboard.press("End")
    page.keyboard.type(f',\n    "{key}": {value}', delay=15)
    page.wait_for_timeout(300)

    # Save to trigger configuration change event
    page.keyboard.press(keyboard.SAVE_FILE)
    page.wait_for_timeout(1000)


def toggle_fullscreen(page: Page) -> None:
    """Toggle fullscreen / zen mode (F11).

    Some extensions react to layout change events.
    """
    page.keyboard.press(keyboard.TOGGLE_FULLSCREEN)
    page.wait_for_timeout(500)
