"""Direct-module tests for ``executor.flows.playwright.attribution.events``.

[FOLLOWUP w12-precursor-tests-attribution-events] safety net before the W12
attribution facade cleanup (`§11.9` underscore re-export rework). Imports the
module by its real path (not via ``attribution.__init__`` re-exports) so the
public event-annotation surface is pinned independently of the facade
rearrangement that W12-2 will perform.

Scope: pure helpers (timestamp + actor + artifact-class) and the attribution
classifier branches (`_classify_event_attribution`), plus shape-level pins for
the three annotators (network/file/process). Inotify→corroboration upgrade is
covered explicitly.
"""

from __future__ import annotations

from datetime import datetime

from executor.flows.playwright.attribution import events as attribution_events
from executor.flows.playwright.monitor.records import ScenarioTrace
from executor.flows.playwright.runtime_capture.events import (
    ActivationEntry,
    FileEvent,
    NetworkEvent,
    ProcessEvent,
)


# ---------------------------------------------------------------------------
# _format_epoch_timestamp — empty/zero/positive
# ---------------------------------------------------------------------------


def test_format_epoch_timestamp_zero_returns_empty_string() -> None:
    assert attribution_events.format_epoch_timestamp(0.0) == ""


def test_format_epoch_timestamp_none_returns_empty_string() -> None:
    assert attribution_events.format_epoch_timestamp(None) == ""


def test_format_epoch_timestamp_positive_returns_iso_with_milliseconds() -> None:
    epoch = datetime(2026, 1, 1, 10, 0, 0, 500_000).timestamp()
    formatted = attribution_events.format_epoch_timestamp(epoch)
    # The exact local-tz string is platform dependent, but ms precision and
    # the ISO `T` separator are not. Assert structural shape only.
    assert "T" in formatted
    assert formatted.endswith(".500")


# ---------------------------------------------------------------------------
# _relative_time — fallback chain on None / non-positive monitoring start
# ---------------------------------------------------------------------------


def test_relative_time_returns_none_when_event_epoch_is_none() -> None:
    assert attribution_events.relative_time(None, monitoring_start=1000.0) is None


def test_relative_time_returns_none_when_monitoring_start_not_positive() -> None:
    assert attribution_events.relative_time(1000.5, monitoring_start=0.0) is None


def test_relative_time_clamps_negative_delta_to_zero() -> None:
    # Event predates monitoring_start → 0.0, never negative.
    assert attribution_events.relative_time(999.0, monitoring_start=1000.0) == 0.0


def test_relative_time_rounds_positive_delta_to_three_decimals() -> None:
    assert attribution_events.relative_time(1000.4567, monitoring_start=1000.0) == 0.457


# ---------------------------------------------------------------------------
# _resolve_event_epoch — timestamp first, then rel_time + base, else None
# ---------------------------------------------------------------------------


def test_resolve_event_epoch_prefers_iso_timestamp_over_rel_time() -> None:
    expected = datetime.fromisoformat("2026-01-01T10:00:00").timestamp()
    epoch = attribution_events._resolve_event_epoch(
        timestamp="2026-01-01T10:00:00",
        rel_time_s=99.0,
        base_time=1.0,  # ignored since timestamp parsed
    )
    assert epoch == expected


def test_resolve_event_epoch_falls_back_to_rel_time_plus_base() -> None:
    epoch = attribution_events._resolve_event_epoch(
        timestamp="",
        rel_time_s=0.5,
        base_time=1000.0,
    )
    assert epoch == 1000.5


def test_resolve_event_epoch_returns_none_when_no_data() -> None:
    assert (
        attribution_events._resolve_event_epoch(
            timestamp="", rel_time_s=None, base_time=0.0
        )
        is None
    )


# ---------------------------------------------------------------------------
# _actor_from_file_source / _actor_from_network_event — small dispatch
# ---------------------------------------------------------------------------


def test_actor_from_file_source_known_values_pass_through() -> None:
    assert attribution_events._actor_from_file_source("extension") == "extension"
    assert attribution_events._actor_from_file_source("automation") == "automation"
    assert attribution_events._actor_from_file_source("system") == "system"


def test_actor_from_file_source_unknown_falls_back_to_unknown() -> None:
    assert attribution_events._actor_from_file_source("garbage") == "unknown"
    assert attribution_events._actor_from_file_source("") == "unknown"


def test_actor_from_network_event_target_extension_returns_extension() -> None:
    event = NetworkEvent(is_target_extension_event=True)
    assert attribution_events._actor_from_network_event(event) == "extension"


