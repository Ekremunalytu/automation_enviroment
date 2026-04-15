from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import automation  # noqa: E402
import capture  # noqa: E402
import debug  # noqa: E402
import editor  # noqa: E402
import keyboard  # noqa: E402
import panel  # noqa: E402
import settings  # noqa: E402
import sidebar  # noqa: E402
import terminal  # noqa: E402
import triggers  # noqa: E402
import vscode  # noqa: E402


class _FakeKeyboard:
    def __init__(self) -> None:
        self.presses: list[str] = []
        self.typed: list[tuple[str, int]] = []

    def press(self, key: str) -> None:
        self.presses.append(key)

    def type(self, text: str, delay: int = 0) -> None:
        self.typed.append((text, delay))


class _FakeElement:
    def __init__(
        self,
        *,
        text: str = "",
        query_results: dict[str, _FakeElement] | None = None,
    ) -> None:
        self._text = text
        self._query_results = query_results or {}
        self.clicked = 0

    def click(self) -> None:
        self.clicked += 1

    def inner_text(self) -> str:
        return self._text

    def query_selector(self, selector: str) -> _FakeElement | None:
        return self._query_results.get(selector)


class _FakePage:
    def __init__(self, responses: list[object] | None = None) -> None:
        self.keyboard = _FakeKeyboard()
        self._responses = list(responses or [])
        self.selector_calls: list[tuple[str, str | None, int | None]] = []
        self.waits: list[int] = []

    def wait_for_selector(
        self,
        selector: str,
        *,
        state: str | None = None,
        timeout: int | None = None,
    ) -> object:
        self.selector_calls.append((selector, state, timeout))
        if self._responses:
            outcome = self._responses.pop(0)
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome
        return _FakeElement()

    def wait_for_timeout(self, ms: int) -> None:
        self.waits.append(ms)


@pytest.mark.parametrize(
    ("helper", "expected_key", "expected_wait"),
    [
        (debug.start_debug, keyboard.START_DEBUG, 2000),
        (debug.stop_debug, keyboard.STOP_DEBUG, 500),
        (debug.step_over, keyboard.STEP_OVER, 300),
        (debug.step_into, keyboard.STEP_INTO, 300),
        (panel.toggle_panel, keyboard.TOGGLE_PANEL, 300),
        (panel.focus_problems, keyboard.FOCUS_PROBLEMS, 300),
        (panel.focus_output, keyboard.FOCUS_OUTPUT, 300),
        (sidebar.toggle_sidebar, keyboard.TOGGLE_SIDEBAR, 300),
        (sidebar.open_explorer, keyboard.FOCUS_EXPLORER, 300),
        (sidebar.open_search, keyboard.FOCUS_SEARCH, 300),
        (sidebar.open_source_control, keyboard.FOCUS_SOURCE_CONTROL, 300),
        (sidebar.open_debug, keyboard.FOCUS_DEBUG, 300),
        (sidebar.open_extensions_view, keyboard.FOCUS_EXTENSIONS, 300),
        (terminal.toggle_terminal, keyboard.TOGGLE_TERMINAL, 500),
        (terminal.new_terminal, keyboard.NEW_TERMINAL, 1000),
        (settings.open_settings, keyboard.OPEN_SETTINGS, 1000),
        (settings.toggle_fullscreen, keyboard.TOGGLE_FULLSCREEN, 500),
        (editor.new_untitled_file, keyboard.NEW_FILE, 500),
        (editor.save_file, keyboard.SAVE_FILE, 500),
        (editor.close_active_editor, keyboard.CLOSE_EDITOR, 300),
        (editor.go_to_definition, keyboard.GO_TO_DEFINITION, 1000),
        (editor.trigger_suggest, keyboard.TRIGGER_SUGGEST, 1000),
        (editor.select_all, keyboard.SELECT_ALL, 200),
    ],
)
def test_shortcut_helpers_press_expected_keys(
    helper,
    expected_key: str,
    expected_wait: int,
) -> None:
    page = _FakePage()

    helper(page)

    assert page.keyboard.presses == [expected_key]
    assert page.waits == [expected_wait]


