"""Serialization and filesystem helpers for planner payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from packages.analysis_contracts import TriggerPayload
from packages.analysis_planner.registry import EventStrategy, ScenarioDefinition
from packages.marketplace_identity import safe_marketplace_slug


def write_trigger_file(
    publisher: str,
    name: str,
    version: str,
    payload: TriggerPayload,
    output_dir: str = "output",
) -> str:
    """Write trigger payload to a JSON file on the shared volume."""

    filename = f"triggers_{safe_marketplace_slug(publisher, name, version)}.json"
    host_path = Path(output_dir) / filename
    host_path.parent.mkdir(parents=True, exist_ok=True)
    host_path.write_text(
        json.dumps(payload.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    return f"/results/{filename}"


def _collect_contributed_view_ids(contributes_views: dict[str, Any] | None) -> set[str]:
    view_ids: set[str] = set()
    if not contributes_views:
        return view_ids
    for views in contributes_views.values():
        if not isinstance(views, list):
            continue
        for view in views:
            if not isinstance(view, dict):
                continue
            view_id = view.get("id")
            if view_id:
                view_ids.add(str(view_id))
    return view_ids


def _serialize_scenario_definition(
    scenario: ScenarioDefinition,
    selection_reasons: list[str],
) -> dict[str, Any]:
    return {
        "name": scenario.name,
        "intent": scenario.intent,
        "activation_events": list(scenario.activation_events),
        "contributes_signals": list(scenario.contributes_signals),
        "api_capabilities": list(scenario.api_capabilities),
        "prerequisites": list(scenario.prerequisites),
        "success_signals": list(scenario.success_signals),
        "risk_of_noise": scenario.risk_of_noise,
        "selection_reasons": selection_reasons,
    }


def _serialize_event_strategy(strategy: EventStrategy) -> dict[str, Any]:
    return {
        "family": strategy.family,
        "capability_tags": list(strategy.capability_tags),
        "executor_group": strategy.executor_group,
        "prerequisites": list(strategy.prerequisites),
        "verification_contract": list(strategy.verification_contract),
        "legacy_scenarios": list(strategy.legacy_scenarios),
        "ui_path": strategy.ui_path,
        "harness_fallback": strategy.harness_fallback or "",
        "official": strategy.official,
        "heuristic": strategy.heuristic,
    }


def _activation_label(event_type: str, event_value: str | None) -> str:
    if event_value:
        return f"{event_type}:{event_value}"
    return event_type


def glob_to_bait_filename(pattern: str) -> str | None:
    """Convert a VS Code filenamePattern glob to a concrete bait filename."""

    name_part = pattern.rsplit("/", maxsplit=1)[-1]

    if name_part.startswith("*."):
        ext = name_part[2:]
        if ext.startswith("{") and "}" in ext:
            ext = ext[1 : ext.index("}")]
            if "," in ext:
                ext = ext.split(",")[0]
        return f"bait.{ext}"

    if "*" not in name_part and "?" not in name_part:
        return name_part

    return None


def _slugify(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value).strip("-").lower()
