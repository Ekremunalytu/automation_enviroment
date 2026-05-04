"""Backward-compat facade for the W10-3 planner registry split.

The historic 669 LoC monolith was split into four focus modules:

- ``capabilities`` — capability taxonomy + per-track support matrices
- ``scenarios`` — scenario definitions + lookup helpers
- ``event_scenario_index`` — event family strategies + reverse-lookup maps
- ``pass_order`` — stimulus pass ordering + per-run limit constants

All names that the historic registry exposed are re-exported here so existing
``from packages.analysis_planner.registry import ...`` call sites keep working
without churn. New code should import from the focus module directly.
"""

from __future__ import annotations

from packages.analysis_planner.capabilities import (
    _GLOBAL_CAPABILITY_NOTES,
    _GLOBAL_CAPABILITY_SUPPORT,
    _HEURISTIC_CAPABILITY_SUPPORT,
    _HEURISTIC_TRACK,
    _OFFICIAL_CAPABILITY_SUPPORT,
    _OFFICIAL_TRACK,
    _TRACK_SOURCE,
    CAPABILITY_TAXONOMY,
)
from packages.analysis_planner.event_scenario_index import (
    _BUILTIN_VIEW_IDS,
    EVENT_TYPE_TO_SCENARIOS,
    HEURISTIC_EVENT_TYPE_TO_SCENARIOS,
    OFFICIAL_EVENT_REGISTRY,
    EventStrategy,
)
from packages.analysis_planner.pass_order import (
    _MAX_EXTRA_COMMANDS,
    _MAX_SCENARIOS_PER_RUN,
    _PASS_DESCRIPTIONS,
    _PASS_LABELS,
    _PASS_ORDER,
)
from packages.analysis_planner.scenarios import (
    _SCENARIO_BY_NAME,
    _SCENARIO_PRIORITY,
    SCENARIO_REGISTRY,
    ScenarioDefinition,
)

__all__ = [
    "CAPABILITY_TAXONOMY",
    "EVENT_TYPE_TO_SCENARIOS",
    "HEURISTIC_EVENT_TYPE_TO_SCENARIOS",
    "OFFICIAL_EVENT_REGISTRY",
    "SCENARIO_REGISTRY",
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
    "EventStrategy",
    "ScenarioDefinition",
]
