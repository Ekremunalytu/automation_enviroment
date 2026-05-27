"""W20-1 / W20-2 / W20-3 capability support map invariants.

W20-1 + W20-2 pinned the per-capability official-track promotion
flips (``scm`` + ``settings``). W20-3 lifts the broader contract
invariants: keyset parity across the three maps + Official ⊆
Heuristic subset rule + ``_GLOBAL_CAPABILITY_NOTES`` ↔ taxonomy
alignment + ``CAPABILITY_TAXONOMY`` ordering pin. Together these
protect future track promotions against silent regressions.
"""

from __future__ import annotations

from packages.analysis_planner.capabilities import (
    _GLOBAL_CAPABILITY_NOTES,
    _GLOBAL_CAPABILITY_SUPPORT,
    _HEURISTIC_CAPABILITY_SUPPORT,
    _OFFICIAL_CAPABILITY_SUPPORT,
    CAPABILITY_TAXONOMY,
)
from packages.analysis_planner.scenarios import SCENARIO_REGISTRY


_EXPECTED_CAPABILITY_TAXONOMY: tuple[str, ...] = (
    "commands",
    "window_ui",
    "workspace_fs",
    "languages_editor",
    "debug",
    "terminal_tasks",
    "scm",
    "search_views",
    "settings",
    "notebooks",
    "custom_editors",
    "uri_walkthrough",
    "authentication",
    "chat",
    "comments",
    "testing",
    "webview",
    "workspace_trust",
)


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


# ---------------------------------------------------------------------
# W21-3 — Workspace trust mid-tier promotion
# ---------------------------------------------------------------------


def test_workspace_trust_official_track_is_covered() -> None:
    """W21-3: ``workspace_trust`` flipped from ``missing`` → ``covered``
    in the official track. Pins the flip — see
    ``[GOAL taxonomy-workspace-trust-coverage]`` at
    ``documents/POST_POC_BACKLOG.md`` W21 Pull-Forward.
    """
    assert _OFFICIAL_CAPABILITY_SUPPORT["workspace_trust"] == "covered", (
        "W21-3 promoted `workspace_trust` to `covered` in the official "
        "track. If this assertion fails the flip has been reverted; "
        "check `packages/analysis_planner/capabilities.py:99`."
    )


def test_workspace_trust_heuristic_track_is_covered() -> None:
    """W21-3 partner pin to the official-track flip.

    ``_HEURISTIC_CAPABILITY_SUPPORT`` derives from
    ``_GLOBAL_CAPABILITY_SUPPORT``; both must read ``covered`` so the
    Official ⊆ Heuristic invariant (W20-3 gate) is satisfied after the
    flip and so a future edit cannot silently regress the heuristic
    track.
    """
    assert _HEURISTIC_CAPABILITY_SUPPORT["workspace_trust"] == "covered"
    assert _GLOBAL_CAPABILITY_SUPPORT["workspace_trust"] == "covered"


def test_workspace_trust_in_capability_taxonomy() -> None:
    """``workspace_trust`` must remain enumerated in ``CAPABILITY_TAXONOMY``.

    The support maps are keyed by taxonomy entries; removing
    ``workspace_trust`` from the taxonomy without updating the support
    maps would surface only as a KeyError at runtime. Pin the taxonomy
    membership here.
    """
    assert "workspace_trust" in CAPABILITY_TAXONOMY


def test_workspace_trust_transition_scenario_advertises_workspace_trust_capability() -> (
    None
):
    """W21-3 flip is meaningful only if at least one scenario in
    ``SCENARIO_REGISTRY`` advertises ``workspace_trust`` in its
    ``api_capabilities``. Pinning ``workspace_trust_transition`` here
    means a future edit that drops the scenario or removes the
    capability mapping has to also update this test — preventing silent
    drift between the scenario registry and the support map.
    """
    workspace_trust_scenarios = [
        scenario.name
        for scenario in SCENARIO_REGISTRY
        if "workspace_trust" in scenario.api_capabilities
    ]
    assert "workspace_trust_transition" in workspace_trust_scenarios, (
        "`workspace_trust_transition` scenario must advertise "
        "`workspace_trust` in api_capabilities so the W21-3 "
        "official-track promotion has a concrete coverage path."
    )


