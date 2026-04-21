from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar
from typing import Any

import pytest

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import entrypoint  # noqa: E402
import triggers as trigger_loader  # noqa: E402


class _FakeKeyboard:
    def __init__(self) -> None:
        self.presses: list[str] = []
        self.typed: list[tuple[str, int | None]] = []

    def press(self, key: str) -> None:
        self.presses.append(key)

    def type(self, text: str, delay: int | None = None) -> None:
        self.typed.append((text, delay))


class _FakePage:
    def __init__(self, title_text: str = "VS Code") -> None:
        self.keyboard = _FakeKeyboard()
        self.waits: list[int] = []
        self._title_text = title_text

    def wait_for_timeout(self, timeout_ms: int) -> None:
        self.waits.append(timeout_ms)

    def wait_for_selector(
        self, selector: str, state: str = "visible", timeout: int = 0
    ):
        _ = (selector, state, timeout)
        return None

    def title(self) -> str:
        return self._title_text


class _FakeBrowser:
    def __init__(self, pages: list[_FakePage] | None = None) -> None:
        self.contexts = [SimpleNamespace(pages=pages or [])]


class _FakeStoppedReport:
    def __init__(self) -> None:
        self.trigger_plan_requested = False
        self.trigger_plan_path = ""
        self.trigger_plan_applied = False
        self.trigger_execution_mode = ""
        self.scenarios_run: list[str] = []
        self.failed_scenarios: list[str] = []
        self.extra_trigger_failures: list[str] = []
        self.print_summary_calls = 0
        self.saved_paths: list[str] = []

    def print_summary(self) -> None:
        self.print_summary_calls += 1

    def save(self, path: str) -> None:
        self.saved_paths.append(path)


