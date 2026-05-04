"""W10-3 regression: registry.py split into 4 focus modules + facade.

Pins two invariants:

1. The four focus modules (``capabilities``, ``scenarios``,
   ``event_scenario_index``, ``pass_order``) import standalone, with no
   accidental cross-module dependency that would defeat the split.
2. The ``registry`` facade re-exports every name the historic monolith
   exposed, so existing call sites keep working unchanged.
"""

from __future__ import annotations

import importlib

import pytest


# Names the historic monolithic registry.py exposed and that downstream
# call sites import. If a name leaves this list the facade re-export is
# also drifting and the regression test must be updated alongside the
# downstream change.
_FACADE_SURFACE: tuple[str, ...] = (
    "CAPABILITY_TAXONOMY",
    "EVENT_TYPE_TO_SCENARIOS",
    "EventStrategy",
    "HEURISTIC_EVENT_TYPE_TO_SCENARIOS",
    "OFFICIAL_EVENT_REGISTRY",
    "SCENARIO_REGISTRY",
    "ScenarioDefinition",
    "_BUILTIN_VIEW_IDS",
    "_GLOBAL_CAPABILITY_NOTES",
    "_GLOBAL_CAPABILITY_SUPPORT",
    "_HEURISTIC_CAPABILITY_SUPPORT",
    "_HEURISTIC_TRACK",
    "_MAX_EXTRA_COMMANDS",
    "_MAX_SCENARIOS_PER_RUN",
    "_OFFICIAL_CAPABILITY_SUPPORT",
    "_OFFICIAL_TRACK",
    "_PASS_DESCRIPTIONS",
    "_PASS_LABELS",
    "_PASS_ORDER",
    "_SCENARIO_BY_NAME",
    "_SCENARIO_PRIORITY",
    "_TRACK_SOURCE",
)


@pytest.mark.parametrize(
    "module_name",
    [
        "packages.analysis_planner.capabilities",
        "packages.analysis_planner.scenarios",
        "packages.analysis_planner.event_scenario_index",
        "packages.analysis_planner.pass_order",
    ],
)
def test_focus_modules_import_standalone(module_name: str) -> None:
    """Each focus module must import without pulling in any of the others."""
    module = importlib.import_module(module_name)
    assert module is not None


def test_facade_exports_full_historic_surface() -> None:
    """registry.py facade must re-export every historic name."""
    facade = importlib.import_module("packages.analysis_planner.registry")
    missing = [name for name in _FACADE_SURFACE if not hasattr(facade, name)]
    assert missing == [], f"facade is missing historic names: {missing}"


def test_facade_all_matches_historic_surface() -> None:
    """``__all__`` must list exactly the historic surface — no quiet drift."""
    facade = importlib.import_module("packages.analysis_planner.registry")
    declared = tuple(sorted(facade.__all__))
    expected = tuple(sorted(_FACADE_SURFACE))
    assert declared == expected


def test_facade_objects_are_identity_equal_to_focus_module_objects() -> None:
    """Facade re-exports must be the SAME objects as the focus modules
    expose — no copies — so monkeypatching a facade name from a test still
    affects the source module."""
    capabilities = importlib.import_module("packages.analysis_planner.capabilities")
    scenarios = importlib.import_module("packages.analysis_planner.scenarios")
    events = importlib.import_module("packages.analysis_planner.event_scenario_index")
    pass_order = importlib.import_module("packages.analysis_planner.pass_order")
    facade = importlib.import_module("packages.analysis_planner.registry")

    assert facade.CAPABILITY_TAXONOMY is capabilities.CAPABILITY_TAXONOMY
    assert facade.SCENARIO_REGISTRY is scenarios.SCENARIO_REGISTRY
    assert facade.OFFICIAL_EVENT_REGISTRY is events.OFFICIAL_EVENT_REGISTRY
    assert facade._PASS_ORDER is pass_order._PASS_ORDER
    assert facade.ScenarioDefinition is scenarios.ScenarioDefinition
    assert facade.EventStrategy is events.EventStrategy


def test_split_did_not_lose_data_volume() -> None:
    """Sanity: shape of the registry matches the historic counts."""
    facade = importlib.import_module("packages.analysis_planner.registry")
    assert len(facade.SCENARIO_REGISTRY) == 13
    assert len(facade.OFFICIAL_EVENT_REGISTRY) == 29
    assert len(facade.CAPABILITY_TAXONOMY) == 18
    assert len(facade._PASS_ORDER) == 5
    assert len(facade._BUILTIN_VIEW_IDS) == 5
