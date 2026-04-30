"""Workbench and navigation Playwright automation scenarios."""

from __future__ import annotations

import editor
import keyboard
import panel
import settings
import sidebar
from playwright.sync_api import Page

from .common import log


def scenario_extension_browsing(page: Page) -> None:
    """Simulate browsing the extensions marketplace."""
    log("Extension browsing")

    sidebar.open_extensions_view(page)
    page.wait_for_timeout(1500)
    for query in ["python", "prettier", "docker", "git"]:
        page.keyboard.press(keyboard.FOCUS_EXTENSIONS)
        page.wait_for_timeout(300)
        page.keyboard.press(keyboard.SELECT_ALL)
        page.keyboard.type(query, delay=40)
        page.wait_for_timeout(2000)
    sidebar.open_explorer(page)
    page.wait_for_timeout(300)


def scenario_settings_modification(page: Page) -> None:
    """Simulate modifying VS Code settings."""
    log("Settings modification")

    setting_changes = [
        ("editor.fontSize", "16"),
        ("editor.formatOnSave", "true"),
        ("editor.wordWrap", '"on"'),
        ("editor.minimap.enabled", "false"),
    ]
    settings.write_settings_batch(page, setting_changes)
    page.wait_for_timeout(500)
    settings.change_theme(page, "Default Light Modern")
    page.wait_for_timeout(1000)
    settings.change_theme(page, "Default Dark Modern")
    page.wait_for_timeout(500)
    settings.open_settings(page)
    page.wait_for_timeout(1000)
    for query in ["font size", "format on save"]:
        settings.search_setting(page, query)
        page.wait_for_timeout(800)
    editor.close_active_editor(page)
    page.wait_for_timeout(300)
    settings.toggle_fullscreen(page)
    page.wait_for_timeout(1000)
    settings.toggle_fullscreen(page)
    page.wait_for_timeout(500)


def scenario_project_exploration(page: Page) -> None:
    """Simulate exploring a project by opening various files."""
    log("Project exploration")

    sidebar.open_explorer(page)
    page.wait_for_timeout(500)
    files_to_open = [
        "src/app.py",
        "frontend/src/api.js",
        "frontend/src/index.ts",
        "docker-compose.yml",
        "frontend/package.json",
        "services/api/main.go",
        "services/worker/src/main.rs",
        "native/parser.c",
        "native/engine.cpp",
        "services/dotnet/Program.cs",
        "scripts/migrate.rb",
        "legacy/api.php",
        "frontend/public/index.html",
        "frontend/public/styles.css",
        "config/settings.xml",
    ]
    for index, filename in enumerate(files_to_open, start=1):
        editor.open_file_by_name(page, filename)
        page.wait_for_timeout(1500)
        if index % 5 == 0:
            editor.close_all_editors(page)
            page.wait_for_timeout(300)
    editor.close_all_editors(page)
    page.wait_for_timeout(500)


def scenario_search_workflow(page: Page) -> None:
    """Simulate searching across files."""
    log("Search workflow")

    sidebar.open_search(page)
    page.wait_for_timeout(800)
    for term in ["API_KEY", "password", "DATABASE_URL", "secret", "token", "import"]:
        page.keyboard.press(keyboard.FOCUS_SEARCH)
        page.wait_for_timeout(300)
        page.keyboard.press(keyboard.SELECT_ALL)
        page.keyboard.type(term, delay=30)
        page.wait_for_timeout(1500)
    sidebar.open_explorer(page)
    page.wait_for_timeout(300)


def scenario_diagnostics_check(page: Page) -> None:
    """Simulate checking diagnostics and output panels."""
    log("Diagnostics check")

    editor.open_file_by_name(page, "src/app.py")
    page.wait_for_timeout(1000)
    panel.focus_problems(page)
    page.wait_for_timeout(1000)
    panel.focus_output(page)
    page.wait_for_timeout(1000)
    page.keyboard.press(keyboard.FOCUS_EDITOR)
    page.wait_for_timeout(300)