def test_actor_from_network_event_non_target_returns_unknown() -> None:
    # Both branches (near_target_activation / other) collapse to "unknown".
    near = NetworkEvent(attribution_status="near_target_activation")
    other = NetworkEvent(attribution_status="unattributed")
    assert attribution_events._actor_from_network_event(near) == "unknown"
    assert attribution_events._actor_from_network_event(other) == "unknown"


# ---------------------------------------------------------------------------
# _artifact_class_for_path — workspace_runtime vs manifest_ingestion
# ---------------------------------------------------------------------------


def test_artifact_class_for_path_workspace_package_json_classifies_as_runtime() -> None:
    assert (
        attribution_events._artifact_class_for_path("/workspace/foo/package.json")
        == "workspace_runtime"
    )


def test_artifact_class_for_path_other_package_json_classifies_as_ingestion() -> None:
    assert (
        attribution_events._artifact_class_for_path(
            "/home/executor/.vscode/extensions/foo/package.json"
        )
        == "manifest_ingestion"
    )


def test_artifact_class_for_path_non_package_json_returns_empty() -> None:
    assert attribution_events._artifact_class_for_path("/workspace/x.json") == ""
    assert attribution_events._artifact_class_for_path("") == ""


# ---------------------------------------------------------------------------
# _nearest_activation_matches — returns (target_match, competitor_match)
# ---------------------------------------------------------------------------


def test_nearest_activation_matches_returns_none_pair_when_event_epoch_missing() -> (
    None
):
    target_match, competitor_match = attribution_events._nearest_activation_matches(
        event_epoch=None,
        activations=[ActivationEntry(extension_id="ext.target")],
        target_extension_id="ext.target",
    )
    assert target_match is None
    assert competitor_match is None


def test_nearest_activation_matches_picks_nearest_target_and_separate_competitor() -> (
    None
):
    activations = [
        ActivationEntry(
            extension_id="ext.target",
            timestamp="2026-01-01T10:00:00.000",
        ),
        ActivationEntry(
            extension_id="ext.target",
            timestamp="2026-01-01T10:00:02.000",  # closer to event
        ),
        ActivationEntry(
            extension_id="ext.other",
            timestamp="2026-01-01T10:00:01.500",
        ),
    ]
    event_epoch = datetime.fromisoformat("2026-01-01T10:00:02.000").timestamp()

    target_match, competitor_match = attribution_events._nearest_activation_matches(
        event_epoch=event_epoch,
        activations=activations,
        target_extension_id="ext.target",
    )

    assert target_match is not None
    target_entry, target_delta = target_match
    assert target_entry.extension_id == "ext.target"
    assert target_delta == 0.0  # exact match

    assert competitor_match is not None
    competitor_entry, _ = competitor_match
    assert competitor_entry.extension_id == "ext.other"


def test_nearest_activation_matches_drops_activations_outside_5s_window() -> None:
    activations = [
        ActivationEntry(
            extension_id="ext.target",
            timestamp="2026-01-01T10:00:00.000",
        ),
    ]
    # Event 6 seconds after the only activation → no match.
    event_epoch = datetime.fromisoformat("2026-01-01T10:00:06.000").timestamp()

    target_match, competitor_match = attribution_events._nearest_activation_matches(
        event_epoch=event_epoch,
        activations=activations,
        target_extension_id="ext.target",
    )
    assert target_match is None
    assert competitor_match is None


# ---------------------------------------------------------------------------
# _classify_event_attribution — branch coverage
# ---------------------------------------------------------------------------


def test_classify_event_attribution_inotify_observer_short_circuits_to_automation_noise() -> (
    None
):
    status, basis, confidence, ext_id, act_evt, is_target, noise = (
        attribution_events._classify_event_attribution(
            event_epoch=1000.0,
            activations=[],
            target_extension_id="ext.target",
            observer="inotify",
        )
    )
    assert status == "automation_noise"
    assert confidence == 0.0
    assert is_target is False
    assert noise  # non-empty narrative
    assert basis  # non-empty narrative
    # Unused fields stay empty for the inotify short-circuit.
    assert ext_id == ""
    assert act_evt == ""


def test_classify_event_attribution_missing_target_id_returns_unattributed() -> None:
    status, _basis, confidence, _ext, _act_evt, is_target, _noise = (
        attribution_events._classify_event_attribution(
            event_epoch=1000.0,
            activations=[ActivationEntry(extension_id="ext.target")],
            target_extension_id="",
            observer="strace",
        )
    )
    assert status == "unattributed"
    assert confidence == 0.0
    assert is_target is False


