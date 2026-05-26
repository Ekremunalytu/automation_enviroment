from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from executor.flows.playwright.vscode import keyboard as keyboard
import pytest

from executor.flows.playwright import (
    automation,
    capture,
    triggers,
    vscode,
)
from executor.flows.playwright.vscode import commands as commands
from executor.flows.playwright.vscode import debug as debug
from executor.flows.playwright.vscode import editor as editor
from executor.flows.playwright.vscode import panel as panel
from executor.flows.playwright.vscode import settings as settings
from executor.flows.playwright.vscode import sidebar as sidebar
from executor.flows.playwright.vscode import terminal as terminal


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
    def __init__(
        self,
        responses: list[object] | None = None,
        *,
        title: str = "[Extension Development Host] Running Extensions - workspace - Visual Studio Code",
        url: str = "vscode-file://vscode-app/usr/share/code/resources/app/out/vs/code/electron-browser/workbench/workbench.html",
    ) -> None:
        self.keyboard = _FakeKeyboard()
        self._responses = list(responses or [])
        self._title = title
        self.url = url
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

    def title(self) -> str:
        return self._title


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


def _settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "settings.json"
    monkeypatch.setenv("EXTRACE_VSCODE_SETTINGS_JSON", str(target))
    return target


def test_toggle_setting_via_json_merges_key_into_existing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _settings_path(tmp_path, monkeypatch)
    target.write_text(
        json.dumps({"telemetry.telemetryLevel": "off"}) + "\n",
        encoding="utf-8",
    )
    page = _FakePage()

    settings.toggle_setting_via_json(page, "editor.fontSize", "16")

    assert json.loads(target.read_text(encoding="utf-8")) == {
        "telemetry.telemetryLevel": "off",
        "editor.fontSize": 16,
    }
    # Helper never touches the Monaco buffer anymore — no keyboard events,
    # no command-palette open, no save shortcut.
    assert page.keyboard.presses == []
    assert page.keyboard.typed == []
    assert page.waits == [1000]


def test_write_settings_batch_short_circuits_when_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _settings_path(tmp_path, monkeypatch)
    target.write_text(json.dumps({"existing": True}) + "\n", encoding="utf-8")

    settings.write_settings_batch(_FakePage(), [])

    # File left untouched.
    assert json.loads(target.read_text(encoding="utf-8")) == {"existing": True}


def test_write_settings_batch_preserves_baseline_and_merges_all_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _settings_path(tmp_path, monkeypatch)
    baseline = {
        "security.workspace.trust.enabled": False,
        "workbench.startupEditor": "none",
        "telemetry.telemetryLevel": "off",
    }
    target.write_text(json.dumps(baseline) + "\n", encoding="utf-8")
    page = _FakePage()

    settings.write_settings_batch(
        page,
        [
            ("editor.fontSize", "16"),
            ("editor.formatOnSave", "true"),
            ("editor.wordWrap", '"on"'),
            ("editor.minimap.enabled", "false"),
        ],
    )

    merged = json.loads(target.read_text(encoding="utf-8"))
    # Baseline survives.
    assert merged["security.workspace.trust.enabled"] is False
    assert merged["workbench.startupEditor"] == "none"
    assert merged["telemetry.telemetryLevel"] == "off"
    # New keys merged with their JSON-parsed values.
    assert merged["editor.fontSize"] == 16
    assert merged["editor.formatOnSave"] is True
    assert merged["editor.wordWrap"] == "on"
    assert merged["editor.minimap.enabled"] is False
    # One timeout to let the VS Code file watcher propagate changes.
    assert page.waits == [1000]


def test_write_settings_batch_creates_file_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _settings_path(tmp_path, monkeypatch)
    assert not target.exists()

    settings.write_settings_batch(_FakePage(), [("editor.fontSize", "14")])

    assert json.loads(target.read_text(encoding="utf-8")) == {"editor.fontSize": 14}


