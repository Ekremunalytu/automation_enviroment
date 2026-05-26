"""W20-1 / W20-2 capability support map invariants.

Pins the official-track promotion flips so a future edit cannot
silently revert them without tripping the gate. Broader track-parity
invariants land at W20-3 in a follow-up file.
"""

from __future__ import annotations

from packages.analysis_planner.capabilities import (
    _GLOBAL_CAPABILITY_SUPPORT,
    _HEURISTIC_CAPABILITY_SUPPORT,
    _OFFICIAL_CAPABILITY_SUPPORT,
    CAPABILITY_TAXONOMY,
)
from packages.analysis_planner.scenarios import SCENARIO_REGISTRY


def test_scm_official_track_is_covered() -> None:
    """W20-1: ``scm`` flipped from ``missing`` → ``covered`` in the
    official track. Pins the flip — see
    ``[GOAL taxonomy-scm-official-promotion]`` at
    ``documents/POST_POC_BACKLOG.md`` W20 Pull-Forward.
    """
    assert _OFFICIAL_CAPABILITY_SUPPORT["scm"] == "covered", (
        "W20-1 promoted `scm` to `covered` in the official track. If this "
        "assertion fails the flip has been reverted; check "
        "`packages/analysis_planner/capabilities.py:88`."
    )


def test_scm_heuristic_track_is_covered() -> None:
    """`scm` was already covered in the heuristic track before W20-1.
    Pinning it here so a future edit cannot silently flip the heuristic
    track to ``missing`` and break the Official ⊆ Heuristic invariant
    (W20-3 lifts that broader invariant to a dedicated gate).
    """
    assert _HEURISTIC_CAPABILITY_SUPPORT["scm"] == "covered"
    assert _GLOBAL_CAPABILITY_SUPPORT["scm"] == "covered"


def test_scm_in_capability_taxonomy() -> None:
    """``scm`` must remain enumerated in ``CAPABILITY_TAXONOMY``.

    The support maps are keyed by taxonomy entries; removing ``scm``
    from the taxonomy without updating the support maps would surface
    only as a KeyError at runtime. Pin the taxonomy membership here.
    """
    assert "scm" in CAPABILITY_TAXONOMY


def test_git_workflow_scenario_advertises_scm_capability() -> None:
    """The W20-1 flip is meaningful only if at least one scenario in
    ``SCENARIO_REGISTRY`` advertises ``scm`` in its ``api_capabilities``.
    Pinning ``git_workflow`` here means a future edit that drops the
    scenario or removes the capability mapping has to also update this
    test — preventing silent drift between the scenario registry and
    the support map.
    """
    scm_scenarios = [
        scenario.name
        for scenario in SCENARIO_REGISTRY
        if "scm" in scenario.api_capabilities
    ]
    assert "git_workflow" in scm_scenarios, (
        "`git_workflow` scenario must advertise `scm` in api_capabilities "
        "so the W20-1 official-track promotion has a concrete coverage path."
    )


def test_settings_official_track_is_covered() -> None:
    """W20-2: ``settings`` flipped from ``missing`` → ``covered`` in
    the official track. Pins the flip — see
    ``[GOAL taxonomy-settings-official-promotion]`` at
    ``documents/POST_POC_BACKLOG.md`` W20 Pull-Forward.
    """
    assert _OFFICIAL_CAPABILITY_SUPPORT["settings"] == "covered", (
        "W20-2 promoted `settings` to `covered` in the official track. "
        "If this assertion fails the flip has been reverted; check "
        "`packages/analysis_planner/capabilities.py:90`."
    )


def test_settings_heuristic_track_is_covered() -> None:
    """`settings` was already covered in the heuristic track before
    W20-2. Pin it here for the same Official ⊆ Heuristic invariant
    pre-emptive coverage as ``test_scm_heuristic_track_is_covered``.
    """
    assert _HEURISTIC_CAPABILITY_SUPPORT["settings"] == "covered"
    assert _GLOBAL_CAPABILITY_SUPPORT["settings"] == "covered"


def test_settings_in_capability_taxonomy() -> None:
    """``settings`` must remain enumerated in ``CAPABILITY_TAXONOMY``."""
    assert "settings" in CAPABILITY_TAXONOMY


def test_settings_modification_scenario_advertises_settings_capability() -> None:
    """W20-2 flip is meaningful only if at least one scenario advertises
    ``settings`` in ``api_capabilities``. ``settings_modification`` is
    the concrete coverage path — pin the scenario registry consistency.
    """
    settings_scenarios = [
        scenario.name
        for scenario in SCENARIO_REGISTRY
        if "settings" in scenario.api_capabilities
    ]
    assert "settings_modification" in settings_scenarios, (
        "`settings_modification` scenario must advertise `settings` in "
        "api_capabilities so the W20-2 official-track promotion has a "
        "concrete coverage path."
    )
