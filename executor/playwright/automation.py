"""User behavior simulation scenarios for extension security testing.

Each scenario composes primitive helpers into a realistic user workflow
that triggers specific VS Code extension activation events.

Usage:
    from playwright.sync_api import sync_playwright
    import vscode, automation

    with sync_playwright() as pw:
        browser, page = vscode.connect(pw)
        vscode.wait_until_ready(page)
        automation.run_all_scenarios(page)
        vscode.disconnect(browser)
"""

import random
from collections.abc import Callable

import commands
import debug
import editor
import keyboard
import panel
import settings
import sidebar
import terminal
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

ScenarioFn = Callable[[Page], None]

# ---------------------------------------------------------------------------
# Scenario 1: Developer coding session
# Triggers: onLanguage:*, completionProvider, formatterProvider, definitionProvider
# ---------------------------------------------------------------------------


def scenario_coding_session(page: Page, language: str = "python") -> None:
    """Simulate a developer writing and editing code.

    Opens a file, types code, triggers IntelliSense, formats, navigates
    to definitions, and saves. This activates language-related extensions.
    """
    _log("Coding session", language)

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

    # Open existing file
    editor.open_file_by_name(page, filename)
    page.wait_for_timeout(1500)  # wait for language server to activate

    # Move to end and type new code
    page.keyboard.press("Control+End")
    page.wait_for_timeout(200)
    page.keyboard.press("Enter")
    page.keyboard.press("Enter")
    editor.type_in_editor(page, snippet)
    page.wait_for_timeout(500)

    # Trigger IntelliSense
    editor.trigger_suggest(page)
    page.keyboard.press("Escape")  # dismiss suggestions
    page.wait_for_timeout(300)

    # Format document
    editor.format_document(page)
    page.wait_for_timeout(500)

    # Try go to definition on a symbol
    page.keyboard.press("Control+Home")
    page.wait_for_timeout(200)
    # Move to a line with a function/import
    for _ in range(5):
        page.keyboard.press("ArrowDown")
    page.wait_for_timeout(100)
    editor.go_to_definition(page)
    page.wait_for_timeout(500)
    page.keyboard.press("Escape")  # close peek if opened

    # Save
    editor.save_file(page)


# ---------------------------------------------------------------------------
# Scenario 2: Debug session
# Triggers: onDebug:*, onDebugResolve:*, onDebugAdapterProtocol:*
# ---------------------------------------------------------------------------


def scenario_debug_session(page: Page) -> None:
    """Simulate a debugging workflow.

    Opens the debug view, sets a breakpoint, starts/stops a debug session.
    This triggers debug-related extension activation events.
    """
    _log("Debug session")

    # Open a Python file to debug
    editor.open_file_by_name(page, "src/app.py")
    page.wait_for_timeout(1000)

    # Open debug sidebar
    sidebar.open_debug(page)
    page.wait_for_timeout(500)

    # Set a breakpoint via command
    page.keyboard.press("Control+Home")
    for _ in range(10):
        page.keyboard.press("ArrowDown")
    page.wait_for_timeout(200)
    debug.add_breakpoint_via_command(page)
    page.wait_for_timeout(300)

    # Start debug session (will likely prompt for configuration)
    debug.start_debug(page)
    page.wait_for_timeout(3000)

    # Dismiss any popups like "Find Python extension" dialog
    editor._dismiss_notification(page)
    page.wait_for_timeout(300)

    # Step through if debug started
    debug.step_over(page)
    page.wait_for_timeout(500)
    debug.step_over(page)
    page.wait_for_timeout(500)

    # Open debug console
    panel.open_debug_console(page)
    page.wait_for_timeout(500)

    # Stop debug
    debug.stop_debug(page)
    page.wait_for_timeout(500)

    # Dismiss any lingering dialogs
    editor._dismiss_notification(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)


# ---------------------------------------------------------------------------
# Scenario 3: Terminal workflow
# Triggers: onTerminalCreate, onTerminalOpen, shell integration extensions
# ---------------------------------------------------------------------------


def scenario_terminal_usage(page: Page) -> None:
    """Simulate developer terminal activity.

    Opens terminal, runs typical developer commands. Extensions monitoring
    terminal activity or providing shell integration will activate.
    """
    _log("Terminal usage")

    terminal.new_terminal(page)
    page.wait_for_timeout(1000)

    # Simulate common developer commands
    cmds = [
        "ls -la",
        "cat .env",
        "git status",
        "python --version",
        "node --version",
        "pip list",
        "npm ls --depth=0",
        "echo $PATH",
    ]

    for cmd in cmds:
        terminal.type_in_terminal(page, cmd)
        page.wait_for_timeout(1500)

    # Open a second terminal
    terminal.new_terminal(page)
    page.wait_for_timeout(500)
    terminal.type_in_terminal(page, "pwd")
    page.wait_for_timeout(500)