@pytest.mark.parametrize(
    ("call_helper", "expected_command", "expected_followup", "expected_wait"),
    [
        (
            lambda page: debug.add_breakpoint_via_command(page),
            "Debug: Toggle Breakpoint",
            False,
            300,
        ),
        (
            lambda page: panel.open_problems(page),
            "View: Toggle Problems",
            False,
            300,
        ),
        (
            lambda page: panel.open_output(page),
            "View: Toggle Output",
            False,
            300,
        ),
        (
            lambda page: panel.open_debug_console(page),
            "View: Debug Console",
            False,
            300,
        ),
        (
            lambda page: sidebar.open_view_by_command(page, "Custom View"),
            "View: Show Custom View",
            False,
            300,
        ),
        (
            lambda page: terminal.new_terminal_via_command(page),
            "Terminal: Create New Terminal",
            False,
            1000,
        ),
        (
            lambda page: settings.open_settings_json(page),
            "Preferences: Open User Settings (JSON)",
            False,
            1000,
        ),
        (
            lambda page: editor.close_all_editors(page),
            "View: Close All Editors",
            False,
            300,
        ),
    ],
)
def test_command_wrapper_helpers_run_expected_command(
    monkeypatch,
    call_helper,
    expected_command: str,
    expected_followup: bool,
    expected_wait: int,
) -> None:
    commands_run: list[tuple[str, bool]] = []

    def fake_run_command(
        page: object,
        command_text: str,
        *,
        expect_followup_quick_input: bool = False,
    ) -> None:
        _ = page
        commands_run.append((command_text, expect_followup_quick_input))

    monkeypatch.setattr(debug, "run_command", fake_run_command)
    monkeypatch.setattr(panel, "run_command", fake_run_command)
    monkeypatch.setattr(sidebar, "run_command", fake_run_command)
    monkeypatch.setattr(terminal, "run_command", fake_run_command)
    monkeypatch.setattr(settings, "run_command", fake_run_command)
    monkeypatch.setattr(editor, "run_command", fake_run_command)

    page = _FakePage()
    call_helper(page)

    assert commands_run == [(expected_command, expected_followup)]
    assert page.waits == [expected_wait]


def test_debug_create_launch_json_uses_followup_picker(monkeypatch) -> None:
    commands_run: list[tuple[str, bool]] = []

    def fake_run_command(
        page: object,
        command_text: str,
        *,
        expect_followup_quick_input: bool = False,
    ) -> None:
        _ = page
        commands_run.append((command_text, expect_followup_quick_input))

    monkeypatch.setattr(debug, "run_command", fake_run_command)
    page = _FakePage()

    debug.create_launch_json(page, "python")

    assert commands_run == [("Debug: Open launch.json", True)]
    assert page.keyboard.typed == [("python", 30)]
    assert page.keyboard.presses == ["Enter"]
    assert page.waits == [1000, 500, 1000]


def test_run_debug_session_wraps_wait_with_start_and_stop() -> None:
    page = _FakePage()

    debug.run_debug_session(page, wait_ms=1234)

    assert page.keyboard.presses == [keyboard.START_DEBUG, keyboard.STOP_DEBUG]
    assert page.waits == [2000, 1234, 500]


@pytest.mark.parametrize(
    ("press_enter", "expected_presses"), [(True, ["Enter"]), (False, [])]
)
def test_type_in_terminal_honors_press_enter(
    press_enter: bool,
    expected_presses: list[str],
) -> None:
    page = _FakePage()

    terminal.type_in_terminal(page, "git status", press_enter=press_enter)

    assert page.keyboard.typed == [("git status", 20)]
    assert page.keyboard.presses == expected_presses
    assert page.waits == ([300] if press_enter else [])


def test_settings_search_setting_uses_first_available_search_box() -> None:
    search_box = _FakeElement()
    page = _FakePage(
        [
            settings.PlaywrightTimeoutError("missing first selector"),
            None,
            search_box,
        ]
    )

    settings.search_setting(page, "python")

    assert len(page.selector_calls) == 3
    assert search_box.clicked == 1
    assert page.keyboard.presses == [keyboard.SELECT_ALL]
    assert page.keyboard.typed == [("python", 30)]
    assert page.waits == [500]


