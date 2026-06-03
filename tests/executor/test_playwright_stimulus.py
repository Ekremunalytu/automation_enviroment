from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from executor.flows.playwright import stimulus
from executor.flows.playwright.stimulus import attempts as stimulus_attempts
from executor.flows.playwright.stimulus import maintenance as stimulus_maintenance
from packages.analysis_contracts import TriggerPayload


class _FakeMonitor:
    def __init__(self) -> None:
        self.results: list[dict[str, object]] = []
        self.pass_events: list[dict[str, object]] = []
        self.attempt_starts: list[dict[str, object]] = []
        self.attempt_ends: list[dict[str, object]] = []
        self.scenario_events: list[dict[str, object]] = []
        self.automation_events: list[dict[str, object]] = []

    def record_prerequisite_result(
        self,
        prerequisite_id: str,
        *,
        status: str,
        detail: str = "",
        reason_code: str = "",
        resolved_targets: dict[str, object] | None = None,
    ) -> None:
        self.results.append(
            {
                "prerequisite_id": prerequisite_id,
                "status": status,
                "detail": detail,
                "reason_code": reason_code,
                "resolved_targets": resolved_targets or {},
            }
        )

    def record_stimulus_pass_event(
        self,
        action: str,
        pass_id: str,
        *,
        label: str = "",
        order: int = 0,
        trigger_method: str = "",
        status: str = "",
    ) -> None:
        self.pass_events.append(
            {
                "action": action,
                "pass_id": pass_id,
                "label": label,
                "order": order,
                "trigger_method": trigger_method,
                "status": status,
            }
        )

    def record_event_attempt_start(
        self,
        attempt_id: str,
        *,
        pass_name: str = "",
    ) -> None:
        self.attempt_starts.append(
            {
                "attempt_id": attempt_id,
                "pass_name": pass_name,
            }
        )

    def record_event_attempt_end(
        self,
        attempt_id: str,
        *,
        status: str,
        pass_name: str = "",
        trigger_method_used: str = "",
        result_details: str = "",
        blocked_reason_code: str = "",
        failure_reason_code: str = "",
    ) -> None:
        self.attempt_ends.append(
            {
                "attempt_id": attempt_id,
                "status": status,
                "pass_name": pass_name,
                "trigger_method_used": trigger_method_used,
                "result_details": result_details,
                "blocked_reason_code": blocked_reason_code,
                "failure_reason_code": failure_reason_code,
            }
        )

    def record_scenario_event(
        self,
        action: str,
        name: str,
        status: str = "",
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.scenario_events.append(
            {
                "action": action,
                "name": name,
                "status": status,
                "metadata": metadata or {},
            }
        )

    def record_automation_event(
        self,
        kind: str,
        message: str,
        status: str = "",
        scenario_name: str = "",
        activation_event: str = "",
    ) -> None:
        self.automation_events.append(
            {
                "kind": kind,
                "message": message,
                "status": status,
                "scenario_name": scenario_name,
                "activation_event": activation_event,
            }
        )


def _payload(**overrides: object) -> SimpleNamespace:
    baseline = {
        "command_targets": {},
        "extra_commands": [],
        "auth_provider_ids": [],
        "webview_view_ids": [],
        "view_targets": {},
        "uri_trigger": None,
        "run_walkthrough_trigger": False,
        "extra_custom_editor_files": [],
        "extra_notebook_files": [],
        "event_attempts": [],
        "stimulus_passes": [],
        "prerequisite_results": [],
    }
    baseline.update(overrides)
    return SimpleNamespace(**baseline)


class _LivePage:
    """Minimal live Playwright-page stand-in for ``is_fatal_ui_error``.

    Reports a healthy renderer (not closed, liveness probe succeeds) so a
    NON-fatal exception raised inside ``run_stimulus_plan`` is classified
    as ``stimulus_execution_failed`` rather than ``fatal_ui_crash``.
    """

    def __init__(self) -> None:
        self.context = SimpleNamespace(is_closed=lambda: False)

    def is_closed(self) -> bool:
        return False

    def wait_for_function(self, _expression: str, *, timeout: int = 0) -> None:
        return None


def test_workspace_contains_fixture_creates_requested_patterns(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(stimulus.workspace, "WORKSPACE_DIR", tmp_path)
    monitor = _FakeMonitor()
    prerequisite = {
        "prerequisite_id": "prep-workspace-contains",
        "key": "workspace_contains_fixture",
        "attempt_ids": ["a", "b"],
    }
    attempts_by_id = {
        "a": {
            "attempt_id": "a",
            "event_value": "app.py",
            "activation_event": "workspaceContains:app.py",
        },
        "b": {
            "attempt_id": "b",
            "event_value": "**/pylock.*.toml",
            "activation_event": "workspaceContains:**/pylock.*.toml",
        },
    }

    result = stimulus._materialize_prerequisite(
        prerequisite,
        payload=_payload(),
        attempts_by_id=attempts_by_id,
        monitor=monitor,
    )

    assert result.status == "completed"
    assert (tmp_path / "app.py").exists()
    assert (tmp_path / "nested" / "pylock.dev.toml").exists()
    assert monitor.results[0]["status"] == "completed"


def test_workspace_contains_fixture_rejects_parent_traversal(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(stimulus.workspace, "WORKSPACE_DIR", tmp_path)
    monitor = _FakeMonitor()
    prerequisite = {
        "prerequisite_id": "prep-workspace-contains",
        "key": "workspace_contains_fixture",
        "attempt_ids": ["a"],
    }
    attempts_by_id = {
        "a": {
            "attempt_id": "a",
            "event_value": "../../tmp/extrace_escape.txt",
            "activation_event": "workspaceContains:../../tmp/extrace_escape.txt",
        }
    }

    result = stimulus._materialize_prerequisite(
        prerequisite,
        payload=_payload(),
        attempts_by_id=attempts_by_id,
        monitor=monitor,
    )

    assert result.status == "blocked"
    assert result.reason_code == "prerequisite_blocked"
    escape_target = (tmp_path / ".." / ".." / "tmp" / "extrace_escape.txt").resolve()
    assert not escape_target.exists()
    assert monitor.results[0]["status"] == "blocked"


def test_workspace_helper_rejects_absolute_and_traversal_paths(
    monkeypatch,
    tmp_path: Path,
) -> None:
    import pytest

    from executor.flows.playwright import workspace as workspace_module

    monkeypatch.setattr(workspace_module, "WORKSPACE_DIR", tmp_path)

    with pytest.raises(ValueError, match="must be relative"):
        workspace_module.create_workspace_file("/etc/passwd_overwrite", "")
    with pytest.raises(ValueError, match="escapes WORKSPACE_DIR"):
        workspace_module.create_workspace_file("../../tmp/extrace_escape.txt", "")
    with pytest.raises(ValueError, match="escapes WORKSPACE_DIR"):
        workspace_module.create_workspace_dir("../sibling")

    # Containment-safe relative path still works.
    safe = workspace_module.create_workspace_file("nested/ok.txt", "ok")
    assert safe.exists()
    assert safe.read_text() == "ok"


def test_workspace_contains_fixture_falls_back_to_deterministic_placeholder(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(stimulus.workspace, "WORKSPACE_DIR", tmp_path)
    monitor = _FakeMonitor()
    prerequisite = {
        "prerequisite_id": "prep-workspace-contains",
        "key": "workspace_contains_fixture",
        "attempt_ids": ["a"],
    }
    attempts_by_id = {
        "a": {
            "attempt_id": "a",
            "event_value": "**/.gitignore",
            "activation_event": "workspaceContains:**/.gitignore",
        }
    }

    result = stimulus._materialize_prerequisite(
        prerequisite,
        payload=_payload(),
        attempts_by_id=attempts_by_id,
        monitor=monitor,
    )

    assert result.status == "completed"
    assert (tmp_path / "nested" / ".gitignore").exists()
    assert monitor.results[0]["status"] == "completed"


def test_command_target_without_metadata_is_blocked() -> None:
    monitor = _FakeMonitor()
    prerequisite = {
        "prerequisite_id": "prep-command",
        "key": "command_target",
        "attempt_ids": ["a"],
    }
    attempts_by_id = {
        "a": {
            "attempt_id": "a",
            "event_family": "onCommand",
            "activation_event": "onCommand",
            "event_value": "",
        }
    }

    result = stimulus._materialize_prerequisite(
        prerequisite,
        payload=_payload(),
        attempts_by_id=attempts_by_id,
        monitor=monitor,
    )

    assert result.status == "blocked"
    assert result.reason_code == "prerequisite_blocked"
    assert monitor.results[0]["status"] == "blocked"


def test_passive_observation_families_are_not_unsupported() -> None:
    """W22: ``onStartupFinished``/``*`` are ambient activation surfaces.

    They fire automatically once the workbench is ready, so the executor
    cannot actively drive them. Rather than short-circuit the attempt to
    ``blocked`` / ``unsupported_activation_surface`` (which makes
    ``reconcile_event_attempts`` skip it), they are treated as passive
    observation families: the benign ``fixture:startup_observe`` attempt runs
    and reconciliation later upgrades it to ``verified`` via the captured
    activation log. A genuinely un-drivable family still reports unsupported.
    """
    from executor.flows.playwright.stimulus import passes as passes_module

    assert (
        passes_module._unsupported_surface_reason({"event_family": "onStartupFinished"})
        is None
    )
    assert passes_module._unsupported_surface_reason({"event_family": "*"}) is None

    reason = passes_module._unsupported_surface_reason(
        {"event_family": "onSomethingExecutorCannotDrive"}
    )
    assert reason is not None
    assert reason[0] == "unsupported_activation_surface"


def test_unknown_language_fixture_is_blocked() -> None:
    result = stimulus._materialize_prerequisite(
        {
            "prerequisite_id": "prep-language",
            "key": "language_fixture",
            "attempt_ids": ["a"],
        },
        payload=_payload(),
        attempts_by_id={
            "a": {
                "attempt_id": "a",
                "event_family": "onLanguage",
                "activation_event": "onLanguage:unknownlang",
                "event_value": "unknownlang",
            }
        },
        monitor=None,
    )

    assert result.status == "blocked"
    assert result.reason_code == "materialization_failed"


def test_supported_generic_language_fixture_creates_sample_file(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(stimulus.workspace, "WORKSPACE_DIR", tmp_path)
    monitor = _FakeMonitor()

    result = stimulus._materialize_prerequisite(
        {
            "prerequisite_id": "prep-language",
            "key": "language_fixture",
            "attempt_ids": ["a"],
        },
        payload=_payload(),
        attempts_by_id={
            "a": {
                "attempt_id": "a",
                "event_family": "onLanguage",
                "activation_event": "onLanguage:json",
                "event_value": "json",
            }
        },
        monitor=monitor,
    )

    assert result.status == "completed"
    assert (tmp_path / "sample.json").exists()
    assert monitor.results[0]["status"] == "completed"


def test_run_stimulus_plan_dedupes_repeat_scenarios_within_pass(
    monkeypatch,
) -> None:
    executed: list[str] = []

    def fake_run_scenario(_page, name: str) -> None:
        executed.append(name)

    monkeypatch.setattr(stimulus.automation, "run_scenario", fake_run_scenario)

    payload = _payload(
        event_attempts=[
            {
                "attempt_id": "a1",
                "activation_event": "workspaceContains:app.py",
                "event_value": "app.py",
                "executor_action": "scenario:project_exploration",
                "trigger_method": "ui_simulation",
            },
            {
                "attempt_id": "a2",
                "activation_event": "workspaceContains:requirements.txt",
                "event_value": "requirements.txt",
                "executor_action": "scenario:project_exploration",
                "trigger_method": "ui_simulation",
            },
        ],
        stimulus_passes=[
            {
                "pass_id": "workspace_bootstrap",
                "label": "workspace/bootstrap pass",
                "order": 1,
                "attempt_ids": ["a1", "a2"],
                "prerequisite_keys": [],
            }
        ],
    )
    monitor = _FakeMonitor()

    result = stimulus.run_stimulus_plan(object(), payload, monitor=monitor)

    assert executed == ["project_exploration"]
    assert result.executed_scenarios == ["project_exploration"]
    assert [item["status"] for item in monitor.attempt_ends] == [
        "attempted_only",
        "attempted_only",
    ]
    assert [(item["action"], item["name"]) for item in monitor.scenario_events] == [
        ("start", "project_exploration"),
        ("end", "project_exploration"),
    ]
    assert (
        "Reused prior scenario:project_exploration result"
        in monitor.attempt_ends[1]["result_details"]
    )


def test_run_stimulus_plan_keeps_distinct_language_coding_sessions(
    monkeypatch,
) -> None:
    executed: list[str] = []

    def fake_coding_session(_page, *, language: str) -> None:
        executed.append(language)

    monkeypatch.setattr(
        stimulus.automation,
        "scenario_coding_session",
        fake_coding_session,
    )

    payload = _payload(
        event_attempts=[
            {
                "attempt_id": "py",
                "activation_event": "onLanguage:python",
                "event_family": "onLanguage",
                "event_value": "python",
                "executor_action": "scenario:coding_session",
                "trigger_method": "ui_simulation",
            },
            {
                "attempt_id": "ts",
                "activation_event": "onLanguage:typescript",
                "event_family": "onLanguage",
                "event_value": "typescript",
                "executor_action": "scenario:coding_session",
                "trigger_method": "ui_simulation",
            },
        ],
        stimulus_passes=[
            {
                "pass_id": "ui_first_user_session",
                "label": "UI-first user session pass",
                "order": 2,
                "attempt_ids": ["py", "ts"],
                "prerequisite_keys": [],
            }
        ],
    )

    result = stimulus.run_stimulus_plan(object(), payload, monitor=None)

    assert executed == ["python", "typescript"]
    assert result.executed_scenarios == ["coding_session", "coding_session"]


def test_run_stimulus_plan_accepts_contract_payload_nested_models(
    monkeypatch,
    tmp_path: Path,
) -> None:
    executed: list[str] = []

    def fake_run_scenario(_page, name: str) -> None:
        executed.append(name)

    monkeypatch.setattr(stimulus.automation, "run_scenario", fake_run_scenario)
    monkeypatch.setattr(stimulus.workspace, "WORKSPACE_DIR", tmp_path)

    payload = TriggerPayload(
        event_attempts=[
            {
                "attempt_id": "a1",
                "declared_event": "workspaceContains:app.py",
                "activation_event": "workspaceContains:app.py",
                "event_family": "workspaceContains",
                "event_value": "app.py",
                "executor_action": "scenario:project_exploration",
                "trigger_method": "ui_simulation",
            }
        ],
        stimulus_passes=[
            {
                "pass_id": "workspace_bootstrap",
                "label": "workspace/bootstrap pass",
                "order": 1,
                "attempt_ids": ["a1"],
                "prerequisite_keys": ["workspace_contains_fixture"],
            }
        ],
        prerequisite_results=[
            {
                "prerequisite_id": "prep-workspace",
                "key": "workspace_contains_fixture",
                "label": "workspace fixture",
                "attempt_ids": ["a1"],
            }
        ],
    )
    monitor = _FakeMonitor()

    result = stimulus.run_stimulus_plan(object(), payload, monitor=monitor)

    assert executed == ["project_exploration"]
    assert result.executed_scenarios == ["project_exploration"]
    assert (tmp_path / "app.py").exists()
    assert monitor.results[0]["status"] == "completed"
    assert [item["status"] for item in monitor.attempt_ends] == ["attempted_only"]
    assert [
        item["status"] for item in monitor.pass_events if item["action"] == "end"
    ] == ["completed"]


def test_run_stimulus_plan_records_language_coding_session_lifecycle(
    monkeypatch,
) -> None:
    executed: list[str] = []

    def fake_coding_session(_page, *, language: str) -> None:
        executed.append(language)

    monkeypatch.setattr(
        stimulus.automation,
        "scenario_coding_session",
        fake_coding_session,
    )

    payload = _payload(
        event_attempts=[
            {
                "attempt_id": "py",
                "activation_event": "onLanguage:python",
                "event_family": "onLanguage",
                "event_value": "python",
                "executor_action": "scenario:coding_session",
                "trigger_method": "ui_simulation",
            }
        ],
        stimulus_passes=[
            {
                "pass_id": "ui_first_user_session",
                "label": "UI-first user session pass",
                "order": 2,
                "attempt_ids": ["py"],
                "prerequisite_keys": [],
            }
        ],
    )
    monitor = _FakeMonitor()

    result = stimulus.run_stimulus_plan(object(), payload, monitor=monitor)

    assert executed == ["python"]
    assert result.executed_scenarios == ["coding_session"]
    assert result.failed_scenarios == []
    assert [
        (item["action"], item["name"], item["status"])
        for item in monitor.scenario_events
    ] == [
        ("start", "coding_session", ""),
        ("end", "coding_session", "completed"),
    ]


def test_run_stimulus_plan_records_failed_layered_scenarios(
    monkeypatch,
) -> None:
    def fail_run_scenario(_page, _name: str) -> None:
        raise RuntimeError("scenario failed")

    monkeypatch.setattr(stimulus.automation, "run_scenario", fail_run_scenario)

    payload = _payload(
        event_attempts=[
            {
                "attempt_id": "a1",
                "activation_event": "workspaceContains:app.py",
                "event_value": "app.py",
                "executor_action": "scenario:project_exploration",
                "trigger_method": "ui_simulation",
            }
        ],
        stimulus_passes=[
            {
                "pass_id": "workspace_bootstrap",
                "label": "workspace/bootstrap pass",
                "order": 1,
                "attempt_ids": ["a1"],
                "prerequisite_keys": [],
            }
        ],
    )
    monitor = _FakeMonitor()

    result = stimulus.run_stimulus_plan(_LivePage(), payload, monitor=monitor)

    assert result.executed_scenarios == ["project_exploration"]
    assert result.failed_scenarios == ["project_exploration"]
    assert [item["status"] for item in monitor.attempt_ends] == ["failed"]
    assert monitor.attempt_ends[0]["failure_reason_code"] == "stimulus_execution_failed"
    assert [
        (item["action"], item["name"], item["status"])
        for item in monitor.scenario_events
    ] == [
        ("start", "project_exploration", ""),
        ("end", "project_exploration", "failed"),
    ]
    assert [
        item["status"] for item in monitor.pass_events if item["action"] == "end"
    ] == ["failed"]


def test_run_stimulus_plan_fatal_ui_crash_fails_fast(monkeypatch) -> None:
    """A renderer crash in the extra-trigger / backfill path must:

    * classify the crashing attempt as ``fatal_ui_crash`` (not the generic
      ``stimulus_execution_failed``) so health rolls up ``inconclusive``;
    * fail-fast — stop driving the dead window, so the remaining triggers
      are NEVER attempted (no ``Target crashed`` keyboard cascade);
    * record those remaining triggers as ``blocked`` /
      ``aborted_after_fatal_ui_crash`` instead of letting them masquerade
      as normal failed extra triggers.
    """
    from playwright.sync_api import Error as PlaywrightError

    from executor.flows.playwright.stimulus import passes as passes_module

    attempted: list[str] = []

    def fake_execute_attempt(_page, _payload, attempt, **_kwargs) -> None:
        attempted.append(attempt["attempt_id"])
        if attempt["attempt_id"] == "a1":
            raise PlaywrightError("Keyboard.press: Target crashed")

    monkeypatch.setattr(passes_module, "execute_attempt", fake_execute_attempt)

    payload = _payload(
        event_attempts=[
            {
                "attempt_id": "a1",
                "activation_event": "onCommand:python.copilotSetupTests",
                "event_family": "onCommand",
                "executor_action": "harness:run_current_stimulus",
                "trigger_method": "harness",
            },
            {
                "attempt_id": "a2",
                "activation_event": "onDebugResolve:python",
                "event_family": "onDebugResolve",
                "executor_action": "harness:run_current_stimulus",
                "trigger_method": "harness",
            },
            {
                "attempt_id": "a3",
                "activation_event": "onTerminalShellIntegration:python",
                "event_family": "onTerminalShellIntegration",
                "executor_action": "harness:run_current_stimulus",
                "trigger_method": "harness",
            },
        ],
        stimulus_passes=[
            {
                "pass_id": "unresolved_event_backfill",
                "label": "unresolved event backfill",
                "order": 4,
                "attempt_ids": ["a1", "a2", "a3"],
                "prerequisite_keys": [],
            }
        ],
    )
    monitor = _FakeMonitor()

    result = stimulus.run_stimulus_plan(_LivePage(), payload, monitor=monitor)

    # Fail-fast: only the crashing attempt was driven; a2/a3 never touched.
    assert attempted == ["a1"]

    ends = {item["attempt_id"]: item for item in monitor.attempt_ends}
    assert ends["a1"]["status"] == "failed"
    assert ends["a1"]["failure_reason_code"] == "fatal_ui_crash"
    assert ends["a2"]["status"] == "blocked"
    assert ends["a2"]["blocked_reason_code"] == "aborted_after_fatal_ui_crash"
    assert ends["a3"]["status"] == "blocked"
    assert ends["a3"]["blocked_reason_code"] == "aborted_after_fatal_ui_crash"

    # Only the crashing attempt is a real extra-trigger failure; aborted
    # triggers must NOT be appended as normal failed extra triggers.
    assert result.extra_trigger_failures == ["a1:harness:run_current_stimulus"]

    # A distinct fatal_ui_crash automation event is emitted for the report
    # log so an operator can see why the run was aborted.
    assert any(event["kind"] == "fatal_ui_crash" for event in monitor.automation_events)


def test_run_stimulus_plan_aborts_when_renderer_dies_between_command_attempts(
    monkeypatch,
) -> None:
    """W22 Fix 4b: a command attempt can SUCCEED yet leave the renderer dead
    from cumulative load (the field black-screen after running many synthesized
    contributes-commands). ``post_command_maintenance`` detects that death
    *between* attempts via the post-attempt liveness probe and must route into
    the same graceful abort as an in-attempt crash — so the next synthesized
    command is never driven into a black window.

    Distinct from ``…fatal_ui_crash_fails_fast`` (which crashes *during* an
    attempt): here every ``execute_attempt`` returns cleanly and the death is
    seen only by the inter-command health gate.
    """
    from executor.flows.playwright.stimulus import passes as passes_module

    attempted: list[str] = []
    probed: list[str] = []

    def fake_execute_attempt(_page, _payload, attempt, **_kwargs) -> None:
        attempted.append(attempt["attempt_id"])  # all succeed; none crash

    def fake_post_command_maintenance(_page, attempt, _action, *, monitor=None) -> bool:
        probed.append(attempt["attempt_id"])
        return attempt["attempt_id"] == "a1"  # renderer dead right after a1

    monkeypatch.setattr(passes_module, "execute_attempt", fake_execute_attempt)
    monkeypatch.setattr(
        passes_module, "post_command_maintenance", fake_post_command_maintenance
    )

    payload = _payload(
        event_attempts=[
            {
                "attempt_id": "a1",
                "activation_event": "onCommand:python.createTerminal",
                "event_family": "onCommand",
                "executor_action": "command:auto",
                "trigger_method": "ui_simulation",
            },
            {
                "attempt_id": "a2",
                "activation_event": "onCommand:python.startREPL",
                "event_family": "onCommand",
                "executor_action": "command:auto",
                "trigger_method": "ui_simulation",
            },
            {
                "attempt_id": "a3",
                "activation_event": "onCommand:python.viewOutput",
                "event_family": "onCommand",
                "executor_action": "command:auto",
                "trigger_method": "ui_simulation",
            },
        ],
        stimulus_passes=[
            {
                "pass_id": "ui_first_user_session",
                "label": "ui-first user session",
                "order": 2,
                "attempt_ids": ["a1", "a2", "a3"],
                "prerequisite_keys": [],
            }
        ],
    )
    monitor = _FakeMonitor()

    stimulus.run_stimulus_plan(_LivePage(), payload, monitor=monitor)

    # a1 ran and was probed (probe reported the renderer dead); the fail-fast
    # means a2/a3 were never driven into the dead window.
    assert attempted == ["a1"]
    assert probed == ["a1"]

    ends = {item["attempt_id"]: item for item in monitor.attempt_ends}
    # a1 itself completed — recorded ``attempted_only``, NOT blocked: it did not
    # crash; the death happened *after* it, between attempts.
    assert ends["a1"]["status"] == "attempted_only"
    assert ends["a1"]["blocked_reason_code"] == ""
    # a2/a3 are aborted via the same graceful path as an in-attempt crash.
    assert ends["a2"]["status"] == "blocked"
    assert ends["a2"]["blocked_reason_code"] == "aborted_after_fatal_ui_crash"
    assert ends["a3"]["status"] == "blocked"
    assert ends["a3"]["blocked_reason_code"] == "aborted_after_fatal_ui_crash"

    # The between-attempts death emits its own fatal_ui_crash event (distinct
    # wording from the in-attempt crash) so an operator can tell the two death
    # modes apart in the report log.
    crashes = [e for e in monitor.automation_events if e["kind"] == "fatal_ui_crash"]
    assert len(crashes) == 1
    assert "between" in crashes[0]["message"].lower()


def test_run_stimulus_plan_uses_lightweight_debug_action(
    monkeypatch,
) -> None:
    debug_events: list[str] = []
    command_calls: list[str] = []

    monkeypatch.setattr(
        stimulus.editor,
        "open_file_by_name",
        lambda _page, filename: debug_events.append(f"open:{filename}"),
    )
    monkeypatch.setattr(
        stimulus.editor,
        "_dismiss_notification",
        lambda _page: debug_events.append("dismiss"),
    )
    monkeypatch.setattr(
        stimulus.debug,
        "start_debug",
        lambda _page: debug_events.append("start"),
    )
    monkeypatch.setattr(
        stimulus.debug,
        "stop_debug",
        lambda _page: debug_events.append("stop"),
    )
    monkeypatch.setattr(
        stimulus.commands,
        "run_command",
        lambda _page, *_args, **_kwargs: command_calls.append("run_command"),
    )

    class _Page:
        def __init__(self) -> None:
            self.keyboard = SimpleNamespace(
                press=lambda key: debug_events.append(f"press:{key}")
            )

        def wait_for_timeout(self, ms: int) -> None:
            debug_events.append(f"wait:{ms}")

    payload = _payload(
        event_attempts=[
            {
                "attempt_id": "d1",
                "activation_event": "onDebugInitialConfigurations",
                "event_family": "onDebugInitialConfigurations",
                "executor_action": "extra:debug_lifecycle",
                "trigger_method": "mixed",
            },
            {
                "attempt_id": "d2",
                "activation_event": "onDebugResolve:python",
                "event_family": "onDebugResolve",
                "executor_action": "extra:debug_lifecycle",
                "trigger_method": "mixed",
            },
        ],
        stimulus_passes=[
            {
                "pass_id": "target_specific_activation",
                "label": "target-specific activation pass",
                "order": 3,
                "attempt_ids": ["d1", "d2"],
                "prerequisite_keys": [],
            }
        ],
    )
    monitor = _FakeMonitor()

    result = stimulus.run_stimulus_plan(_Page(), payload, monitor=monitor)

    assert command_calls == []
    assert result.executed_scenarios == []
    assert debug_events.count("start") == 1
    assert debug_events.count("stop") == 1
    assert [item["status"] for item in monitor.attempt_ends] == [
        "attempted_only",
        "attempted_only",
    ]
    assert (
        "Reused prior extra:debug_lifecycle result"
        in monitor.attempt_ends[1]["result_details"]
    )


def test_run_stimulus_plan_waits_for_trigger_effect_for_custom_editor(
    monkeypatch,
) -> None:
    calls: list[tuple[str, str | None]] = []
    waits: list[str] = []

    monkeypatch.setattr(
        stimulus.editor,
        "open_file_by_name",
        lambda _page, filename: calls.append(("open", filename)),
    )
    monkeypatch.setattr(
        stimulus.editor,
        "close_active_editor",
        lambda _page: calls.append(("close", None)),
    )
    monkeypatch.setattr(
        stimulus_attempts,
        "wait_for_trigger_effect",
        lambda *_args, **_kwargs: "trigger_effect",
    )
    monkeypatch.setattr(
        stimulus_attempts,
        "wait_for_ui_settle",
        lambda *_args, **_kwargs: "ui_settle",
    )
    monkeypatch.setattr(
        stimulus_attempts,
        "wait_for_editor_ready",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("custom editor attempts should not wait for Monaco")
        ),
    )
    monkeypatch.setattr(
        stimulus_attempts,
        "require_wait",
        lambda result: waits.append(str(result)),
    )

    payload = _payload(
        extra_custom_editor_files=["samples/report.drawio"],
        event_attempts=[
            {
                "attempt_id": "custom-editor",
                "activation_event": "onCustomEditor:drawio",
                "event_family": "onCustomEditor",
                "executor_action": "extra:custom_editor",
                "trigger_method": "mixed",
            }
        ],
        stimulus_passes=[
            {
                "pass_id": "target_specific_activation",
                "label": "target-specific activation pass",
                "order": 3,
                "attempt_ids": ["custom-editor"],
                "prerequisite_keys": [],
            }
        ],
    )

    result = stimulus.run_stimulus_plan(SimpleNamespace(), payload, monitor=None)

    assert result.executed_scenarios == []
    assert calls == [("open", "samples/report.drawio"), ("close", None)]
    assert waits == ["trigger_effect", "ui_settle"]


def _valid_marker_payload(**overrides: object) -> str:
    import json as _json

    payload: dict[str, object] = {
        "ready_at_unix": 1700000000.0,
        "command": "extrace.harness.runCurrentStimulus",
        "marker_version": 1,
        "epoch_run_id": "",
        "pid": 4321,
    }
    payload.update(overrides)
    return _json.dumps(payload)


def test_ensure_harness_ready_returns_when_marker_valid(tmp_path: Path) -> None:
    marker = tmp_path / "ready.json"
    marker.write_text(_valid_marker_payload(), encoding="utf-8")
    stimulus_attempts._ensure_harness_ready(
        timeout_s=0.5, poll_interval_s=0.05, ready_path=marker
    )


def test_ensure_harness_ready_raises_missing_when_marker_absent(tmp_path: Path) -> None:
    import pytest

    from executor.flows.playwright.stimulus.types import (
        HARNESS_READY_MARKER_MISSING_REASON,
        HarnessUnavailableError,
    )

    marker = tmp_path / "ready.json"
    with pytest.raises(HarnessUnavailableError) as exc_info:
        stimulus_attempts._ensure_harness_ready(
            timeout_s=0.1, poll_interval_s=0.05, ready_path=marker
        )
    assert exc_info.value.reason_code == HARNESS_READY_MARKER_MISSING_REASON


def test_ensure_harness_ready_raises_invalid_when_marker_unparseable(
    tmp_path: Path,
) -> None:
    import pytest

    from executor.flows.playwright.stimulus.types import (
        HARNESS_READY_MARKER_INVALID_REASON,
        HarnessUnavailableError,
    )

    marker = tmp_path / "ready.json"
    marker.write_text("{not-json", encoding="utf-8")
    with pytest.raises(HarnessUnavailableError) as exc_info:
        stimulus_attempts._ensure_harness_ready(
            timeout_s=0.5, poll_interval_s=0.05, ready_path=marker
        )
    assert exc_info.value.reason_code == HARNESS_READY_MARKER_INVALID_REASON


def test_ensure_harness_ready_raises_invalid_when_required_field_missing(
    tmp_path: Path,
) -> None:
    import json as _json

    import pytest

    from executor.flows.playwright.stimulus.types import (
        HARNESS_READY_MARKER_INVALID_REASON,
        HarnessUnavailableError,
    )

    marker = tmp_path / "ready.json"
    # Drop the required `pid` field — payload becomes invalid.
    marker.write_text(
        _json.dumps(
            {
                "ready_at_unix": 1700000000.0,
                "command": "extrace.harness.runCurrentStimulus",
                "marker_version": 1,
                "epoch_run_id": "",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(HarnessUnavailableError) as exc_info:
        stimulus_attempts._ensure_harness_ready(
            timeout_s=0.5, poll_interval_s=0.05, ready_path=marker
        )
    assert exc_info.value.reason_code == HARNESS_READY_MARKER_INVALID_REASON


def test_ensure_harness_ready_raises_stale_when_epoch_mismatches(
    tmp_path: Path,
) -> None:
    import pytest

    from executor.flows.playwright.stimulus.types import (
        HARNESS_READY_MARKER_STALE_REASON,
        HarnessUnavailableError,
    )

    marker = tmp_path / "ready.json"
    marker.write_text(
        _valid_marker_payload(epoch_run_id="previous-container"), encoding="utf-8"
    )
    with pytest.raises(HarnessUnavailableError) as exc_info:
        stimulus_attempts._ensure_harness_ready(
            timeout_s=0.5,
            poll_interval_s=0.05,
            ready_path=marker,
            expected_epoch_run_id="current-container",
        )
    assert exc_info.value.reason_code == HARNESS_READY_MARKER_STALE_REASON


def test_ensure_harness_ready_skips_stale_check_when_expected_empty(
    tmp_path: Path,
) -> None:
    """Backwards-compat: empty expected epoch disables stale verification."""
    marker = tmp_path / "ready.json"
    marker.write_text(
        _valid_marker_payload(epoch_run_id="any-container"), encoding="utf-8"
    )
    stimulus_attempts._ensure_harness_ready(
        timeout_s=0.5,
        poll_interval_s=0.05,
        ready_path=marker,
        expected_epoch_run_id="",
    )


def test_parse_harness_ready_marker_round_trip(tmp_path: Path) -> None:
    marker = tmp_path / "ready.json"
    marker.write_text(
        _valid_marker_payload(
            epoch_run_id="boot-abc", pid=9999, ready_at_unix=1700000005.5
        ),
        encoding="utf-8",
    )
    parsed = stimulus_attempts.parse_harness_ready_marker(marker)
    assert parsed is not None
    assert parsed.epoch_run_id == "boot-abc"
    assert parsed.pid == 9999
    assert parsed.marker_version == 1
    assert parsed.ready_at_unix == 1700000005.5


def test_parse_harness_ready_marker_returns_none_on_garbage(tmp_path: Path) -> None:
    marker = tmp_path / "ready.json"
    marker.write_text("not json at all", encoding="utf-8")
    assert stimulus_attempts.parse_harness_ready_marker(marker) is None


def test_parse_harness_ready_marker_returns_none_on_missing_file(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "absent.json"
    assert stimulus_attempts.parse_harness_ready_marker(marker) is None


def test_ensure_harness_ready_with_recovery_succeeds_on_second_poll(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """First poll sees nothing; recovery sleep writes the marker; second poll succeeds."""
    marker = tmp_path / "ready.json"

    call_state = {"count": 0}
    real_sleep = stimulus_attempts.time.sleep

    def staging_sleep(_seconds: float) -> None:
        call_state["count"] += 1
        # On the recovery_sleep between attempts, materialise the marker
        # so the second `_ensure_harness_ready` call observes a valid file.
        if call_state["count"] == 1:
            marker.write_text(_valid_marker_payload(), encoding="utf-8")

    monkeypatch.setattr(stimulus_attempts.time, "sleep", staging_sleep)
    try:
        stimulus_attempts._ensure_harness_ready_with_recovery(
            timeout_s=0.05,
            poll_interval_s=0.01,
            ready_path=marker,
            recovery_sleep_s=0.0,
        )
    finally:
        monkeypatch.setattr(stimulus_attempts.time, "sleep", real_sleep)


def test_ensure_harness_ready_with_recovery_exhausts_budget(tmp_path: Path) -> None:
    import pytest

    from executor.flows.playwright.stimulus.types import (
        HARNESS_READY_MARKER_MISSING_REASON,
        HarnessUnavailableError,
    )

    marker = tmp_path / "ready.json"
    with pytest.raises(HarnessUnavailableError) as exc_info:
        stimulus_attempts._ensure_harness_ready_with_recovery(
            timeout_s=0.05,
            poll_interval_s=0.01,
            ready_path=marker,
            recovery_sleep_s=0.0,
        )
    assert exc_info.value.reason_code == HARNESS_READY_MARKER_MISSING_REASON


def test_ensure_harness_ready_with_recovery_does_not_retry_stale(
    tmp_path: Path,
) -> None:
    """STALE is a corruption signal: retry would observe the same defect."""
    import pytest

    from executor.flows.playwright.stimulus.types import (
        HARNESS_READY_MARKER_STALE_REASON,
        HarnessUnavailableError,
    )

    marker = tmp_path / "ready.json"
    marker.write_text(
        _valid_marker_payload(epoch_run_id="previous-container"), encoding="utf-8"
    )
    with pytest.raises(HarnessUnavailableError) as exc_info:
        stimulus_attempts._ensure_harness_ready_with_recovery(
            timeout_s=0.5,
            poll_interval_s=0.05,
            ready_path=marker,
            expected_epoch_run_id="current-container",
            recovery_sleep_s=0.0,
        )
    assert exc_info.value.reason_code == HARNESS_READY_MARKER_STALE_REASON
    # The marker file must still exist — the wrapper must not unlink it
    # because non-recoverable reasons keep their evidence on disk.
    assert marker.exists()


def test_health_summary_reason_labels_cover_w8_0_codes() -> None:
    from executor.flows.playwright.health.summary import automation_reason_to_text

    for code in (
        "harness_ready_marker_missing",
        "harness_ready_marker_stale",
        "harness_ready_marker_invalid",
        "harness_activation_timeout",
    ):
        # The label should be a non-empty human-readable sentence,
        # never the underscore-replaced fallback.
        label = automation_reason_to_text(code)
        assert label
        assert label != code.replace("_", " ")
        assert label.endswith(".")


# --- W22 Fix 4b/4c: inter-command maintenance (cleanup + health gate) --------


def test_is_terminal_command_attempt_detects_terminal_and_repl_commands() -> None:
    for command_id in (
        "python.execInTerminal",
        "python.startREPL",
        "python.startNativeREPL",
        "workbench.action.terminal.new",
    ):
        assert stimulus_maintenance._is_terminal_command_attempt(
            {"event_value": command_id}, "command:auto"
        ), command_id
    # Non-terminal command and non-command action are both False.
    assert not stimulus_maintenance._is_terminal_command_attempt(
        {"event_value": "python.sortImports"}, "command:auto"
    )
    assert not stimulus_maintenance._is_terminal_command_attempt(
        {"event_value": "python.execInTerminal"}, "scenario:coding_session"
    )


def test_post_command_maintenance_noop_for_non_command_action() -> None:
    import pytest

    probed: list[object] = []
    killed: list[object] = []

    def fake_alive(page: object) -> bool:
        probed.append(page)
        return True

    def fake_kill(page: object) -> None:
        killed.append(page)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(stimulus_maintenance.automation, "is_renderer_alive", fake_alive)
        mp.setattr(stimulus_maintenance.terminal, "close_all_terminals", fake_kill)
        page = object()
        dead = stimulus_maintenance.post_command_maintenance(
            page, {"event_value": "x"}, "scenario:coding_session", monitor=None
        )

    # A non-command action does not even probe the renderer or run cleanup.
    assert dead is False
    assert probed == []
    assert killed == []


def test_post_command_maintenance_probes_renderer_after_command() -> None:
    import pytest

    killed: list[object] = []

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            stimulus_maintenance.automation, "is_renderer_alive", lambda page: False
        )
        mp.setattr(
            stimulus_maintenance.terminal,
            "close_all_terminals",
            lambda page: killed.append(page),
        )
        page = object()
        dead = stimulus_maintenance.post_command_maintenance(
            page, {"event_value": "python.sortImports"}, "command:auto", monitor=None
        )

    # Non-terminal command: renderer probed (reported dead), no terminal kill.
    assert dead is True
    assert killed == []


def test_post_command_maintenance_kills_terminals_for_terminal_command() -> None:
    import pytest

    killed: list[object] = []

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            stimulus_maintenance.automation, "is_renderer_alive", lambda page: True
        )
        mp.setattr(
            stimulus_maintenance.terminal,
            "close_all_terminals",
            lambda page: killed.append(page),
        )
        page = object()
        dead = stimulus_maintenance.post_command_maintenance(
            page,
            {
                "event_value": "python.execInTerminal",
                "activation_event": "onCommand:python.execInTerminal",
            },
            "command:auto",
            monitor=None,
        )

    assert dead is False
    assert killed == [page]


def test_post_command_maintenance_terminal_cleanup_is_best_effort() -> None:
    import pytest

    def fake_kill(page: object) -> None:
        raise stimulus_maintenance.PlaywrightError("Target crashed during killAll")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            stimulus_maintenance.automation, "is_renderer_alive", lambda page: False
        )
        mp.setattr(stimulus_maintenance.terminal, "close_all_terminals", fake_kill)
        # A kill that raises (renderer dying) must not propagate; the liveness
        # probe is the source of truth and reports the dead renderer.
        dead = stimulus_maintenance.post_command_maintenance(
            object(),
            {"event_value": "python.startREPL"},
            "command:auto",
            monitor=None,
        )

    assert dead is True