# ---------------------------------------------------------------------------
# Scenario 4: Git / Source Control workflow
# Triggers: onView:scm, git extension activation, SCM providers
# ---------------------------------------------------------------------------


def scenario_git_workflow(page: Page) -> None:
    """Simulate a git workflow via sidebar and terminal.

    Opens Source Control view, makes a file change, stages and commits.
    """
    _log("Git workflow")

    # Open Source Control view
    sidebar.open_source_control(page)
    page.wait_for_timeout(1000)

    # Edit a file to create a change
    editor.open_file_by_name(page, "README.md")
    page.wait_for_timeout(500)
    page.keyboard.press("Control+End")
    editor.type_in_editor(page, "\n## Updated section\nNew content here.\n")
    editor.save_file(page)
    page.wait_for_timeout(500)

    # Go back to Source Control to see changes
    sidebar.open_source_control(page)
    page.wait_for_timeout(1000)

    # Use terminal for git commands
    terminal.toggle_terminal(page)
    page.wait_for_timeout(500)
    terminal.type_in_terminal(page, "git --no-pager diff")
    page.wait_for_timeout(1000)
    terminal.type_in_terminal(page, "git add -A")
    page.wait_for_timeout(500)
    terminal.type_in_terminal(page, "git status")
    page.wait_for_timeout(500)

    # Toggle terminal back
    terminal.toggle_terminal(page)


# ---------------------------------------------------------------------------
# Scenario 5: Extension browsing
# Triggers: onView:extensions, extension marketplace interaction
# ---------------------------------------------------------------------------


def scenario_extension_browsing(page: Page) -> None:
    """Simulate browsing the extensions marketplace.

    Opens Extensions view, searches for extensions. Some extensions react
    to the extensions view being opened.
    """
    _log("Extension browsing")

    sidebar.open_extensions_view(page)
    page.wait_for_timeout(1500)

    # Search for popular extensions
    searches = ["python", "prettier", "docker", "git"]
    for query in searches:
        # The extensions search input should be focused
        page.keyboard.press(keyboard.FOCUS_EXTENSIONS)
        page.wait_for_timeout(300)
        page.keyboard.press(keyboard.SELECT_ALL)
        page.keyboard.type(query, delay=40)
        page.wait_for_timeout(2000)

    # Return to explorer
    sidebar.open_explorer(page)
    page.wait_for_timeout(300)


# ---------------------------------------------------------------------------
# Scenario 6: Settings modification
# Triggers: onConfiguration:*, workspace configuration changes
# ---------------------------------------------------------------------------


def scenario_settings_modification(page: Page) -> None:
    """Simulate modifying VS Code settings.

    Writes real values into settings.json to trigger onConfiguration:* events,
    changes the color theme, and browses the Settings UI.
    """
    _log("Settings modification")

    # --- Phase 1: Modify settings via settings.json (triggers onConfiguration:*) ---
    setting_changes = [
        ("editor.fontSize", "16"),
        ("editor.formatOnSave", "true"),
        ("editor.wordWrap", '"on"'),
        ("editor.minimap.enabled", "false"),
    ]
    settings.write_settings_batch(page, setting_changes)
    page.wait_for_timeout(500)

    # --- Phase 2: Change color theme (separate from JSON edits) ---
    settings.change_theme(page, "Default Light Modern")
    page.wait_for_timeout(1000)
    settings.change_theme(page, "Default Dark Modern")
    page.wait_for_timeout(500)

    # --- Phase 3: Browse Settings UI (visual interaction) ---
    settings.open_settings(page)
    page.wait_for_timeout(1000)
    for query in ["font size", "format on save"]:
        settings.search_setting(page, query)
        page.wait_for_timeout(800)
    editor.close_active_editor(page)
    page.wait_for_timeout(300)

    # Toggle fullscreen (layout change event)
    settings.toggle_fullscreen(page)
    page.wait_for_timeout(1000)
    settings.toggle_fullscreen(page)
    page.wait_for_timeout(500)