# ---------------------------------------------------------------------
# W20-3 — Coverage matrix contract invariants
# ---------------------------------------------------------------------


def test_support_map_keysets_match_taxonomy() -> None:
    """W20-3 invariant 1 (keyset parity).

    ``_OFFICIAL_CAPABILITY_SUPPORT`` and ``_HEURISTIC_CAPABILITY_SUPPORT``
    are both keyed by ``CAPABILITY_TAXONOMY``. A future edit that adds
    a key to one map but not the other (or to a map but not the
    taxonomy) would surface only as a KeyError at runtime; pin the
    set equality here so the gate fires at static-test time.
    """
    taxonomy_set = set(CAPABILITY_TAXONOMY)
    official_keys = set(_OFFICIAL_CAPABILITY_SUPPORT.keys())
    heuristic_keys = set(_HEURISTIC_CAPABILITY_SUPPORT.keys())
    global_keys = set(_GLOBAL_CAPABILITY_SUPPORT.keys())

    assert official_keys == taxonomy_set, (
        f"_OFFICIAL_CAPABILITY_SUPPORT keyset drift: "
        f"missing from taxonomy = {official_keys - taxonomy_set}, "
        f"missing from map = {taxonomy_set - official_keys}."
    )
    assert heuristic_keys == taxonomy_set, (
        f"_HEURISTIC_CAPABILITY_SUPPORT keyset drift: "
        f"missing from taxonomy = {heuristic_keys - taxonomy_set}, "
        f"missing from map = {taxonomy_set - heuristic_keys}."
    )
    assert global_keys == taxonomy_set, (
        f"_GLOBAL_CAPABILITY_SUPPORT keyset drift: "
        f"missing from taxonomy = {global_keys - taxonomy_set}, "
        f"missing from map = {taxonomy_set - global_keys}."
    )


def test_official_track_is_subset_of_heuristic() -> None:
    """W20-3 invariant 2 (Official ⊆ Heuristic).

    Official-track coverage means an event-level trigger AND a scenario
    exist. Heuristic-track coverage means a workflow scenario exists
    (broader scope). Therefore an official-covered capability must also
    be heuristic-covered; an official-covered capability that's
    heuristic-missing is incoherent. Pin the subset rule.
    """
    incoherent: list[str] = []
    for capability in CAPABILITY_TAXONOMY:
        official = _OFFICIAL_CAPABILITY_SUPPORT[capability]
        heuristic = _HEURISTIC_CAPABILITY_SUPPORT[capability]
        if official == "covered" and heuristic != "covered":
            incoherent.append(
                f"{capability}: official={official!r}, heuristic={heuristic!r}"
            )
    assert not incoherent, (
        "Official ⊆ Heuristic invariant violated — an official-covered "
        "capability cannot be heuristic-missing: " + "; ".join(incoherent)
    )


def test_capability_notes_keys_subset_of_taxonomy() -> None:
    """W20-3 invariant 3 (notes ↔ taxonomy alignment).

    ``_GLOBAL_CAPABILITY_NOTES`` carries policy text for selected
    capabilities (``custom_editors``, ``chat``, ``comments``, etc.).
    Every notes key must reference an enumerated taxonomy capability;
    a notes entry for a removed/renamed capability would silently
    drift otherwise.
    """
    extra_keys = set(_GLOBAL_CAPABILITY_NOTES.keys()) - set(CAPABILITY_TAXONOMY)
    assert not extra_keys, (
        f"_GLOBAL_CAPABILITY_NOTES has policy entries for capabilities "
        f"not in CAPABILITY_TAXONOMY: {sorted(extra_keys)}"
    )