def test_settings_search_setting_falls_back_to_local_find() -> None:
    page = _FakePage(
        [
            settings.PlaywrightTimeoutError("missing"),
            settings.PlaywrightTimeoutError("missing"),
            settings.PlaywrightTimeoutError("missing"),
        ]
    )

    settings.search_setting(page, "font size")

    assert page.keyboard.presses == ["Control+KeyF", keyboard.SELECT_ALL]
    assert page.keyboard.typed == [("font size", 30)]
    assert page.waits == [300, 500]


def test_settings_change_theme_waits_for_picker_to_close(monkeypatch) -> None:
    commands_run: list[tuple[str, bool]] = []
    hidden_waits: list[int] = []

    def fake_run_command(
        page: object,
        command_text: str,
        *,
        expect_followup_quick_input: bool = False,
    ) -> None:
        _ = page
        commands_run.append((command_text, expect_followup_quick_input))

    monkeypatch.setattr(settings, "run_command", fake_run_command)
    monkeypatch.setattr(
        settings,
        "wait_for_quick_input_hidden",
        lambda page, timeout_ms=5000: hidden_waits.append(timeout_ms),
    )
    page = _FakePage()

    settings.change_theme(page, "Default Light Modern")

    assert commands_run == [("Preferences: Color Theme", True)]
    assert page.keyboard.typed == [("Default Light Modern", 30)]
    assert page.keyboard.presses == ["Enter"]
    assert hidden_waits == [3000]
    assert page.waits == [800, 1000]


def test_toggle_setting_via_json_appends_and_saves(monkeypatch) -> None:
    opened: list[str] = []
    monkeypatch.setattr(
        settings, "open_settings_json", lambda page: opened.append("open")
    )
    page = _FakePage()

    settings.toggle_setting_via_json(page, "editor.fontSize", "16")

    assert opened == ["open"]
    assert page.keyboard.presses == [
        "Control+a",
        "Control+End",
        "ArrowUp",
        "End",
        keyboard.SAVE_FILE,
        keyboard.CLOSE_EDITOR,
    ]
    assert page.keyboard.typed == [(',\n    "editor.fontSize": 16', 15)]
    assert page.waits == [800, 200, 200, 300, 1000, 300]


def test_write_settings_batch_short_circuits_when_empty(monkeypatch) -> None:
    opened: list[str] = []
    monkeypatch.setattr(
        settings, "open_settings_json", lambda page: opened.append("open")
    )

    settings.write_settings_batch(_FakePage(), [])

    assert opened == []


def test_write_settings_batch_writes_all_settings_in_one_open(monkeypatch) -> None:
    opened: list[str] = []
    monkeypatch.setattr(
        settings, "open_settings_json", lambda page: opened.append("open")
    )
    page = _FakePage()

    settings.write_settings_batch(
        page,
        [
            ("editor.fontSize", "16"),
            ("editor.wordWrap", '"on"'),
        ],
    )

    assert opened == ["open"]
    assert page.keyboard.typed == [
        (',\n    "editor.fontSize": 16', 15),
        (',\n    "editor.wordWrap": "on"', 15),
    ]
    assert page.keyboard.presses == [
        "Control+End",
        "ArrowUp",
        "End",
        "Control+End",
        "ArrowUp",
        "End",
        keyboard.SAVE_FILE,
        keyboard.CLOSE_EDITOR,
    ]
    assert page.waits == [800, 200, 300, 200, 300, 1000, 300]


