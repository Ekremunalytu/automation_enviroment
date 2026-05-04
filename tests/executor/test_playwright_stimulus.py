from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from executor.flows.playwright import stimulus, stimulus_attempts
from packages.analysis_contracts import TriggerPayload


class _FakeMonitor:
    def __init__(self) -> None:
        self.results: list[dict[str, object]] = []
        self.pass_events: list[dict[str, object]] = []
        self.attempt_starts: list[dict[str, object]] = []
        self.attempt_ends: list[dict[str, object]] = []
        self.scenario_events: list[dict[str, object]] = []

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

    result = stimulus.run_stimulus_plan(object(), payload, monitor=monitor)

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

    from executor.flows.playwright.stimulus_types import (
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

    from executor.flows.playwright.stimulus_types import (
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

    from executor.flows.playwright.stimulus_types import (
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

    from executor.flows.playwright.stimulus_types import (
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

    from executor.flows.playwright.stimulus_types import (
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

    from executor.flows.playwright.stimulus_types import (
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
    from executor.flows.playwright.health_summary import automation_reason_to_text

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