# ---------------------------------------------------------------------------
# Scenario 7: Multi-file project exploration
# Triggers: onLanguage:* (multiple), workspaceContains:*, onView:explorer
# ---------------------------------------------------------------------------


def scenario_project_exploration(page: Page) -> None:
    """Simulate exploring a project by opening various files.

    Opens multiple file types to trigger onLanguage activation for each.
    """
    _log("Project exploration")

    sidebar.open_explorer(page)
    page.wait_for_timeout(500)

    # Open each file type, wait for language activation, then close to save memory.
    # Each open triggers onLanguage:* for the corresponding language extension.
    files_to_open = [
        "src/app.py",  # python
        "frontend/src/api.js",  # javascript
        "frontend/src/index.ts",  # typescript
        "docker-compose.yml",  # yaml
        "frontend/package.json",  # json
        "services/api/main.go",  # go
        "services/worker/src/main.rs",  # rust
        "native/parser.c",  # c
        "native/engine.cpp",  # cpp
        "services/dotnet/Program.cs",  # csharp
        "scripts/migrate.rb",  # ruby
        "legacy/api.php",  # php
        "frontend/public/index.html",  # html
        "frontend/public/styles.css",  # css
        "config/settings.xml",  # xml
    ]

    for i, filename in enumerate(files_to_open):
        editor.open_file_by_name(page, filename)
        page.wait_for_timeout(1500)  # wait for language server activation

        # Close every 5 files to avoid memory buildup
        if (i + 1) % 5 == 0:
            editor.close_all_editors(page)
            page.wait_for_timeout(300)

    # Close remaining editors
    editor.close_all_editors(page)
    page.wait_for_timeout(500)


# ---------------------------------------------------------------------------
# Scenario 8: Search workflow
# Triggers: onView:search, search provider extensions
# ---------------------------------------------------------------------------


def scenario_search_workflow(page: Page) -> None:
    """Simulate searching across files.

    Opens search sidebar and searches for various terms. Extensions providing
    custom search results or search decorations will activate.
    """
    _log("Search workflow")

    sidebar.open_search(page)
    page.wait_for_timeout(800)

    search_terms = [
        "API_KEY",
        "password",
        "DATABASE_URL",
        "secret",
        "token",
        "import",
    ]

    for term in search_terms:
        page.keyboard.press(keyboard.FOCUS_SEARCH)
        page.wait_for_timeout(300)
        page.keyboard.press(keyboard.SELECT_ALL)
        page.keyboard.type(term, delay=30)
        page.wait_for_timeout(1500)

    # Return to explorer
    sidebar.open_explorer(page)
    page.wait_for_timeout(300)


# ---------------------------------------------------------------------------
# Scenario 9: Output and diagnostics monitoring
# Triggers: onView:output, diagnostic extensions, linters
# ---------------------------------------------------------------------------


def scenario_diagnostics_check(page: Page) -> None:
    """Simulate checking diagnostics and output panels.

    Opens Problems and Output panels. Linter and diagnostic extensions
    will surface their findings.
    """
    _log("Diagnostics check")

    # Open a file with potential issues
    editor.open_file_by_name(page, "src/app.py")
    page.wait_for_timeout(1000)

    # Focus problems panel
    panel.focus_problems(page)
    page.wait_for_timeout(1000)

    # Focus output panel to see extension logs
    panel.focus_output(page)
    page.wait_for_timeout(1000)

    # Back to editor
    page.keyboard.press(keyboard.FOCUS_EDITOR)
    page.wait_for_timeout(300)


# ---------------------------------------------------------------------------
# Scenario 10: Rename/refactor workflow
# Triggers: renameProvider, codeActionProvider
# ---------------------------------------------------------------------------


def scenario_refactor_workflow(page: Page) -> None:
    """Simulate a rename/refactor action.

    Opens a file, selects a symbol, and renames it. This triggers
    rename providers and code action providers.
    """
    _log("Refactor workflow")

    editor.open_file_by_name(page, "src/app.py")
    page.wait_for_timeout(1000)

    # Navigate to a function name
    page.keyboard.press("Control+Home")
    page.wait_for_timeout(200)

    # Use Ctrl+D to find and select a word
    commands.run_command(page, "Find and Replace")
    page.wait_for_timeout(500)
    page.keyboard.type("health", delay=30)
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # Try rename symbol
    editor.rename_symbol(page, "health_check")
    page.wait_for_timeout(500)

    # Undo the rename to keep the file intact
    page.keyboard.press("Control+KeyZ")
    page.wait_for_timeout(300)
    page.keyboard.press("Control+KeyZ")
    page.wait_for_timeout(300)

    editor.save_file(page)