def test_capability_taxonomy_ordering_is_canonical() -> None:
    """W20-3 invariant 4 (anti-drift on ordering).

    The taxonomy order is referenced by coverage matrix emit logic
    (``coverage.py`` iterates ``CAPABILITY_TAXONOMY`` to build the
    matrix). Pinning the exact sequence here means any insertion or
    reordering trips the gate and forces the change to be intentional.
    """
    assert tuple(CAPABILITY_TAXONOMY) == _EXPECTED_CAPABILITY_TAXONOMY, (
        "CAPABILITY_TAXONOMY ordering drifted. Expected:\n"
        f"  {_EXPECTED_CAPABILITY_TAXONOMY}\nActual:\n"
        f"  {tuple(CAPABILITY_TAXONOMY)}"
    )


def test_w20_1_and_w20_2_post_condition_combined() -> None:
    """W20-3 invariant 5 (combined post-condition gate).

    Even if ``test_scm_official_track_is_covered`` or
    ``test_settings_official_track_is_covered`` regresses, this combined
    gate fires the same way — making the W20-1 + W20-2 acceptance
    surface a single auditable invariant rather than two scattered
    pins. Live coverage matrix consumer (``coverage.py``) relies on
    these two flips for `scm` + `settings` to land in
    `partial`/`covered` rather than `missing`.
    """
    must_be_covered = ("scm", "settings")
    actual = {c: _OFFICIAL_CAPABILITY_SUPPORT[c] for c in must_be_covered}
    expected = dict.fromkeys(must_be_covered, "covered")
    assert actual == expected, (
        "W20-1 + W20-2 post-condition regression: scm + settings must "
        f"remain `covered` in the official track. Got: {actual}"
    )


def test_official_capability_support_dict_shape_is_canonical() -> None:
    """W20-5 invariant (full dict shape pin).

    The broader sibling of ``test_w20_1_and_w20_2_post_condition_combined``
    — pins the full ``_OFFICIAL_CAPABILITY_SUPPORT`` value map at the
    W20-end state. Any single-key value change (including future W21-1
    ``testing``, W21-2 ``comments``, W21-3 ``workspace_trust``, or W22-2
    ``chat`` flips) must update both the live map and this expected
    shape together.

    Catches drift the individual scm/settings tests miss: e.g. an
    accidental flip of ``debug`` to ``"missing"`` would pass the W20-1
    + W20-2 gates yet fail here. The W21 capability flips are the
    natural touch point for advancing this constant.
    """
    expected_shape: dict[str, str] = {
        "commands": "covered",
        "window_ui": "covered",
        "workspace_fs": "covered",
        "languages_editor": "covered",
        "debug": "covered",
        "terminal_tasks": "covered",
        "scm": "covered",  # W20-1 promotion
        "search_views": "covered",
        "settings": "covered",  # W20-2 promotion
        "notebooks": "covered",
        "custom_editors": "covered",
        "uri_walkthrough": "covered",
        "authentication": "covered",
        "chat": "missing",  # W22-2 candidate (hard tier)
        "comments": "missing",  # W21-2 candidate (mid tier)
        "testing": "missing",  # W21-1 candidate (mid tier)
        "webview": "covered",
        "workspace_trust": "covered",  # W21-3 promotion
    }
    assert expected_shape == _OFFICIAL_CAPABILITY_SUPPORT, (
        "_OFFICIAL_CAPABILITY_SUPPORT shape drift. If you intentionally "
        "flipped a capability (e.g., a W21 mid-tier promotion of "
        "testing/comments/workspace_trust, or a W22 chat promotion), "
        "update `expected_shape` in this test alongside the actual "
        f"map.\nExpected: {expected_shape}\nActual: {_OFFICIAL_CAPABILITY_SUPPORT}"
    )