def test_classify_event_attribution_strace_within_tight_window_uses_high_confidence() -> (
    None
):
    activations = [
        ActivationEntry(
            extension_id="ext.target",
            timestamp="2026-01-01T10:00:00.000",
            activation_event="onCommand:tool.run",
        ),
    ]
    # Event 0.2s after activation → tight window → confidence=0.93.
    event_epoch = datetime.fromisoformat("2026-01-01T10:00:00.200").timestamp()

    status, _basis, confidence, ext_id, act_evt, is_target, _noise = (
        attribution_events._classify_event_attribution(
            event_epoch=event_epoch,
            activations=activations,
            target_extension_id="ext.target",
            observer="strace",
        )
    )
    assert status == "target_attributed"
    assert confidence == 0.93
    assert ext_id == "ext.target"
    assert act_evt == "onCommand:tool.run"
    assert is_target is True


def test_classify_event_attribution_competing_activation_demotes_to_competing_candidate() -> (
    None
):
    activations = [
        ActivationEntry(
            extension_id="ext.target",
            timestamp="2026-01-01T10:00:00.500",
        ),
        ActivationEntry(
            extension_id="ext.other",
            timestamp="2026-01-01T10:00:00.400",  # closer than target
        ),
    ]
    event_epoch = datetime.fromisoformat("2026-01-01T10:00:00.500").timestamp()

    status, _basis, confidence, _ext, _act_evt, is_target, _noise = (
        attribution_events._classify_event_attribution(
            event_epoch=event_epoch,
            activations=activations,
            target_extension_id="ext.target",
            observer="strace",
        )
    )
    assert status == "competing_candidate"
    assert is_target is False
    assert confidence == 0.45


def test_classify_event_attribution_network_observer_in_far_window_marks_near_target() -> (
    None
):
    activations = [
        ActivationEntry(
            extension_id="ext.target",
            timestamp="2026-01-01T10:00:00.000",
        ),
    ]
    # 2s after activation → outside the tight 0.75s window but inside the
    # 5s outer band → near_target_activation.
    event_epoch = datetime.fromisoformat("2026-01-01T10:00:02.000").timestamp()

    status, _basis, _confidence, _ext, _act_evt, is_target, _noise = (
        attribution_events._classify_event_attribution(
            event_epoch=event_epoch,
            activations=activations,
            target_extension_id="ext.target",
            observer="network",
        )
    )
    assert status == "near_target_activation"
    assert is_target is False


# ---------------------------------------------------------------------------
# _upgrade_inotify_correlations — duplicate strace+inotify → corroboration
# ---------------------------------------------------------------------------


def test_upgrade_inotify_correlations_promotes_matching_pair_within_one_second() -> (
    None
):
    strace_event = FileEvent(
        timestamp="2026-01-01T10:00:00.000",
        observer="strace",
        path="/workspace/secret.txt",
        operation="read",
        attribution_status="target_attributed",
    )
    inotify_event = FileEvent(
        timestamp="2026-01-01T10:00:00.500",
        observer="inotify",
        path="/workspace/secret.txt",
        operation="read",
        attribution_status="automation_noise",
    )

    upgraded = attribution_events._upgrade_inotify_correlations(
        [strace_event, inotify_event]
    )

    inotify_after = next(e for e in upgraded if e.observer == "inotify")
    assert inotify_after.attribution_status == "corroboration"
    assert inotify_after.attribution_confidence == 0.25
    assert inotify_after.attribution_basis  # narrative populated
    assert "duplicate" in inotify_after.noise_reason


def test_upgrade_inotify_correlations_leaves_lone_inotify_alone() -> None:
    inotify_event = FileEvent(
        timestamp="2026-01-01T10:00:00.000",
        observer="inotify",
        path="/workspace/x",
        operation="read",
        attribution_status="automation_noise",
    )

    upgraded = attribution_events._upgrade_inotify_correlations([inotify_event])

    # Without a paired strace event, the inotify entry stays as-is.
    assert upgraded[0].attribution_status == "automation_noise"


# ---------------------------------------------------------------------------
# _scenario_name_for_timestamp — window membership
# ---------------------------------------------------------------------------


