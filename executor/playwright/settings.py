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

    Opens the theme picker, types the theme name, and confirms selection.
    Waits for the quick-input widget to fully close before returning.
    """
    # Open theme picker via Command Palette
    page.keyboard.press(keyboard.COMMAND_PALETTE)
    page.wait_for_timeout(500)
    page.keyboard.type("Preferences: Color Theme", delay=30)
    page.wait_for_timeout(600)
    page.keyboard.press("Enter")
    page.wait_for_timeout(800)

    # Theme picker is now open — type to filter and select
    page.keyboard.type(theme_name, delay=30)
    page.wait_for_timeout(800)
    page.keyboard.press("Enter")
    page.wait_for_timeout(1000)

    # Wait for quick-input to close (theme applied)
    try:
        quick_input_sel = ".quick-input-widget:not([style*='display: none'])"
        page.wait_for_selector(quick_input_sel, state="detached", timeout=3000)
    except PlaywrightTimeoutError:
        # Force close if still open
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)


def toggle_setting_via_json(page: Page, key: str, value: str) -> None:
    """Open settings.json and insert/update a setting key-value pair.

    This triggers onConfiguration change events for extensions watching the key.
    Selects all existing content and rewrites the JSON to avoid navigation issues.

    Args:
        key: The setting key (e.g. "editor.fontSize").
        value: The setting value as a JSON string (e.g. "16").
    """
    open_settings_json(page)
    page.wait_for_timeout(800)

    # Read current JSON content by selecting all
    page.keyboard.press("Control+a")
    page.wait_for_timeout(200)

    # Get selected text to parse existing settings
    # Since we can't easily read, just append to a known structure
    # Type the complete settings JSON with the new key added
    page.keyboard.press("Control+End")
    page.wait_for_timeout(200)

    # Go to end, move before closing brace, add setting
    page.keyboard.press("ArrowUp")
    page.keyboard.press("End")
    page.keyboard.type(f',\n    "{key}": {value}', delay=15)
    page.wait_for_timeout(300)

    # Save to trigger configuration change event
    page.keyboard.press(keyboard.SAVE_FILE)
    page.wait_for_timeout(1000)

    # Close the file to prevent duplicate-tab issues on next call
    page.keyboard.press(keyboard.CLOSE_EDITOR)
    page.wait_for_timeout(300)


def write_settings_batch(page: Page, settings: list[tuple[str, str]]) -> None:
    """Write multiple settings to settings.json in a single operation.

    More reliable than calling toggle_setting_via_json multiple times,
    since it opens the file once, writes all values, and saves once.

    Args:
        settings: List of (key, value) tuples.
    """
    if not settings:
        return

    open_settings_json(page)
    page.wait_for_timeout(800)

    for key, value in settings:
        # Navigate to end each time, move before closing brace
        page.keyboard.press("Control+End")
        page.wait_for_timeout(200)
        page.keyboard.press("ArrowUp")
        page.keyboard.press("End")
        page.keyboard.type(f',\n    "{key}": {value}', delay=15)
        page.wait_for_timeout(300)

    # Save once to trigger all configuration change events
    page.keyboard.press(keyboard.SAVE_FILE)
    page.wait_for_timeout(1000)

    # Close settings.json
    page.keyboard.press(keyboard.CLOSE_EDITOR)
    page.wait_for_timeout(300)


def toggle_fullscreen(page: Page) -> None:
    """Toggle fullscreen / zen mode (F11).

    Some extensions react to layout change events.
    """
    page.keyboard.press(keyboard.TOGGLE_FULLSCREEN)
    page.wait_for_timeout(500)