def test_editor_type_open_format_and_rename_use_expected_helpers(monkeypatch) -> None:
    quick_opened: list[str] = []
    commands_run: list[str] = []
    dismissed: list[str] = []

    monkeypatch.setattr(
        editor, "quick_open", lambda page, filename: quick_opened.append(filename)
    )
    monkeypatch.setattr(
        editor, "run_command", lambda page, command: commands_run.append(command)
    )
    monkeypatch.setattr(
        editor, "_dismiss_notification", lambda page: dismissed.append("dismissed")
    )
    page = _FakePage()

    editor.type_in_editor(page, "print('ok')\n")
    editor.open_file_by_name(page, "src/app.py")
    editor.format_document(page)
    editor.rename_symbol(page, "health_check")

    assert quick_opened == ["src/app.py"]
    assert commands_run == []
    assert dismissed == ["dismissed"]
    assert page.keyboard.presses == [
        keyboard.FOCUS_EDITOR,
        keyboard.FORMAT_DOCUMENT,
        keyboard.RENAME_SYMBOL,
        keyboard.SELECT_ALL,
        "Enter",
    ]
    assert page.keyboard.typed == [("print('ok')\n", 10), ("health_check", 20)]
    assert page.waits == [200, 1000, 500, 300, 1000]


def test_editor_save_file_as_uses_xdotool(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(args: list[str], *, check: bool) -> None:
        assert check is True
        calls.append(args)

    monkeypatch.setattr(editor.subprocess, "run", fake_run)
    page = _FakePage()

    editor.save_file_as(page, "report.txt")

    assert page.keyboard.presses == [keyboard.SAVE_FILE_AS]
    assert calls == [
        ["xdotool", "key", "ctrl+a"],
        ["xdotool", "type", "--delay", "30", "report.txt"],
        ["xdotool", "key", "Return"],
    ]
    assert page.waits == [1500, 300, 1000]


def test_editor_dismiss_notification_prefers_close_button() -> None:
    close_button = _FakeElement()
    toast = _FakeElement(
        text="No formatter installed",
        query_results={
            ".codicon-notifications-clear, .codicon-close": close_button,
        },
    )
    page = _FakePage([toast])

    result = editor._dismiss_notification(page)

    assert result == "No formatter installed"
    assert close_button.clicked == 1
    assert page.waits == [300]


def test_editor_dismiss_notification_falls_back_to_cancel() -> None:
    cancel_button = _FakeElement()
    toast = _FakeElement(
        text="Install recommended extensions?",
        query_results={
            "a.action-label[title='Cancel']": cancel_button,
        },
    )
    page = _FakePage([toast])

    result = editor._dismiss_notification(page)

    assert result == "Install recommended extensions?"
    assert cancel_button.clicked == 1
    assert page.waits == [300]


def test_editor_dismiss_notification_escapes_when_no_toast_is_visible() -> None:
    page = _FakePage(
        [
            editor.PlaywrightTimeoutError("missing"),
            editor.PlaywrightTimeoutError("missing"),
        ]
    )

    result = editor._dismiss_notification(page)

    assert result == ""
    assert page.keyboard.presses == ["Escape"]
    assert page.waits == [200]


def test_vscode_connect_wait_until_ready_and_disconnect() -> None:
    browser_page = _FakePage()
    browser = SimpleNamespace(
        contexts=[SimpleNamespace(pages=[browser_page])],
        closed=False,
    )

    def close() -> None:
        browser.closed = True

    browser.close = close
    captured_urls: list[str] = []

    def connect_over_cdp(url: str) -> object:
        captured_urls.append(url)
        return browser

    playwright = SimpleNamespace(
        chromium=SimpleNamespace(connect_over_cdp=connect_over_cdp)
    )

    connected_browser, connected_page = vscode.connect(playwright)
    vscode.wait_until_ready(browser_page, timeout_ms=4321)
    vscode.disconnect(connected_browser)

    assert connected_browser is browser
    assert connected_page is browser_page
    assert captured_urls == [vscode.CDP_URL]
    assert browser_page.selector_calls == [(".monaco-workbench", "visible", 4321)]
    assert browser.closed is True


def test_summarize_extension_host_logs_counts_only_new_bytes(tmp_path: Path) -> None:
    existing_log = tmp_path / "exthost.log"
    existing_log.write_text("abcdef")
    missing_log = tmp_path / "missing.log"

    summary = capture.summarize_extension_host_logs(
        {
            str(existing_log.resolve()): 2,
            str(missing_log.resolve()): 0,
        },
        [existing_log, missing_log],
    )

    assert summary == {
        "extension_host_log_found": True,
        "extension_host_log_present": True,
        "post_start_bytes": 4,
    }


def test_summarize_extension_host_logs_handles_no_logs() -> None:
    assert capture.summarize_extension_host_logs({}, []) == {
        "extension_host_log_found": False,
        "extension_host_log_present": False,
        "post_start_bytes": 0,
    }


def test_load_trigger_file_returns_none_for_missing_path(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.json"

    assert triggers.load_trigger_file(str(missing_path)) is None


def test_load_trigger_file_rejects_invalid_or_non_object_json(tmp_path: Path) -> None:
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{bad json")

    assert triggers.load_trigger_file(str(invalid_json)) is None
    assert not invalid_json.exists()

    non_object_json = tmp_path / "list.json"
    non_object_json.write_text(json.dumps(["not", "an", "object"]))

    assert triggers.load_trigger_file(str(non_object_json)) is None
    assert not non_object_json.exists()


def test_load_trigger_file_returns_payload_and_cleans_up(tmp_path: Path) -> None:
    trigger_path = tmp_path / "trigger.json"
    trigger_path.write_text(
        json.dumps(
            {
                "analysis_profile": "focused",
                "selected_scenarios": ["terminal_usage"],
                "official_selected_scenarios": ["terminal_usage"],
                "command_targets": {"Test: Command": "test.command"},
                "extra_commands": ["workbench.action.tasks.runTask"],
                "run_task_trigger": True,
                "heuristic_workflow_coverage": {"terminal_tasks": "covered"},
            }
        )
    )

    payload = triggers.load_trigger_file(str(trigger_path))

    assert payload is not None
    assert payload.analysis_profile == "focused"
    assert payload.selected_scenarios == ["terminal_usage"]
    assert payload.command_targets == {"Test: Command": "test.command"}
    assert payload.extra_commands == ["workbench.action.tasks.runTask"]
    assert payload.run_task_trigger is True
    assert payload.heuristic_workflow_coverage == {"terminal_tasks": "covered"}
    assert not trigger_path.exists()


def test_scenario_terminal_usage_runs_expected_commands(monkeypatch) -> None:
    terminal_calls: list[tuple[str, Any]] = []

    monkeypatch.setattr(automation, "_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        automation.terminal,
        "new_terminal",
        lambda page: terminal_calls.append(("new_terminal", None)),
    )
    monkeypatch.setattr(
        automation.terminal,
        "type_in_terminal",
        lambda page, text, press_enter=True: terminal_calls.append(
            ("type_in_terminal", (text, press_enter))
        ),
    )
    page = _FakePage()

    automation.scenario_terminal_usage(page)

    assert terminal_calls == [
        ("new_terminal", None),
        ("type_in_terminal", ("ls -la", True)),
        ("type_in_terminal", ("cat .env", True)),
        ("type_in_terminal", ("git status", True)),
        ("type_in_terminal", ("python --version", True)),
        ("type_in_terminal", ("node --version", True)),
        ("type_in_terminal", ("pip list", True)),
        ("type_in_terminal", ("npm ls --depth=0", True)),
        ("type_in_terminal", ("echo $PATH", True)),
        ("new_terminal", None),
        ("type_in_terminal", ("pwd", True)),
    ]


def test_scenario_settings_modification_calls_helper_layers(monkeypatch) -> None:
    actions: list[tuple[str, Any]] = []

    monkeypatch.setattr(automation, "_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        automation.settings,
        "write_settings_batch",
        lambda page, values: actions.append(("write_settings_batch", values)),
    )
    monkeypatch.setattr(
        automation.settings,
        "change_theme",
        lambda page, theme: actions.append(("change_theme", theme)),
    )
    monkeypatch.setattr(
        automation.settings,
        "open_settings",
        lambda page: actions.append(("open_settings", None)),
    )
    monkeypatch.setattr(
        automation.settings,
        "search_setting",
        lambda page, query: actions.append(("search_setting", query)),
    )
    monkeypatch.setattr(
        automation.settings,
        "toggle_fullscreen",
        lambda page: actions.append(("toggle_fullscreen", None)),
    )
    monkeypatch.setattr(
        automation.editor,
        "close_active_editor",
        lambda page: actions.append(("close_active_editor", None)),
    )
    page = _FakePage()

    automation.scenario_settings_modification(page)

    assert actions == [
        (
            "write_settings_batch",
            [
                ("editor.fontSize", "16"),
                ("editor.formatOnSave", "true"),
                ("editor.wordWrap", '"on"'),
                ("editor.minimap.enabled", "false"),
            ],
        ),
        ("change_theme", "Default Light Modern"),
        ("change_theme", "Default Dark Modern"),
        ("open_settings", None),
        ("search_setting", "font size"),
        ("search_setting", "format on save"),
        ("close_active_editor", None),
        ("toggle_fullscreen", None),
        ("toggle_fullscreen", None),
    ]


def test_scenario_project_exploration_closes_editors_in_batches(monkeypatch) -> None:
    opened_files: list[str] = []
    close_all_calls: list[str] = []
    explorer_calls: list[str] = []

    monkeypatch.setattr(automation, "_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        automation.sidebar,
        "open_explorer",
        lambda page: explorer_calls.append("open_explorer"),
    )
    monkeypatch.setattr(
        automation.editor,
        "open_file_by_name",
        lambda page, filename: opened_files.append(filename),
    )
    monkeypatch.setattr(
        automation.editor,
        "close_all_editors",
        lambda page: close_all_calls.append("close_all_editors"),
    )
    page = _FakePage()

    automation.scenario_project_exploration(page)

    assert explorer_calls == ["open_explorer"]
    assert len(opened_files) == 15
    assert opened_files[0] == "src/app.py"
    assert opened_files[-1] == "config/settings.xml"
    assert close_all_calls == [
        "close_all_editors",
        "close_all_editors",
        "close_all_editors",
        "close_all_editors",
    ]


def test_recover_ui_state_restores_focus(monkeypatch) -> None:
    dismissed: list[str] = []

    monkeypatch.setattr(
        automation.editor,
        "_dismiss_notification",
        lambda page: dismissed.append("dismissed"),
    )
    monkeypatch.setattr(automation, "_log", lambda *args, **kwargs: None)
    page = _FakePage()

    automation._recover_ui_state(page)

    assert dismissed == ["dismissed"]
    assert page.keyboard.presses == [
        "Escape",
        "Escape",
        "Escape",
        keyboard.FOCUS_EDITOR,
    ]
    assert page.waits == [200, 200, 200, 300]


def test_cleanup_between_scenarios_closes_editors_terminals_and_panel(
    monkeypatch,
) -> None:
    commands_run: list[str] = []
    dismissed: list[str] = []

    monkeypatch.setattr(
        automation.commands,
        "run_command",
        lambda page, command_text: commands_run.append(command_text),
    )
    monkeypatch.setattr(
        automation.editor,
        "_dismiss_notification",
        lambda page: dismissed.append("dismissed"),
    )
    monkeypatch.setattr(automation, "_log", lambda *args, **kwargs: None)
    page = _FakePage()

    automation._cleanup_between_scenarios(page)

    assert commands_run == ["Terminal: Kill All Terminals"]
    assert dismissed == ["dismissed"]
    assert page.keyboard.presses == [
        "Control+KeyK",
        "Control+KeyW",
        keyboard.TOGGLE_PANEL,
        "Escape",
        keyboard.FOCUS_EDITOR,
    ]
    assert page.waits == [100, 500, 500, 200, 200]


def test_kill_all_terminals_ignores_playwright_errors(monkeypatch) -> None:
    monkeypatch.setattr(
        automation.commands,
        "run_command",
        lambda page, command_text: (_ for _ in ()).throw(
            automation.PlaywrightError("terminal missing")
        ),
    )

    automation._kill_all_terminals(_FakePage())