class _FakeMonitor:
    instances: ClassVar[list[_FakeMonitor]] = []

    def __init__(
        self, page: object, report_path: str, target_extension_id: str
    ) -> None:
        self.page = page
        self.report_path = report_path
        self.target_extension_id = target_extension_id
        self.report = _FakeStoppedReport()
        self.applied_payloads: list[object] = []
        self.automation_events: list[tuple[str, str, str, str, str]] = []
        self.missing_trigger_paths: list[str] = []
        self.applied_trigger_plans: list[tuple[list[str] | None, str | None]] = []
        self.execution_modes: list[str] = []
        self.failed_scenario_batches: list[list[str]] = []
        self.attach_runtime_tracers_calls = 0
        self.start_calls = 0
        self.stop_calls = 0
        self.snapshot_calls = 0
        self.verify_calls: list[dict[str, object]] = []
        self.scenario_events: list[tuple[str, str, str, dict[str, object] | None]] = []
        type(self).instances.append(self)

    def start(self) -> None:
        self.start_calls += 1

    def stop(self) -> _FakeStoppedReport:
        self.stop_calls += 1
        return self.report

    def record_scenario_event(
        self,
        action: str,
        name: str,
        status: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.scenario_events.append((action, name, status, metadata))

    def apply_trigger_payload(self, payload: object) -> None:
        self.applied_payloads.append(payload)
        self.report.trigger_plan_requested = True

    def record_automation_event(
        self,
        kind: str,
        message: str,
        status: str = "",
        scenario_name: str = "",
        activation_event: str = "",
    ) -> None:
        self.automation_events.append(
            (kind, message, status, scenario_name, activation_event)
        )

    def mark_trigger_plan_missing(self, trigger_path: str = "") -> None:
        self.missing_trigger_paths.append(trigger_path)
        self.report.trigger_plan_requested = True
        self.report.trigger_plan_path = trigger_path

    def mark_trigger_plan_applied(
        self,
        *,
        scenarios: list[str] | None = None,
        trigger_path: str | None = None,
    ) -> None:
        self.applied_trigger_plans.append((scenarios, trigger_path))
        self.report.trigger_plan_applied = True
        if trigger_path:
            self.report.trigger_plan_path = trigger_path

    def set_trigger_execution_mode(self, mode: str) -> None:
        self.execution_modes.append(mode)
        self.report.trigger_execution_mode = mode

    def attach_runtime_tracers(self) -> None:
        self.attach_runtime_tracers_calls += 1

    def record_failed_scenarios(self, failed_scenarios: list[str]) -> None:
        self.failed_scenario_batches.append(list(failed_scenarios))
        self.report.failed_scenarios = list(failed_scenarios)

    def capture_runtime_snapshot(self) -> dict[str, int]:
        self.snapshot_calls += 1
        return {"target_activations": self.snapshot_calls}

    def verify_target_reaction(
        self,
        baseline: dict[str, int | bool],
        *,
        capability: str,
        trigger_label: str,
        activation_event: str = "",
        success_signal: bool = False,
    ) -> bool:
        self.verify_calls.append(
            {
                "baseline": baseline,
                "capability": capability,
                "trigger_label": trigger_label,
                "activation_event": activation_event,
                "success_signal": success_signal,
            }
        )
        return True


class _FakePlaywrightContext:
    def __init__(self, payload: object = None) -> None:
        self.payload = payload if payload is not None else object()

    def __enter__(self) -> object:
        return self.payload

    def __exit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


def _configure_main_runtime(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    *,
    browser: _FakeBrowser | None = None,
    page: _FakePage | None = None,
) -> tuple[_FakeBrowser, _FakePage, list[tuple[object, int]], list[object]]:
    current_page = page or _FakePage()
    current_browser = browser or _FakeBrowser([current_page])
    wait_calls: list[tuple[object, int]] = []
    disconnect_calls: list[object] = []

    monkeypatch.setattr(sys, "argv", ["entrypoint.py", *argv])
    monkeypatch.setattr(
        entrypoint,
        "sync_playwright",
        lambda: _FakePlaywrightContext("playwright"),
    )
    monkeypatch.setattr(
        entrypoint.vscode,
        "connect",
        lambda playwright: (current_browser, current_page),
    )
    monkeypatch.setattr(
        entrypoint.vscode,
        "wait_until_ready",
        lambda ready_page, timeout_ms=10_000: wait_calls.append(
            (ready_page, timeout_ms)
        ),
    )
    monkeypatch.setattr(
        entrypoint.vscode,
        "disconnect",
        lambda browser_obj: disconnect_calls.append(browser_obj),
    )
    return current_browser, current_page, wait_calls, disconnect_calls


def test_resolve_execution_plan_prefers_layered_trigger_passes() -> None:
    payload = trigger_loader.TriggerPayload(
        selected_scenarios=["rename_symbol"],
        stimulus_passes=[
            {
                "pass_id": "workspace_bootstrap",
                "label": "workspace/bootstrap pass",
                "order": 1,
                "status": "planned",
            }
        ],
    )

    plan, scenarios = entrypoint._resolve_execution_plan(
        False,
        None,
        payload,
    )

    assert plan == "layered_passes"
    assert scenarios == ["rename_symbol"]


def test_resolve_execution_plan_uses_selected_scenarios_for_explicit_scenario() -> None:
    payload = trigger_loader.TriggerPayload(selected_scenarios=["rename_symbol"])

    plan, scenarios = entrypoint._resolve_execution_plan(
        False,
        "coding_session",
        payload,
    )

    assert plan == "selected_scenarios"
    assert scenarios == ["coding_session"]


def test_resolve_execution_plan_uses_single_scenario_fallback() -> None:
    plan, scenarios = entrypoint._resolve_execution_plan(
        False,
        "coding_session",
        None,
    )

    assert plan == "single_scenario"
    assert scenarios == ["coding_session"]


def test_resolve_execution_plan_runs_all_without_payload_or_fallback() -> None:
    plan, scenarios = entrypoint._resolve_execution_plan(
        False,
        None,
        None,
    )

    assert plan == "all_scenarios"
    assert scenarios == []


def test_resolve_execution_plan_supports_skip_automation_mode() -> None:
    plan, scenarios = entrypoint._resolve_execution_plan(
        True,
        None,
        None,
    )

    assert plan == "skip_automation"
    assert scenarios == []


def test_run_extra_triggers_runs_non_command_branches(monkeypatch) -> None:
    payload = trigger_loader.TriggerPayload(
        extra_custom_editor_files=["samples/report.drawio"],
        uri_trigger="vscode://publisher.tool/open",
        run_task_trigger=True,
        run_walkthrough_trigger=True,
    )
    events: list[tuple[str, str, str, str, str]] = []
    calls: list[tuple[str, Any]] = []
    page = _FakePage()

    def record_event(
        kind: str,
        message: str,
        status: str,
        scenario_name: str = "",
        activation_event: str = "",
    ) -> None:
        events.append((kind, message, status, scenario_name, activation_event))

    monkeypatch.setattr(
        entrypoint.editor,
        "open_file_by_name",
        lambda current_page, filename: calls.append(("open_file", filename)),
    )
    monkeypatch.setattr(
        entrypoint.editor,
        "close_active_editor",
        lambda current_page: calls.append(("close_editor", None)),
    )
    monkeypatch.setattr(
        entrypoint.terminal,
        "new_terminal",
        lambda current_page: calls.append(("new_terminal", None)),
    )
    monkeypatch.setattr(
        entrypoint.terminal,
        "type_in_terminal",
        lambda current_page, text: calls.append(("type_terminal", text)),
    )
    monkeypatch.setattr(
        entrypoint.commands,
        "run_command",
        lambda current_page, command_text: calls.append(("run_command", command_text)),
    )
    monkeypatch.setattr(
        entrypoint.editor,
        "_dismiss_notification",
        lambda current_page: "",
    )

    failed = entrypoint._run_extra_triggers(
        page,
        payload,
        automation_event_recorder=record_event,
    )

    assert failed == []
    assert calls == [
        ("open_file", "samples/report.drawio"),
        ("close_editor", None),
        ("new_terminal", None),
        ("type_terminal", "xdg-open 'vscode://publisher.tool/open'"),
        ("run_command", "Tasks: Run Task"),
        ("run_command", "Welcome: Open Walkthrough"),
        ("close_editor", None),
    ]
    assert page.keyboard.presses == []
    event_kinds = [item[0] for item in events]
    assert event_kinds.count("extra_trigger") == 8
    assert "wait_for_trigger_effect" in event_kinds
    assert "wait_for_ui_settle" in event_kinds


@pytest.mark.parametrize(
    ("payload", "patch_target", "expected_failure"),
    [
        (
            trigger_loader.TriggerPayload(
                extra_custom_editor_files=["samples/broken.drawio"]
            ),
            ("editor", "open_file_by_name"),
            "custom_editor:samples/broken.drawio",
        ),
        (
            trigger_loader.TriggerPayload(uri_trigger="vscode://publisher.tool/open"),
            ("terminal", "new_terminal"),
            "uri_trigger",
        ),
        (
            trigger_loader.TriggerPayload(run_task_trigger=True),
            ("commands", "run_command"),
            "task_trigger",
        ),
        (
            trigger_loader.TriggerPayload(run_walkthrough_trigger=True),
            ("commands", "run_command"),
            "walkthrough_trigger",
        ),
    ],
)
def test_run_extra_triggers_collects_non_command_failures(
    monkeypatch,
    payload: trigger_loader.TriggerPayload,
    patch_target: tuple[str, str],
    expected_failure: str,
) -> None:
    events: list[tuple[str, str, str, str, str]] = []
    page = _FakePage()

    def record_event(
        kind: str,
        message: str,
        status: str,
        scenario_name: str = "",
        activation_event: str = "",
    ) -> None:
        events.append((kind, message, status, scenario_name, activation_event))

    def _raise(*args, **kwargs) -> None:
        _ = (args, kwargs)
        raise entrypoint.PlaywrightError("expected failure")

    module_name, attr_name = patch_target
    monkeypatch.setattr(getattr(entrypoint, module_name), attr_name, _raise)

    failed = entrypoint._run_extra_triggers(
        page,
        payload,
        automation_event_recorder=record_event,
    )

    assert failed == [expected_failure]
    assert any(item[2] == "failed" for item in events)


def test_run_extra_triggers_records_ui_blocker_and_verification_for_commands(
    monkeypatch,
) -> None:
    payload = trigger_loader.TriggerPayload(extra_commands=["Extension: Run Check"])
    recorder_events: list[tuple[str, str, str, str, str]] = []
    monitor = _FakeMonitor(_FakePage(), "/results/report.json", "publisher.tool")
    page = _FakePage()
    run_commands: list[str] = []

    def record_event(
        kind: str,
        message: str,
        status: str,
        scenario_name: str = "",
        activation_event: str = "",
    ) -> None:
        recorder_events.append((kind, message, status, scenario_name, activation_event))

    monkeypatch.setattr(
        entrypoint.commands,
        "run_command",
        lambda current_page, command_text: run_commands.append(command_text),
    )
    monkeypatch.setattr(
        entrypoint.editor,
        "_dismiss_notification",
        lambda current_page: "Install recommended extension?",
    )

    failed = entrypoint._run_extra_triggers(
        page,
        payload,
        automation_event_recorder=record_event,
        verification_monitor=monitor,
    )

    assert failed == []
    assert run_commands == ["Extension: Run Check"]
    assert monitor.snapshot_calls == 2
    assert monitor.verify_calls == [
        {
            "baseline": {"target_activations": 1},
            "capability": "commands",
            "trigger_label": "Extension: Run Check",
            "activation_event": "onCommand",
            "success_signal": True,
        }
    ]
    event_kinds = [item[0] for item in recorder_events]
    assert event_kinds[0] == "command"
    assert "wait_for_command_effect" in event_kinds
    assert "wait_for_target_reaction" in event_kinds
    assert "ui_blocker_detected" in event_kinds
    assert "ui_blocker_dismissed" in event_kinds
    assert event_kinds[-1] == "command"
    assert page.keyboard.presses == []


def test_run_extra_triggers_recovers_from_command_failure(monkeypatch) -> None:
    payload = trigger_loader.TriggerPayload(extra_commands=["Extension: Fail"])
    recorder_events: list[tuple[str, str, str, str, str]] = []
    page = _FakePage()

    def record_event(
        kind: str,
        message: str,
        status: str,
        scenario_name: str = "",
        activation_event: str = "",
    ) -> None:
        recorder_events.append((kind, message, status, scenario_name, activation_event))

    monkeypatch.setattr(
        entrypoint.commands,
        "run_command",
        lambda current_page, command_text: (_ for _ in ()).throw(
            entrypoint.PlaywrightError("command failed")
        ),
    )

    failed = entrypoint._run_extra_triggers(
        page,
        payload,
        automation_event_recorder=record_event,
    )

    assert failed == ["command:Extension: Fail"]
    assert page.keyboard.presses == ["Escape"]
    event_kinds = [item[0] for item in recorder_events]
    assert event_kinds[0] == "command"
    assert "wait_for_ui_settle" in event_kinds
    assert "ui_blocker_unresolved" in event_kinds
    assert event_kinds[-1] == "command"


def test_reload_window_under_monitoring_reuses_primary_page(monkeypatch) -> None:
    page = _FakePage()
    browser = _FakeBrowser([page])
    reload_calls: list[tuple[_FakeBrowser, _FakePage, int, object]] = []

    monkeypatch.setattr(
        entrypoint.vscode,
        "reload_workbench_window",
        lambda current_browser,
        current_page,
        *,
        reconnect_timeout_ms=30_000,
        log=None: (
            reload_calls.append(
                (current_browser, current_page, reconnect_timeout_ms, log)
            )
            or current_page
        ),
    )

    reloaded = entrypoint._reload_window_under_monitoring(browser, page)

    assert reloaded is page
    assert reload_calls == [
        (browser, page, entrypoint.vscode.DEFAULT_RECONNECT_TIMEOUT_MS, print)
    ]


def test_reload_window_under_monitoring_uses_fallback_page(monkeypatch) -> None:
    primary_page = _FakePage("primary")
    fallback_page = _FakePage("fallback")
    browser = _FakeBrowser([fallback_page])
    reload_calls: list[tuple[_FakeBrowser, _FakePage, int, object]] = []

    monkeypatch.setattr(
        entrypoint.vscode,
        "reload_workbench_window",
        lambda current_browser,
        current_page,
        *,
        reconnect_timeout_ms=30_000,
        log=None: (
            reload_calls.append(
                (current_browser, current_page, reconnect_timeout_ms, log)
            )
            or fallback_page
        ),
    )

    reloaded = entrypoint._reload_window_under_monitoring(browser, primary_page)

    assert reloaded is fallback_page
    assert reload_calls == [
        (
            browser,
            primary_page,
            entrypoint.vscode.DEFAULT_RECONNECT_TIMEOUT_MS,
            print,
        )
    ]


def test_reload_window_under_monitoring_raises_when_no_window_is_available(
    monkeypatch,
) -> None:
    page = _FakePage()
    browser = _FakeBrowser([])
    reload_calls: list[tuple[_FakeBrowser, _FakePage, int, object]] = []

    monkeypatch.setattr(
        entrypoint.vscode,
        "reload_workbench_window",
        lambda current_browser,
        current_page,
        *,
        reconnect_timeout_ms=30_000,
        log=None: (
            reload_calls.append(
                (current_browser, current_page, reconnect_timeout_ms, log)
            )
            or (_ for _ in ()).throw(
                entrypoint.vscode.ReloadWindowError(
                    "reconnect",
                    "Could not find a VS Code workbench page via CDP.",
                )
            )
        ),
    )

    with pytest.raises(
        entrypoint.PlaywrightError,
        match="Unable to reconnect to VS Code window after reload: reconnect:",
    ):
        entrypoint._reload_window_under_monitoring(browser, page)
    assert reload_calls == [
        (browser, page, entrypoint.vscode.DEFAULT_RECONNECT_TIMEOUT_MS, print)
    ]


def test_main_list_mode_prints_scenarios_without_connecting(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr(sys, "argv", ["entrypoint.py", "--list"])
    monkeypatch.setattr(entrypoint.automation, "list_scenarios", lambda: ["one", "two"])
    monkeypatch.setattr(
        entrypoint,
        "sync_playwright",
        lambda: (_ for _ in ()).throw(AssertionError("should not connect")),
    )

    entrypoint.main()

    captured = capsys.readouterr()
    assert "Available scenarios:" in captured.out
    assert "one" in captured.out
    assert "two" in captured.out


@pytest.mark.parametrize(
    ("argv", "payload", "expected_call"),
    [
        (["--demo"], None, ("demo", None)),
        (["--scenario", "coding_session"], None, ("selected", ["coding_session"])),
        ([], None, ("all", False)),
        (
            ["--triggers", "/results/triggers.json"],
            trigger_loader.TriggerPayload(selected_scenarios=["coding_session"]),
            ("selected", ["coding_session"]),
        ),
    ],
)
def test_main_dispatches_non_monitored_execution_modes(
    monkeypatch,
    argv: list[str],
    payload: trigger_loader.TriggerPayload | None,
    expected_call: tuple[str, object],
) -> None:
    _FakeMonitor.instances.clear()
    _configure_main_runtime(monkeypatch, argv)
    dispatched: list[tuple[str, object]] = []

    monkeypatch.setattr(
        entrypoint.trigger_loader, "load_trigger_file", lambda path: payload
    )
    monkeypatch.setattr(
        entrypoint, "run_demo", lambda page: dispatched.append(("demo", None))
    )
    monkeypatch.setattr(
        entrypoint.automation,
        "run_scenario",
        lambda page, name: dispatched.append(("single", name)),
    )
    monkeypatch.setattr(
        entrypoint.automation,
        "run_all_scenarios",
        lambda page, shuffle=False: dispatched.append(("all", shuffle)) or [],
    )
    monkeypatch.setattr(
        entrypoint.automation,
        "run_selected_scenarios",
        lambda page, names, shuffle=False: dispatched.append(("selected", names)) or [],
    )
    monkeypatch.setattr(
        entrypoint.automation,
        "list_scenarios",
        lambda: ["coding_session", "debug_session"],
    )

    entrypoint.main()

    assert dispatched == [expected_call]


def test_main_monitor_marks_missing_trigger_plan(monkeypatch) -> None:
    _FakeMonitor.instances.clear()
    monkeypatch.setattr(entrypoint, "uuid4", lambda: SimpleNamespace(hex="fixture"))
    _, _, _, disconnect_calls = _configure_main_runtime(
        monkeypatch,
        ["--monitor", "--triggers", "/results/triggers.json"],
    )

    monkeypatch.setattr(entrypoint.monitor, "ExtensionMonitor", _FakeMonitor)
    monkeypatch.setattr(
        entrypoint.trigger_loader, "load_trigger_file", lambda path: None
    )
    monkeypatch.setattr(
        entrypoint.automation,
        "run_all_scenarios",
        lambda page, shuffle=False: [],
    )
    monkeypatch.setattr(
        entrypoint.automation, "list_scenarios", lambda: ["coding_session"]
    )

    entrypoint.main()

    monitor = _FakeMonitor.instances[0]
    assert monitor.missing_trigger_paths == ["/results/triggers.json"]
    assert any(kind == "trigger_plan_missing" for kind, *_ in monitor.automation_events)
    assert monitor.report.print_summary_calls == 1
    assert monitor.report.saved_paths == ["/results/activation_report_fixture.json"]
    assert disconnect_calls == [disconnect_calls[0]]


def test_main_monitor_can_skip_automation(monkeypatch) -> None:
    _FakeMonitor.instances.clear()
    monkeypatch.setattr(entrypoint, "uuid4", lambda: SimpleNamespace(hex="skip"))
    _configure_main_runtime(monkeypatch, ["--monitor", "--skip-automation"])

    automation_calls: list[str] = []

    monkeypatch.setattr(entrypoint.monitor, "ExtensionMonitor", _FakeMonitor)
    monkeypatch.setattr(
        entrypoint.automation,
        "run_all_scenarios",
        lambda page, shuffle=False: automation_calls.append("all") or [],
    )
    monkeypatch.setattr(
        entrypoint.automation,
        "list_scenarios",
        lambda: ["coding_session"],
    )

    entrypoint.main()

    monitor = _FakeMonitor.instances[0]
    assert monitor.execution_modes == ["skip_automation"]
    assert monitor.report.trigger_execution_mode == "skip_automation"
    assert monitor.report.scenarios_run == []
    assert monitor.report.saved_paths == ["/results/activation_report_skip.json"]
    assert automation_calls == []


def test_main_selected_scenarios_exit_nonzero_when_failures_returned(
    monkeypatch,
) -> None:
    _FakeMonitor.instances.clear()
    _configure_main_runtime(
        monkeypatch,
        ["--monitor", "--triggers", "/results/triggers.json"],
    )
    payload = trigger_loader.TriggerPayload(selected_scenarios=["coding_session"])

    monkeypatch.setattr(entrypoint.monitor, "ExtensionMonitor", _FakeMonitor)
    monkeypatch.setattr(
        entrypoint.trigger_loader,
        "load_trigger_file",
        lambda path: payload,
    )
    monkeypatch.setattr(
        entrypoint.automation,
        "run_selected_scenarios",
        lambda page, names, shuffle=False: ["coding_session"],
    )

    with pytest.raises(SystemExit, match="1"):
        entrypoint.main()

    monitor = _FakeMonitor.instances[0]
    assert monitor.execution_modes == ["selected_scenarios"]
    assert monitor.applied_trigger_plans == [
        (["coding_session"], "/results/triggers.json")
    ]
    assert monitor.failed_scenario_batches == [["coding_session"]]


def test_main_layered_passes_updates_monitor_and_exits_on_extra_trigger_failures(
    monkeypatch,
) -> None:
    _FakeMonitor.instances.clear()
    original_page = _FakePage("before reload")
    reloaded_page = _FakePage("after reload")
    _, _, _, disconnect_calls = _configure_main_runtime(
        monkeypatch,
        ["--monitor", "--reload-before-run", "--triggers", "/results/triggers.json"],
        browser=_FakeBrowser([original_page]),
        page=original_page,
    )
    payload = trigger_loader.TriggerPayload(
        selected_scenarios=["coding_session"],
        stimulus_passes=[
            {
                "pass_id": "workspace_bootstrap",
                "label": "workspace/bootstrap pass",
                "order": 1,
                "status": "planned",
            }
        ],
        event_attempts=[
            {
                "attempt_id": "attempt-1",
                "declared_event": "onCommand:extension.run",
                "activation_event": "onCommand:extension.run",
                "event_family": "onCommand",
            }
        ],
    )

    monkeypatch.setattr(entrypoint.monitor, "ExtensionMonitor", _FakeMonitor)
    monkeypatch.setattr(
        entrypoint.trigger_loader,
        "load_trigger_file",
        lambda path: payload,
    )
    monkeypatch.setattr(
        entrypoint,
        "_reload_window_under_monitoring",
        lambda browser, page: reloaded_page,
    )
    monkeypatch.setattr(
        entrypoint.stimulus,
        "run_stimulus_plan",
        lambda page, payload, monitor=None: SimpleNamespace(
            executed_scenarios=["coding_session"],
            failed_scenarios=[],
            extra_trigger_failures=["command:Extension: Fail"],
        ),
    )

    with pytest.raises(SystemExit, match="1"):
        entrypoint.main()

    monitor = _FakeMonitor.instances[0]
    assert monitor.execution_modes == ["layered_passes"]
    assert monitor.page is reloaded_page
    assert monitor.attach_runtime_tracers_calls == 1
    assert monitor.applied_payloads == [payload]
    assert monitor.applied_trigger_plans == [
        (["coding_session"], "/results/triggers.json")
    ]
    assert monitor.report.scenarios_run == ["coding_session"]
    assert monitor.report.extra_trigger_failures == ["command:Extension: Fail"]
    assert disconnect_calls == [disconnect_calls[0]]


def test_main_resets_reporter_and_disconnects_when_execution_raises(
    monkeypatch,
) -> None:
    _FakeMonitor.instances.clear()
    browser, _, _, disconnect_calls = _configure_main_runtime(
        monkeypatch,
        ["--monitor", "--scenario", "coding_session"],
    )
    reporter_calls: list[object] = []

    monkeypatch.setattr(entrypoint.monitor, "ExtensionMonitor", _FakeMonitor)
    monkeypatch.setattr(
        entrypoint.automation,
        "run_selected_scenarios",
        lambda page, names, shuffle=False: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(
        entrypoint.automation,
        "set_scenario_event_reporter",
        lambda reporter: reporter_calls.append(reporter),
    )

    with pytest.raises(RuntimeError, match="boom"):
        entrypoint.main()

    assert reporter_calls[0] is not None
    assert reporter_calls[-1] is None
    assert disconnect_calls == [browser]