# ---------------------------------------------------------------------------
# Master orchestrator
# ---------------------------------------------------------------------------

_ALL_SCENARIOS: list[tuple[str, ScenarioFn]] = [
    ("coding_session", scenario_coding_session),
    ("debug_session", scenario_debug_session),
    ("terminal_usage", scenario_terminal_usage),
    ("git_workflow", scenario_git_workflow),
    ("extension_browsing", scenario_extension_browsing),
    ("settings_modification", scenario_settings_modification),
    ("project_exploration", scenario_project_exploration),
    ("search_workflow", scenario_search_workflow),
    ("diagnostics_check", scenario_diagnostics_check),
    ("refactor_workflow", scenario_refactor_workflow),
]


def run_all_scenarios(page: Page, shuffle: bool = False) -> list[str]:
    """Run all user behavior simulation scenarios sequentially.

    Args:
        page: Playwright Page connected to VS Code via CDP.
        shuffle: If True, randomize scenario order to vary timing patterns.

    Returns:
        List of scenario names that failed.
    """
    scenarios = list(_ALL_SCENARIOS)
    failed_scenarios: list[str] = []
    if shuffle:
        random.shuffle(scenarios)

    for name, fn in scenarios:
        try:
            fn(page)
            _log(f"DONE: {name}")
        except (PlaywrightError, RuntimeError, ValueError) as exc:
            _log(f"FAIL: {name} -> {exc}")
            failed_scenarios.append(name)
            # Cleanup: dismiss any stuck dialogs/menus after failure
            _recover_ui_state(page)
        _cleanup_between_scenarios(page)
        # Small pause between scenarios
        page.wait_for_timeout(1000)

    return failed_scenarios


def run_scenario(page: Page, name: str) -> None:
    """Run a single scenario by name.

    Args:
        page: Playwright Page connected to VS Code.
        name: Scenario name (e.g. "coding_session", "debug_session").
    """
    scenario_map = dict(_ALL_SCENARIOS)
    fn = scenario_map.get(name)
    if fn is None:
        raise ValueError(f"Unknown scenario: {name!r}. Available: {list(scenario_map)}")
    fn(page)


def list_scenarios() -> list[str]:
    """Return available scenario names."""
    return [name for name, _ in _ALL_SCENARIOS]


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _recover_ui_state(page: Page) -> None:
    """Dismiss stuck dialogs and return VS Code to a usable state."""
    try:
        # Press Escape multiple times to close any open dialogs/menus
        for _ in range(3):
            page.keyboard.press("Escape")
            page.wait_for_timeout(200)
        # Dismiss any VS Code notification toasts (e.g. formatter, extension)
        editor._dismiss_notification(page)
        # Focus back to editor
        page.keyboard.press(keyboard.FOCUS_EDITOR)
        page.wait_for_timeout(300)
    except PlaywrightError as exc:
        _log(f"UI recovery failed: {exc}")


def _cleanup_between_scenarios(page: Page) -> None:
    """Release UI/editor state between scenarios to reduce memory pressure."""
    try:
        # Close all editors using Ctrl+K, Ctrl+W chord (two sequential presses)
        page.keyboard.press("Control+KeyK")
        page.wait_for_timeout(100)
        page.keyboard.press("Control+KeyW")
        page.wait_for_timeout(500)
        # Kill all terminal instances to free memory
        _kill_all_terminals(page)
        # Close bottom panel (terminal, output, etc.)
        page.keyboard.press(keyboard.TOGGLE_PANEL)
        page.wait_for_timeout(200)
        # Dismiss any lingering notifications
        editor._dismiss_notification(page)
        page.keyboard.press("Escape")
        page.keyboard.press(keyboard.FOCUS_EDITOR)
        page.wait_for_timeout(200)
    except PlaywrightError as exc:
        _log(f"Inter-scenario cleanup failed: {exc}")


def _kill_all_terminals(page: Page) -> None:
    """Kill all terminal instances via Command Palette."""
    try:
        commands.run_command(page, "Terminal: Kill All Terminals")
        page.wait_for_timeout(500)
    except PlaywrightError:
        pass  # No terminals open — fine


def _log(msg: str, detail: str = "") -> None:
    suffix = f" ({detail})" if detail else ""
    print(f"[automation] {msg}{suffix}")
