"""Editing-focused Playwright automation scenarios."""

from __future__ import annotations

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from .. import commands, editor
from .common import log


def scenario_coding_session(page: Page, language: str = "python") -> None:
    """Simulate a developer writing and editing code."""
    log("Coding session", language)

    sample_files = {
        "python": (
            "src/app.py",
            "def process_data(items):\n    return [x for x in items]\n",
        ),
        "javascript": (
            "frontend/src/api.js",
            "const getData = async () => {\n    return fetch('/api');\n};\n",
        ),
        "typescript": (
            "frontend/src/index.ts",
            "interface User {\n    name: string;\n    email: string;\n}\n",
        ),
        "go": (
            "services/api/main.go",
            "func handler(w http.ResponseWriter, r *http.Request) {\n",
        ),
        "rust": (
            "services/worker/src/main.rs",
            "fn process(data: &[u8]) -> Result<(), Error> {\n",
        ),
    }

    filename, snippet = sample_files.get(language, sample_files["python"])
    editor.open_file_by_name(page, filename)
    page.wait_for_timeout(1500)
    page.keyboard.press("Control+End")
    page.wait_for_timeout(200)
    page.keyboard.press("Enter")
    page.keyboard.press("Enter")
    editor.type_in_editor(page, snippet)
    page.wait_for_timeout(500)
    editor.trigger_suggest(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    editor.format_document(page)
    page.wait_for_timeout(500)
    page.keyboard.press("Control+Home")
    page.wait_for_timeout(200)
    for _ in range(5):
        page.keyboard.press("ArrowDown")
    page.wait_for_timeout(100)
    editor.go_to_definition(page)
    page.wait_for_timeout(500)
    page.keyboard.press("Escape")
    editor.save_file(page)


def scenario_refactor_workflow(page: Page) -> None:
    """Simulate a rename/refactor action."""
    log("Refactor workflow")

    editor.open_file_by_name(page, "src/app.py")
    page.wait_for_timeout(1000)
    page.keyboard.press("Control+Home")
    page.wait_for_timeout(200)
    commands.run_command(page, "Find and Replace")
    page.wait_for_timeout(500)
    page.keyboard.type("health", delay=30)
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    editor.rename_symbol(page, "health_check")
    page.wait_for_timeout(500)
    page.keyboard.press("Control+KeyZ")
    page.wait_for_timeout(300)
    page.keyboard.press("Control+KeyZ")
    page.wait_for_timeout(300)
    editor.save_file(page)


def scenario_notebook_session(page: Page) -> None:
    """Simulate opening and interacting with a Jupyter notebook."""
    log("Notebook session")

    editor.open_file_by_name(page, "notebooks/analysis.ipynb")
    page.wait_for_timeout(3000)
    editor._dismiss_notification(page)
    page.wait_for_timeout(500)
    try:
        cell = page.locator(".cell-editor-container").first
        if cell.is_visible(timeout=2000):
            cell.click()
            page.wait_for_timeout(500)
    except PlaywrightError:
        pass
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(300)
    editor.close_active_editor(page)
    page.wait_for_timeout(500)