def test_scenario_name_for_timestamp_returns_name_when_inside_window() -> None:
    monitoring_start = datetime.fromisoformat("2026-01-01T10:00:00.000").timestamp()
    trace = ScenarioTrace(
        name="canary",
        started_at=monitoring_start + 5.0,
        ended_at=monitoring_start + 15.0,
    )

    name = attribution_events.scenario_name_for_timestamp(
        timestamp="",  # force the rel_time_s + monitoring_start fallback
        rel_time_s=10.0,
        scenario_traces=[trace],
        monitoring_start=monitoring_start,
    )
    assert name == "canary"


def test_scenario_name_for_timestamp_returns_empty_when_outside_window() -> None:
    monitoring_start = datetime.fromisoformat("2026-01-01T10:00:00.000").timestamp()
    trace = ScenarioTrace(
        name="canary",
        started_at=monitoring_start + 5.0,
        ended_at=monitoring_start + 15.0,
    )

    name = attribution_events.scenario_name_for_timestamp(
        timestamp="",
        rel_time_s=20.0,  # past the window
        scenario_traces=[trace],
        monitoring_start=monitoring_start,
    )
    assert name == ""


# ---------------------------------------------------------------------------
# _matches_extension_signature — path/operation + 1s rel_time tolerance
# ---------------------------------------------------------------------------


def test_matches_extension_signature_path_op_match_within_one_second() -> None:
    sigs = [("/workspace/x", "read", 5.0)]
    file_event = FileEvent(path="/workspace/x", operation="read", rel_time_s=5.5)

    assert attribution_events._matches_extension_signature(file_event, sigs) is True


def test_matches_extension_signature_path_or_op_mismatch_returns_false() -> None:
    sigs = [("/workspace/x", "read", 5.0)]
    file_event = FileEvent(path="/workspace/y", operation="read", rel_time_s=5.0)

    assert attribution_events._matches_extension_signature(file_event, sigs) is False


# ---------------------------------------------------------------------------
# _annotate_network_events / _annotate_file_events / _annotate_process_events
# Shape-level pins so the W12 facade rearrangement does not silently regress.
# ---------------------------------------------------------------------------


def test_annotate_network_events_classifies_target_attribution_with_scenario_label() -> (
    None
):
    activations = [
        ActivationEntry(
            extension_id="ext.target",
            timestamp="2026-01-01T10:00:00.000",
            activation_event="onCommand:tool.run",
        ),
    ]
    scenario = ScenarioTrace(
        name="canary",
        started_at=datetime.fromisoformat("2026-01-01T09:59:59.000").timestamp(),
        ended_at=datetime.fromisoformat("2026-01-01T10:00:01.000").timestamp(),
    )
    network_event = NetworkEvent(
        timestamp="2026-01-01T10:00:00.300",
        host="evil.example.com",
        summary="POST /steal",
    )

    annotated = attribution_events.annotate_network_events(
        [network_event],
        activations,
        [scenario],
        target_extension_id="ext.target",
    )

    assert len(annotated) == 1
    out = annotated[0]
    assert out.attribution_status == "target_attributed"
    assert out.related_extension_id == "ext.target"
    assert out.summary.endswith("[canary]")  # scenario label appended


def test_annotate_file_events_marks_inotify_as_automation_noise() -> None:
    inotify_event = FileEvent(
        timestamp="2026-01-01T10:00:00.500",
        observer="inotify",
        path="/workspace/.vscode/settings.json",
        operation="write",
        scenario_name="canary",
    )

    annotated = attribution_events.annotate_file_events(
        [inotify_event],
        activations=[],
        scenario_traces=[],
        target_extension_id="ext.target",
    )

    assert len(annotated) == 1
    out = annotated[0]
    assert out.attribution_status == "automation_noise"
    # Source rewrite per observer + scenario_name presence: inotify + scenario
    # → "automation".
    assert out.source == "automation"


def test_annotate_process_events_attributes_target_strace_event() -> None:
    activations = [
        ActivationEntry(
            extension_id="ext.target",
            timestamp="2026-01-01T10:00:00.000",
        ),
    ]
    process_event = ProcessEvent(
        timestamp="2026-01-01T10:00:00.200",
        pid=4242,
        operation="exec",
        command="/usr/bin/node",
    )

    annotated = attribution_events.annotate_process_events(
        [process_event],
        activations,
        scenario_traces=[],
        target_extension_id="ext.target",
    )

    assert len(annotated) == 1
    out = annotated[0]
    assert out.attribution_status == "target_attributed"
    assert out.is_target_extension_event is True
