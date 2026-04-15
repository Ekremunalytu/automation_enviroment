from __future__ import annotations

import ast
import json
from pathlib import Path

from packages.analysis_planner import select_scenarios

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
                    assert (
                        root not in _BANNED_IMPORT_ROOTS
                    ), f"{module_path.name} imports banned module root {root}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".", maxsplit=1)[0]
                assert (
                    root not in _BANNED_IMPORT_ROOTS
                ), f"{module_path.name} imports banned module root {root}"


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
