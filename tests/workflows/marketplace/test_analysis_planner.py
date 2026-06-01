from __future__ import annotations

import ast
import json
from pathlib import Path

from packages.analysis_planner import select_scenarios
from packages.analysis_planner.attempts import _is_window_reload_command

_BANNED_IMPORT_ROOTS = {"appcore", "executor", "fastapi", "sqlalchemy", "workflows"}


def _planner_dir() -> Path:
    return Path(__file__).parents[3] / "packages" / "analysis_planner"


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_analysis_planner_modules_avoid_runtime_imports() -> None:
    planner_dir = _planner_dir()

    for module_path in sorted(planner_dir.glob("*.py")):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", maxsplit=1)[0]
                    assert root not in _BANNED_IMPORT_ROOTS, (
                        f"{module_path.name} imports banned module root {root}"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".", maxsplit=1)[0]
                assert root not in _BANNED_IMPORT_ROOTS, (
                    f"{module_path.name} imports banned module root {root}"
                )


def test_ms_python_planner_input_matches_frozen_trigger_fixture() -> None:
    fixtures_dir = Path(__file__).parent / "fixtures"
    planner_input = _load_json(
        fixtures_dir / "planner_inputs" / "ms_python_python.json"
    )
    expected_payload = _load_json(
        fixtures_dir / "trigger_payloads" / "ms_python_python.json"
    )

    payload = select_scenarios(
        planner_input["activation_events"],
        publisher_name=str(planner_input["publisher_name"]),
        contributes_commands=planner_input["contributes_commands"],
        contributes_walkthroughs=planner_input["contributes_walkthroughs"],
    )

    assert payload.model_dump(mode="json") == expected_payload


def test_is_window_reload_command_detects_reload_not_restart() -> None:
    assert _is_window_reload_command("python.clearCacheAndReload")
    assert _is_window_reload_command("foo.bar", "Reload Window")
    # ``restart`` is intentionally NOT reload-class — a language-server restart
    # does not reload the window.
    assert not _is_window_reload_command("python.analysis.restartLanguageServer")
    assert not _is_window_reload_command("python.runTests", "Run Tests")


def test_reload_class_command_deferred_to_final_pass_and_ordered_last() -> None:
    """W22 Fix 4a: a contributed ``*reload*`` command blacks out the renderer if
    it runs early (the layered executor can't reconnect). The planner must
    defer it out of the early UI pass to the final executable pass, ordered
    last — without dropping it (it still runs, just last)."""
    payload = select_scenarios(
        [{"event_type": "onStartupFinished", "event_value": None}],
        publisher_name="pub.ext",
        contributes_commands=[
            {"command": "pub.doThing", "title": "Do Thing"},
            {"command": "pub.clearCacheAndReload", "title": "Clear Cache and Reload"},
            {"command": "pub.other", "title": "Other"},
        ],
    )
    data = payload.model_dump(mode="json")
    by_pass = {p["pass_id"]: p["attempt_ids"] for p in data["stimulus_passes"]}
    reload_id = next(
        a["attempt_id"]
        for a in data["event_attempts"]
        if a["event_value"] == "pub.clearCacheAndReload"
    )

    # Still synthesized (not dropped)...
    assert reload_id in {a["attempt_id"] for a in data["event_attempts"]}
    # ...not in the early UI pass...
    assert reload_id not in by_pass["ui_first_user_session"]
    # ...and ordered LAST within the final executable pass.
    assert by_pass["unresolved_event_backfill"][-1] == reload_id
    # Non-reload contributed commands still run in the early UI pass.
    other_ids = {
        a["attempt_id"]
        for a in data["event_attempts"]
        if a["event_value"] in {"pub.doThing", "pub.other"}
    }
    assert other_ids <= set(by_pass["ui_first_user_session"])