def test_write_settings_batch_refuses_to_overwrite_corrupted_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _settings_path(tmp_path, monkeypatch)
    corrupted = '{\n  "valid": true\n},\n    "editor.fontSize": 16\n'
    target.write_text(corrupted, encoding="utf-8")
    page = _FakePage()

    settings.write_settings_batch(page, [("editor.fontSize", "20")])

    # Helper must bail rather than compound the damage.
    assert target.read_text(encoding="utf-8") == corrupted
    assert page.waits == [500]


def test_write_settings_batch_output_is_valid_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Round-trip invariant: whatever we write must parse cleanly."""
    target = _settings_path(tmp_path, monkeypatch)

    settings.write_settings_batch(
        _FakePage(),
        [
            ("editor.fontSize", "16"),
            ("editor.wordWrap", '"on"'),
            ("editor.rulers", "[80, 120]"),
        ],
    )

    # Parses without error and round-trips the keys.
    parsed = json.loads(target.read_text(encoding="utf-8"))
    assert parsed == {
        "editor.fontSize": 16,
        "editor.wordWrap": "on",
        "editor.rulers": [80, 120],
    }


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


def test_vscode_connect_prefers_workbench_page_over_devtools() -> None:
    devtools_page = _FakePage(title="DevTools", url="devtools://devtools/bundled/")
    workbench_page = _FakePage()
    browser = SimpleNamespace(
        contexts=[SimpleNamespace(pages=[devtools_page, workbench_page])],
    )

    playwright = SimpleNamespace(
        chromium=SimpleNamespace(connect_over_cdp=lambda _url: browser)
    )

    connected_browser, connected_page = vscode.connect(playwright)

    assert connected_browser is browser
    assert connected_page is workbench_page


def test_vscode_connect_reports_discovered_pages_when_workbench_is_missing() -> None:
    devtools_page = _FakePage(title="DevTools", url="devtools://devtools/bundled/")
    browser = SimpleNamespace(
        contexts=[SimpleNamespace(pages=[devtools_page])],
    )

    playwright = SimpleNamespace(
        chromium=SimpleNamespace(connect_over_cdp=lambda _url: browser)
    )

    with pytest.raises(RuntimeError) as exc_info:
        vscode.connect(playwright)

    message = str(exc_info.value)
    assert "Could not find a VS Code workbench page via CDP" in message
    assert "DevTools" in message
    assert "devtools://devtools/bundled/" in message


def test_vscode_reconnect_to_workbench_retries_until_fallback_page_is_ready(
    monkeypatch,
) -> None:
    primary_page = _FakePage(title="Primary", url="vscode-file://primary")
    fallback_page = _FakePage()
    browser = SimpleNamespace(contexts=[SimpleNamespace(pages=[fallback_page])])
    wait_calls: list[tuple[object, int]] = []
    sleep_calls: list[float] = []
    attempts = {"count": 0}

    def fake_wait_until_ready(page: object, timeout_ms: int = 10_000) -> None:
        wait_calls.append((page, timeout_ms))
        if page is primary_page:
            raise vscode.PlaywrightError("page detached")
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise vscode.PlaywrightError("workbench not ready yet")

    monkeypatch.setattr(vscode, "wait_until_ready", fake_wait_until_ready)
    monkeypatch.setattr(
        vscode.time, "sleep", lambda seconds: sleep_calls.append(seconds)
    )

    reloaded_page = vscode.reconnect_to_workbench(
        browser,
        preferred_page=primary_page,
        timeout_ms=5_000,
        probe_timeout_ms=250,
        poll_interval_ms=100,
    )

    assert reloaded_page is fallback_page
    assert wait_calls == [
        (primary_page, 250),
        (fallback_page, 250),
        (primary_page, 250),
        (fallback_page, 250),
    ]
    assert sleep_calls == [0.1]


def test_vscode_connect_to_ready_workbench_uses_timeout_and_logs() -> None:
    page = _FakePage()
    browser = SimpleNamespace(contexts=[SimpleNamespace(pages=[page])])
    captured_calls: list[tuple[str, int]] = []
    reload_logs: list[str] = []

    def connect_over_cdp(url: str, *, timeout: int) -> object:
        captured_calls.append((url, timeout))
        return browser

    playwright = SimpleNamespace(
        chromium=SimpleNamespace(connect_over_cdp=connect_over_cdp)
    )

    connected_browser, connected_page = vscode.connect_to_ready_workbench(
        playwright,
        timeout_ms=4321,
        log=reload_logs.append,
    )

    assert connected_browser is browser
    assert connected_page is page
    assert captured_calls == [(vscode.CDP_URL, 4321)]
    assert reload_logs == [
        f"[reload] connect: Connecting to VS Code over CDP at {vscode.CDP_URL}...",
        (
            "[reload] connect: Connected to ready workbench page "
            "title='[Extension Development Host] Running Extensions - workspace - Visual Studio Code' "
            "url='vscode-file://vscode-app/usr/share/code/resources/app/out/vs/code/electron-browser/workbench/workbench.html'."
        ),
    ]


def test_vscode_connect_to_ready_workbench_fails_closed_when_cdp_connect_fails() -> (
    None
):
    playwright = SimpleNamespace(
        chromium=SimpleNamespace(
            connect_over_cdp=lambda _url, *, timeout: (_ for _ in ()).throw(
                vscode.PlaywrightError("connection refused")
            )
        )
    )

    with pytest.raises(vscode.ReloadWindowError, match="connect: Could not connect"):
        vscode.connect_to_ready_workbench(playwright, timeout_ms=5000)


def test_vscode_reload_workbench_window_logs_and_reuses_primary_page(
    monkeypatch,
) -> None:
    page = _FakePage()
    browser = SimpleNamespace(contexts=[SimpleNamespace(pages=[page])])
    ready_calls: list[tuple[object, int]] = []
    reconnect_calls: list[tuple[object, object, int]] = []
    command_calls: list[object] = []
    reload_logs: list[str] = []

    monkeypatch.setattr(
        vscode,
        "wait_until_ready",
        lambda current_page, timeout_ms=10_000: ready_calls.append(
            (current_page, timeout_ms)
        ),
    )
    monkeypatch.setattr(
        commands,
        "run_reload_window_command",
        lambda current_page: command_calls.append(current_page),
    )
    monkeypatch.setattr(
        vscode,
        "reconnect_to_workbench",
        lambda current_browser, *, preferred_page, timeout_ms=30_000: (
            reconnect_calls.append((current_browser, preferred_page, timeout_ms))
            or preferred_page
        ),
    )

    reloaded_page = vscode.reload_workbench_window(
        browser,
        page,
        reconnect_timeout_ms=7654,
        log=reload_logs.append,
    )

    assert reloaded_page is page
    assert ready_calls == [(page, 10_000)]
    assert command_calls == [page]
    assert reconnect_calls == [(browser, page, 7654)]
    assert page.waits == [3000, 5000]
    assert reload_logs == [
        "[reload] pre_ready: Waiting for VS Code workbench before reload...",
        "[reload] dispatch: Sending 'Developer: Reload Window' command...",
        "[reload] reconnect: Waiting 3000ms for VS Code to tear down before reconnect...",
        "[reload] reconnect: Reconnecting to a ready VS Code workbench...",
        "[reload] reconnect: Connected to the preferred workbench page.",
        "[reload] post_settle: Waiting 5000ms for extensions to settle after reload...",
        "[reload] done: VS Code reload completed.",
    ]


def test_vscode_reload_workbench_window_rewrites_harness_secret_before_dispatch(
    monkeypatch,
) -> None:
    """W19-X: ``reload_workbench_window`` must call ``_rewrite_harness_secret``
    before dispatching ``run_reload_window_command`` so the reactivating
    Extension Host can read a fresh per-launch HMAC secret on its activate().
    Without this wiring, reload reactivations read ENOENT, emit unsigned
    markers, and the verifier rejects onDebug* attempts as unverified."""
    call_order: list[str] = []
    page = _FakePage()
    browser = SimpleNamespace(contexts=[SimpleNamespace(pages=[page])])

    monkeypatch.setattr(
        vscode,
        "wait_until_ready",
        lambda *_a, **_k: call_order.append("wait_until_ready"),
    )
    monkeypatch.setattr(
        vscode,
        "_rewrite_harness_secret",
        lambda log=None: call_order.append("rewrite_harness_secret"),
    )
    monkeypatch.setattr(
        commands,
        "run_reload_window_command",
        lambda _current_page: call_order.append("run_reload_window_command"),
    )
    monkeypatch.setattr(
        vscode,
        "reconnect_to_workbench",
        lambda current_browser, *, preferred_page, timeout_ms=30_000: preferred_page,
    )

    vscode.reload_workbench_window(browser, page)

    rewrite_idx = call_order.index("rewrite_harness_secret")
    dispatch_idx = call_order.index("run_reload_window_command")
    assert rewrite_idx < dispatch_idx, (
        f"rewrite must precede reload dispatch; got order {call_order}"
    )


def test_vscode_rewrite_harness_secret_noop_when_launch_script_absent(
    monkeypatch, tmp_path
) -> None:
    """W19-X: ``_rewrite_harness_secret`` must be a no-op when the launch
    script is absent (e.g. test/host environments without the executor
    container layout). Otherwise unit tests that exercise the reload helper
    would fail trying to invoke a non-existent bash script."""
    monkeypatch.setattr(vscode, "_VSCODE_LAUNCH_SCRIPT", str(tmp_path / "missing.sh"))
    subprocess_calls: list[object] = []
    monkeypatch.setattr(
        vscode.subprocess,
        "run",
        lambda *a, **k: subprocess_calls.append((a, k)),
    )

    vscode._rewrite_harness_secret()

    assert subprocess_calls == []


def test_vscode_rewrite_harness_secret_invokes_subprocess_when_script_exists(
    monkeypatch, tmp_path
) -> None:
    """W19-X: when the launch script is present, ``_rewrite_harness_secret``
    invokes ``bash launch_vscode.sh --secret-only`` so the running VS Code's
    next reactivation finds a fresh secret on disk. Mirrors the
    runtime contract; the actual subprocess is stubbed to keep the test
    hermetic."""
    fake_script = tmp_path / "launch_vscode.sh"
    fake_script.write_text("#!/bin/bash\nexit 0\n")
    monkeypatch.setattr(vscode, "_VSCODE_LAUNCH_SCRIPT", str(fake_script))

    captured: list[tuple] = []

    def fake_run(args, **kwargs):
        captured.append((tuple(args), kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(vscode.subprocess, "run", fake_run)

    vscode._rewrite_harness_secret()

    assert len(captured) == 1
    args, kwargs = captured[0]
    assert args == ("bash", str(fake_script), "--secret-only")
    assert kwargs.get("check") is False
    assert kwargs.get("timeout") == vscode._SECRET_REWRITE_TIMEOUT_S


def test_vscode_reload_workbench_window_uses_fallback_page(monkeypatch) -> None:
    primary_page = _FakePage(title="Primary", url="vscode-file://primary")
    fallback_page = _FakePage()
    browser = SimpleNamespace(contexts=[SimpleNamespace(pages=[fallback_page])])

    monkeypatch.setattr(vscode, "wait_until_ready", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        commands,
        "run_reload_window_command",
        lambda _current_page: None,
    )
    monkeypatch.setattr(
        vscode,
        "reconnect_to_workbench",
        lambda _current_browser, *, preferred_page, timeout_ms=30_000: fallback_page,
    )

    reloaded_page = vscode.reload_workbench_window(browser, primary_page)

    assert reloaded_page is fallback_page
    assert primary_page.waits == [3000]
    assert fallback_page.waits == [5000]


def test_vscode_reload_workbench_window_fails_closed_when_pre_ready_fails(
    monkeypatch,
) -> None:
    page = _FakePage()
    browser = SimpleNamespace(contexts=[SimpleNamespace(pages=[page])])
    command_calls: list[object] = []

    monkeypatch.setattr(
        vscode,
        "wait_until_ready",
        lambda _page, timeout_ms=10_000: (_ for _ in ()).throw(
            vscode.PlaywrightError("page detached")
        ),
    )
    monkeypatch.setattr(
        commands,
        "run_reload_window_command",
        lambda current_page: command_calls.append(current_page),
    )

    with pytest.raises(
        vscode.ReloadWindowError,
        match="pre_ready: VS Code workbench was not ready before reload: page detached",
    ):
        vscode.reload_workbench_window(browser, page)

    assert command_calls == []
    assert page.waits == []


def test_vscode_reload_workbench_window_fails_closed_when_reconnect_fails(
    monkeypatch,
) -> None:
    page = _FakePage()
    browser = SimpleNamespace(contexts=[SimpleNamespace(pages=[page])])
    command_calls: list[object] = []

    monkeypatch.setattr(vscode, "wait_until_ready", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        commands,
        "run_reload_window_command",
        lambda current_page: command_calls.append(current_page),
    )
    monkeypatch.setattr(
        vscode,
        "reconnect_to_workbench",
        lambda _current_browser, *, preferred_page, timeout_ms=30_000: (
            _ for _ in ()
        ).throw(
            RuntimeError("Timed out while reconnecting to a VS Code workbench page.")
        ),
    )

    with pytest.raises(
        vscode.ReloadWindowError,
        match="reconnect: Timed out while reconnecting to a VS Code workbench page",
    ):
        vscode.reload_workbench_window(browser, page)

    assert command_calls == [page]
    assert page.waits == [3000]


def test_vscode_reload_workbench_window_fails_closed_when_post_settle_fails(
    monkeypatch,
) -> None:
    page = _FakePage()
    fallback_page = _FakePage()
    browser = SimpleNamespace(contexts=[SimpleNamespace(pages=[fallback_page])])

    monkeypatch.setattr(vscode, "wait_until_ready", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        commands,
        "run_reload_window_command",
        lambda _current_page: None,
    )
    monkeypatch.setattr(
        vscode,
        "reconnect_to_workbench",
        lambda _current_browser, *, preferred_page, timeout_ms=30_000: fallback_page,
    )

    def fail_post_settle(timeout_ms: int) -> None:
        raise vscode.PlaywrightError("page closed")

    fallback_page.wait_for_timeout = fail_post_settle

    with pytest.raises(
        vscode.ReloadWindowError,
        match="post_settle: VS Code did not remain stable after reload: page closed",
    ):
        vscode.reload_workbench_window(browser, page)

    assert page.waits == [3000]


def test_run_reload_window_command_skips_quick_input_waits(monkeypatch) -> None:
    opened: list[str] = []
    page = _FakePage()

    def fake_open_command_palette(target_page: object) -> None:
        assert target_page is page
        opened.append("opened")

    monkeypatch.setattr(commands, "open_command_palette", fake_open_command_palette)
    commands.run_reload_window_command(page)

    assert opened == ["opened"]
    assert page.keyboard.typed == [("Developer: Reload Window", 30)]
    assert page.keyboard.presses == ["Enter"]
    assert page.waits == [500]


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
                "coverage_tracks": {},
                "coverage_summary": {},
                "event_attempts": [],
                "official_event_coverage": {},
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


def test_load_trigger_file_rejects_schema_invalid_object(tmp_path: Path) -> None:
    trigger_path = tmp_path / "invalid_object.json"
    trigger_path.write_text(json.dumps({"selected_scenarios": "not-a-list"}))

    assert triggers.load_trigger_file(str(trigger_path)) is None
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
        ("type_in_terminal", ("git status", True)),
        ("type_in_terminal", ("python --version", True)),
        ("type_in_terminal", ("node --version", True)),
        ("type_in_terminal", ("echo $PATH", True)),
        ("new_terminal", None),
        ("type_in_terminal", ("pwd", True)),
    ]
    assert ("type_in_terminal", ("cat .env", True)) not in terminal_calls
    assert ("type_in_terminal", ("pip list", True)) not in terminal_calls
    assert ("type_in_terminal", ("npm ls --depth=0", True)) not in terminal_calls


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
