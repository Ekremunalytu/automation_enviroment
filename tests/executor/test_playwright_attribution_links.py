"""Direct-module tests for ``executor.flows.playwright.attribution.links``.

[FOLLOWUP w12-precursor-tests-attribution-links] safety net before the W12
attribution facade cleanup (`§11.9` underscore re-export rework). Imports the
module by its real path (not via ``attribution.__init__`` re-exports) so the
public link-builder surface is pinned independently of the facade
rearrangement that W12-2 will perform.

Scope: pure helpers (`_temporal_confidence`, `_dedupe_evidence_links`,
`_nearest_activation`) plus the four ``_build_*_links`` builders and a smoke
test for the ``_build_evidence_bundle`` orchestrator. Each test feeds the
builder hand-crafted ``(event_id, event, epoch)`` tuples or dataclasses so the
behaviour can be pinned without spinning up an end-to-end activation report.
"""

from __future__ import annotations

from datetime import datetime

from executor.flows.playwright.attribution import links
from executor.flows.playwright.monitor.records import (
    EvidenceLink,
    LogStreamEntry,
    ScenarioTrace,
)
from executor.flows.playwright.monitor.types import ActivationReport
from executor.flows.playwright.runtime_capture.events import (
    ActivationEntry,
    FileEvent,
    NetworkEvent,
    OutputSignalEvent,
    ProcessEvent,
)


# ---------------------------------------------------------------------------
# _temporal_confidence — pure floor/ceiling formula
# ---------------------------------------------------------------------------


def test_temporal_confidence_zero_delta_returns_ceiling() -> None:
    # delta=0 → 0.7 - 0 = 0.7 (the formula's effective ceiling)
    assert links._temporal_confidence(0.0) == 0.7


def test_temporal_confidence_mid_delta_drops_linearly() -> None:
    # delta=2.0 → 0.7 - 0.2 = 0.5
    assert links._temporal_confidence(2.0) == 0.5


def test_temporal_confidence_clamps_oversized_delta_to_floor() -> None:
    # delta=10s clamps to 5s in the formula → 0.7 - 0.5 = 0.2 (floor)
    assert links._temporal_confidence(10.0) == 0.2


def test_temporal_confidence_floor_is_0_2() -> None:
    # Even delta=5 sits exactly on the floor (0.7 - 0.5 = 0.2).
    assert links._temporal_confidence(5.0) == 0.2


# ---------------------------------------------------------------------------
# _dedupe_evidence_links — 4-tuple key dedup, preserves first occurrence
# ---------------------------------------------------------------------------


def test_dedupe_evidence_links_empty_returns_empty() -> None:
    assert links._dedupe_evidence_links([]) == []


def test_dedupe_evidence_links_keeps_distinct_links() -> None:
    a = EvidenceLink("a", "b", "rel1", 0.5, "reason-a")
    b = EvidenceLink("a", "b", "rel2", 0.5, "reason-a")  # different link_type
    c = EvidenceLink("a", "b", "rel1", 0.5, "reason-b")  # different reason

    assert links._dedupe_evidence_links([a, b, c]) == [a, b, c]


def test_dedupe_evidence_links_collapses_full_4tuple_match() -> None:
    a = EvidenceLink("a", "b", "rel1", 0.5, "reason")
    duplicate = EvidenceLink("a", "b", "rel1", 0.9, "reason")  # confidence ignored

    deduped = links._dedupe_evidence_links([a, duplicate])

    # Confidence is NOT in the dedup key, so the second entry collapses into
    # the first; the surviving link must be the original (preserves order).
    assert deduped == [a]


# ---------------------------------------------------------------------------
# _nearest_activation — 5s window, drops None epochs, returns nearest by delta
# ---------------------------------------------------------------------------


def _activation(extension_id: str = "ext.target") -> ActivationEntry:
    return ActivationEntry(extension_id=extension_id)


def test_nearest_activation_empty_returns_none() -> None:
    assert links._nearest_activation([], event_epoch=1000.0) is None


def test_nearest_activation_skips_none_epochs() -> None:
    entries: list[tuple[str, ActivationEntry, float | None]] = [
        ("act-1", _activation(), None),
    ]
    assert links._nearest_activation(entries, event_epoch=1000.0) is None


def test_nearest_activation_drops_out_of_window_5s() -> None:
    entries: list[tuple[str, ActivationEntry, float | None]] = [
        ("act-1", _activation(), 1000.0),
    ]
    # Event 6 seconds away from the only activation → no match.
    assert links._nearest_activation(entries, event_epoch=1006.0) is None


def test_nearest_activation_returns_smallest_delta_when_multiple_in_window() -> None:
    entries: list[tuple[str, ActivationEntry, float | None]] = [
        ("act-far", _activation("ext.far"), 1000.0),
        ("act-near", _activation("ext.near"), 1004.0),
    ]
    match = links._nearest_activation(entries, event_epoch=1004.5)

    assert match is not None
    activation_event_id, _entry, delta = match
    assert activation_event_id == "act-near"
    assert delta == 0.5


# ---------------------------------------------------------------------------
# _build_scenario_links — event inside scenario window → "occurred_in_scenario"
# ---------------------------------------------------------------------------


def test_build_scenario_links_links_events_inside_window_with_full_confidence() -> None:
    trace = ScenarioTrace(name="canary", started_at=1000.0, ended_at=1010.0)
    activation_entries = [("act-1", _activation(), 1005.0)]

    built = links._build_scenario_links(
        scenario_entries=[("scenario-0001", trace)],
        activation_entries=activation_entries,
        network_entries=[],
        file_entries=[],
        process_entries=[],
        blocker_entries=[],
    )

    assert len(built) == 1
    link = built[0]
    assert link.from_event_id == "act-1"
    assert link.to_event_id == "scenario-0001"
    assert link.link_type == "occurred_in_scenario"
    assert link.confidence == 1.0
    assert "canary" in link.reason


def test_build_scenario_links_drops_events_outside_window() -> None:
    trace = ScenarioTrace(name="canary", started_at=1000.0, ended_at=1010.0)
    activation_entries = [("act-1", _activation(), 1020.0)]  # outside window

    built = links._build_scenario_links(
        scenario_entries=[("scenario-0001", trace)],
        activation_entries=activation_entries,
        network_entries=[],
        file_entries=[],
        process_entries=[],
        blocker_entries=[],
    )

    assert built == []


def test_build_scenario_links_skips_traces_with_invalid_window() -> None:
    # started_at=0 is the sentinel for "scenario never started" → no links.
    trace = ScenarioTrace(name="canary", started_at=0.0, ended_at=1010.0)
    activation_entries = [("act-1", _activation(), 1005.0)]

    built = links._build_scenario_links(
        scenario_entries=[("scenario-0001", trace)],
        activation_entries=activation_entries,
        network_entries=[],
        file_entries=[],
        process_entries=[],
        blocker_entries=[],
    )

    assert built == []


# ---------------------------------------------------------------------------
# _build_temporal_links — branch coverage for file/network/process events
# ---------------------------------------------------------------------------


def test_build_temporal_links_target_attributed_file_event_emits_caused_by_link() -> (
    None
):
    activation_entries = [("act-1", _activation("ext.target"), 1000.0)]
    file_event = FileEvent(
        path="/workspace/secret.txt",
        operation="read",
        is_target_extension_event=True,
        attribution_confidence=0.9,
    )

    built = links._build_temporal_links(
        activation_entries=activation_entries,
        network_entries=[],
        file_entries=[("file-1", file_event, 1000.5)],
        process_entries=[],
    )

    assert len(built) == 1
    assert built[0].link_type == "caused_by_target_extension"
    assert built[0].confidence == 0.9  # uses event's own confidence when present


def test_build_temporal_links_competing_file_event_emits_near_target_link() -> None:
    activation_entries = [("act-1", _activation(), 1000.0)]
    file_event = FileEvent(
        path="/workspace/x",
        operation="read",
        is_target_extension_event=False,
        attribution_status="competing_candidate",
    )

    built = links._build_temporal_links(
        activation_entries=activation_entries,
        network_entries=[],
        file_entries=[("file-1", file_event, 1000.5)],
        process_entries=[],
    )

    assert len(built) == 1
    assert built[0].link_type == "near_target_activation"
    # Confidence falls back to _temporal_confidence(0.5) = 0.65.
    assert built[0].confidence == 0.65


def test_build_temporal_links_target_attributed_network_event_emits_caused_by_link() -> (
    None
):
    activation_entries = [("act-1", _activation("ext.target"), 1000.0)]
    network_event = NetworkEvent(
        host="evil.example.com",
        is_target_extension_event=True,
        attribution_confidence=0.78,
    )

    built = links._build_temporal_links(
        activation_entries=activation_entries,
        network_entries=[("net-1", network_event, 1000.3)],
        file_entries=[],
        process_entries=[],
    )

    assert len(built) == 1
    assert built[0].link_type == "caused_by_target_extension"


def test_build_temporal_links_target_attributed_process_event_emits_caused_by_link() -> (
    None
):
    activation_entries = [("act-1", _activation("ext.target"), 1000.0)]
    process_event = ProcessEvent(
        pid=4242,
        operation="exec",
        is_target_extension_event=True,
        attribution_confidence=0.84,
    )

    built = links._build_temporal_links(
        activation_entries=activation_entries,
        network_entries=[],
        file_entries=[],
        process_entries=[("proc-1", process_event, 1000.4)],
    )

    assert len(built) == 1
    assert built[0].link_type == "caused_by_target_extension"


def test_build_temporal_links_drops_events_with_no_nearby_activation() -> None:
    # Activation is 6 seconds away → outside the 5s window → no link.
    activation_entries = [("act-1", _activation(), 1000.0)]
    file_event = FileEvent(
        path="/workspace/y",
        operation="write",
        is_target_extension_event=True,
    )

    built = links._build_temporal_links(
        activation_entries=activation_entries,
        network_entries=[],
        file_entries=[("file-1", file_event, 1006.0)],
        process_entries=[],
    )

    assert built == []


# ---------------------------------------------------------------------------
# _build_duplicate_file_links — strace+inotify pairing within 1s
# ---------------------------------------------------------------------------


def test_build_duplicate_file_links_pairs_strace_and_inotify_within_one_second() -> (
    None
):
    strace_event = FileEvent(
        path="/workspace/secret.txt", operation="read", observer="strace"
    )
    inotify_event = FileEvent(
        path="/workspace/secret.txt", operation="read", observer="inotify"
    )

    built = links._build_duplicate_file_links(
        [
            ("file-strace", strace_event, 1000.0),
            ("file-inotify", inotify_event, 1000.7),
        ]
    )

    assert len(built) == 1
    link = built[0]
    assert link.link_type == "duplicate_signal"
    assert link.confidence == 0.9
    assert {link.from_event_id, link.to_event_id} == {"file-strace", "file-inotify"}


def test_build_duplicate_file_links_skips_pairs_more_than_one_second_apart() -> None:
    strace_event = FileEvent(
        path="/workspace/secret.txt", operation="read", observer="strace"
    )
    inotify_event = FileEvent(
        path="/workspace/secret.txt", operation="read", observer="inotify"
    )

    built = links._build_duplicate_file_links(
        [
            ("file-strace", strace_event, 1000.0),
            ("file-inotify", inotify_event, 1002.0),  # >1s apart
        ]
    )

    assert built == []


def test_build_duplicate_file_links_requires_strace_inotify_observer_pair() -> None:
    # Two strace observers should never pair as a duplicate.
    a = FileEvent(path="/workspace/x", operation="read", observer="strace")
    b = FileEvent(path="/workspace/x", operation="read", observer="strace")

    built = links._build_duplicate_file_links(
        [("file-a", a, 1000.0), ("file-b", b, 1000.5)]
    )

    assert built == []


# ---------------------------------------------------------------------------
# _build_noise_links — automation_noise + blocked_by_ui scenario links
# ---------------------------------------------------------------------------


def test_build_noise_links_emits_automation_noise_for_inotify_workspace_writes() -> (
    None
):
    trace = ScenarioTrace(name="canary", started_at=1000.0, ended_at=1010.0)
    file_event = FileEvent(
        path="/workspace/.vscode/settings.json",
        operation="write",
        observer="inotify",
        scenario_name="canary",
        attribution_status="automation_noise",
    )

    built = links._build_noise_links(
        scenario_entries=[("scenario-0001", trace)],
        file_entries=[("file-1", file_event, 1003.0)],
        blocker_entries=[],
    )

    assert len(built) == 1
    assert built[0].link_type == "automation_noise"
    assert built[0].to_event_id == "scenario-0001"


def test_build_noise_links_emits_blocked_by_ui_for_blocker_entries() -> None:
    trace = ScenarioTrace(name="canary", started_at=1000.0, ended_at=1010.0)
    blocker = LogStreamEntry(
        stream="ui_blockers",
        scenario_name="canary",
        message="A modal blocked the canary scenario.",
        status="blocked",
    )

    built = links._build_noise_links(
        scenario_entries=[("scenario-0001", trace)],
        file_entries=[],
        blocker_entries=[("blocker-1", blocker, 1004.0)],
    )

    assert len(built) == 1
    assert built[0].link_type == "blocked_by_ui"


# ---------------------------------------------------------------------------
# _build_evidence_bundle — orchestrator smoke test
# ---------------------------------------------------------------------------


def test_build_evidence_bundle_empty_report_returns_empty_events_and_links() -> None:
    report = ActivationReport(target_extension_id="ext.target", monitoring_start=0.0)

    events, link_list = links.build_evidence_bundle(report)

    assert events == []
    assert link_list == []


def test_build_evidence_bundle_round_trips_activation_with_scenario_link() -> None:
    """End-to-end smoke: an activation falling inside a scenario window must
    surface as both an evidence event and an ``occurred_in_scenario`` link.

    Pinning here is intentionally narrow — the goal is to keep the orchestrator's
    integration with `_build_scenario_links` honest across the W12 split. Per-
    branch detail is covered by the dedicated builder tests above.
    """
    # Use a real ISO timestamp + matching epochs so the orchestrator's
    # `_resolve_event_epoch` returns the same epoch space that the scenario
    # window lives in (sembolik 1000.0 vs real 2026 epoch would mismatch).
    activation_ts = "2026-01-01T10:00:05.000"
    activation_epoch = datetime.fromisoformat(activation_ts).timestamp()
    monitoring_start = activation_epoch - 5.0
    scenario = ScenarioTrace(
        name="canary",
        started_at=activation_epoch - 2.0,
        ended_at=activation_epoch + 2.0,
        status="completed",
    )
    activation = ActivationEntry(
        extension_id="ext.target",
        timestamp=activation_ts,
        source="log",
    )
    report = ActivationReport(
        target_extension_id="ext.target",
        monitoring_start=monitoring_start,
        scenario_traces=[scenario],
        activated=[activation],
    )

    events, link_list = links.build_evidence_bundle(report)

    kinds = {event.kind for event in events}
    assert "scenario" in kinds
    assert "activation" in kinds

    # Exactly one occurred_in_scenario link is expected from the activation
    # falling inside the canary scenario window.
    occurred_in_scenario = [
        link for link in link_list if link.link_type == "occurred_in_scenario"
    ]
    assert len(occurred_in_scenario) == 1
    assert occurred_in_scenario[0].confidence == 1.0


# ---------------------------------------------------------------------------
# W17-1 attribution-count-parity — kind="activation" evidence events must
# stamp ``is_target_extension_event`` whenever the activation matches
# ``report.target_extension_id``. Before W17-1, ``build_evidence_bundle``
# never set the flag for activation events, so evidence-side counters
# (e.g. ``kind=activation,is_target_extension_event=True``) read zero
# even when ``count_target_activations(report.activated, ...)`` matched.
# W14 production scan ``2026-05-14`` surfaced the drift; W16-3 split the
# parity half out as ``[FOLLOWUP attribution-count-parity]``; W17-1 closes
# it at the producer emit-site.
# ---------------------------------------------------------------------------


def test_build_evidence_bundle_activation_event_flags_target_extension() -> None:
    """A ``kind="activation"`` event for the target extension is flagged."""
    activation = ActivationEntry(
        extension_id="ms-python.python",
        timestamp="2026-05-14T10:00:00.000",
        source="log",
        activation_event="workspaceContains:requirements.txt",
    )
    report = ActivationReport(
        target_extension_id="ms-python.python",
        monitoring_start=1700_000_000.0,
        activated=[activation],
    )

    events, _ = links.build_evidence_bundle(report)

    activation_events = [event for event in events if event.kind == "activation"]
    assert len(activation_events) == 1
    assert activation_events[0].is_target_extension_event is True


def test_build_evidence_bundle_activation_event_does_not_flag_non_target() -> None:
    """A ``kind="activation"`` event for a non-target extension stays unflagged."""
    activation = ActivationEntry(
        extension_id="other.extension",
        timestamp="2026-05-14T10:00:00.000",
        source="log",
    )
    report = ActivationReport(
        target_extension_id="ms-python.python",
        monitoring_start=1700_000_000.0,
        activated=[activation],
    )

    events, _ = links.build_evidence_bundle(report)

    activation_events = [event for event in events if event.kind == "activation"]
    assert len(activation_events) == 1
    assert activation_events[0].is_target_extension_event is False


def test_build_evidence_bundle_activation_event_unflagged_when_no_target_set() -> None:
    """Empty ``target_extension_id`` keeps the flag False (mirrors count_target_activations guard)."""
    activation = ActivationEntry(
        extension_id="ms-python.python",
        timestamp="2026-05-14T10:00:00.000",
        source="log",
    )
    report = ActivationReport(
        target_extension_id="",
        monitoring_start=1700_000_000.0,
        activated=[activation],
    )

    events, _ = links.build_evidence_bundle(report)

    activation_events = [event for event in events if event.kind == "activation"]
    assert len(activation_events) == 1
    assert activation_events[0].is_target_extension_event is False


def test_build_evidence_bundle_target_activation_parity_invariant() -> None:
    """W17-1 parity invariant: count of target-flagged ``kind="activation"``
    evidence events equals ``count_target_activations(report.activated, target_id)``.

    This is the W17-1 contract pin closing
    ``[FOLLOWUP attribution-count-parity]`` (W14 production scan
    ``2026-05-14`` divergence: ``attribution_summary.target_activation_count = 1``
    while ``kind=activation,is_target_extension_event=True`` count was 0).
    Both counters now derive from the same predicate
    (``entry.extension_id == report.target_extension_id``).
    """
    from executor.flows.playwright.health.summary import count_target_activations

    target_id = "ms-python.python"
    activated = [
        ActivationEntry(
            extension_id=target_id,
            timestamp="2026-05-14T10:00:01.000",
            source="log",
            activation_event="workspaceContains:requirements.txt",
        ),
        ActivationEntry(
            extension_id="other.extension",
            timestamp="2026-05-14T10:00:02.000",
            source="log",
        ),
        ActivationEntry(
            extension_id=target_id,
            timestamp="2026-05-14T10:00:03.000",
            source="log",
            activation_event="onStartupFinished",
        ),
    ]
    report = ActivationReport(
        target_extension_id=target_id,
        monitoring_start=1700_000_000.0,
        activated=activated,
    )

    events, _ = links.build_evidence_bundle(report)
    target_flagged_evidence = [
        event
        for event in events
        if event.kind == "activation" and event.is_target_extension_event
    ]

    summary_target_count = count_target_activations(activated, target_id)
    evidence_target_count = len(target_flagged_evidence)

    assert summary_target_count == 2
    assert evidence_target_count == summary_target_count, (
        "W17-1 parity invariant violated: "
        f"attribution_summary.target_activation_count={summary_target_count} "
        f"but kind=activation,is_target_extension_event=True count="
        f"{evidence_target_count}. Both counters must derive from the same "
        "predicate (entry.extension_id == report.target_extension_id) so "
        "downstream rule helpers in packages/analysis_engine/rules/_common.py "
        "(``is_target_owned`` / ``target_file_events``) see the same truth."
    )


# ---------------------------------------------------------------------------
# W22-3 attribution-count-parity-process-events — mirrors W17-1 paterni
# for ``kind="process"`` evidence events. The four tests below pin the
# producer-side stamp at
# ``executor/flows/playwright/attribution/links.py`` against
# ``count_target_process_events(...)`` in ``health/summary.py`` so the
# evidence-side counter cannot silently diverge from the summary-side
# counter (W14 production scan divergence shape applied to process events).
# ---------------------------------------------------------------------------


def test_build_evidence_bundle_process_event_flags_target_extension() -> None:
    """A ``kind="process"`` event whose ``related_extension_id`` matches the
    report's ``target_extension_id`` is flagged ``is_target_extension_event=True``.
    """
    process_event = ProcessEvent(
        timestamp="2026-05-14T10:00:00.000",
        pid=1234,
        related_extension_id="ms-python.python",
        operation="execve",
        command="python3",
    )
    report = ActivationReport(
        target_extension_id="ms-python.python",
        monitoring_start=1700_000_000.0,
        process_events=[process_event],
    )

    events, _ = links.build_evidence_bundle(report)

    process_events = [event for event in events if event.kind == "process"]
    assert len(process_events) == 1
    assert process_events[0].is_target_extension_event is True
    assert process_events[0].actor == "extension"


def test_build_evidence_bundle_process_event_does_not_flag_non_target() -> None:
    """A ``kind="process"`` event for a non-target extension stays unflagged."""
    process_event = ProcessEvent(
        timestamp="2026-05-14T10:00:00.000",
        pid=1234,
        related_extension_id="other.extension",
        operation="execve",
    )
    report = ActivationReport(
        target_extension_id="ms-python.python",
        monitoring_start=1700_000_000.0,
        process_events=[process_event],
    )

    events, _ = links.build_evidence_bundle(report)

    process_events = [event for event in events if event.kind == "process"]
    assert len(process_events) == 1
    assert process_events[0].is_target_extension_event is False
    assert process_events[0].actor == "unknown"


def test_build_evidence_bundle_process_event_unflagged_when_no_target_set() -> None:
    """Empty ``target_extension_id`` keeps the flag False (mirrors
    ``count_target_process_events`` guard).
    """
    process_event = ProcessEvent(
        timestamp="2026-05-14T10:00:00.000",
        pid=1234,
        related_extension_id="ms-python.python",
        operation="execve",
    )
    report = ActivationReport(
        target_extension_id="",
        monitoring_start=1700_000_000.0,
        process_events=[process_event],
    )

    events, _ = links.build_evidence_bundle(report)

    process_events = [event for event in events if event.kind == "process"]
    assert len(process_events) == 1
    assert process_events[0].is_target_extension_event is False


def test_build_evidence_bundle_target_process_parity_invariant() -> None:
    """W22-3 parity invariant: count of target-flagged ``kind="process"``
    evidence events equals
    ``count_target_process_events(report.process_events, target_id)``.

    Mirrors W17-1 parity invariant for ``kind="activation"`` events
    (commit ``8c26d02`` + self-stamp ``0a8f59e``). Both counters derive
    from the same predicate (``entry.related_extension_id ==
    report.target_extension_id``) so downstream rule helpers see the
    same truth.
    """
    from executor.flows.playwright.health.summary import (
        count_target_process_events,
    )

    target_id = "ms-python.python"
    process_events = [
        ProcessEvent(
            timestamp="2026-05-14T10:00:01.000",
            pid=1234,
            related_extension_id=target_id,
            operation="execve",
        ),
        ProcessEvent(
            timestamp="2026-05-14T10:00:02.000",
            pid=1235,
            related_extension_id="other.extension",
            operation="execve",
        ),
        ProcessEvent(
            timestamp="2026-05-14T10:00:03.000",
            pid=1236,
            related_extension_id=target_id,
            operation="openat",
        ),
    ]
    report = ActivationReport(
        target_extension_id=target_id,
        monitoring_start=1700_000_000.0,
        process_events=process_events,
    )

    events, _ = links.build_evidence_bundle(report)
    target_flagged_evidence = [
        event
        for event in events
        if event.kind == "process" and event.is_target_extension_event
    ]

    summary_target_count = count_target_process_events(process_events, target_id)
    evidence_target_count = len(target_flagged_evidence)

    assert summary_target_count == 2
    assert evidence_target_count == summary_target_count, (
        "W22-3 parity invariant violated (process events): "
        f"count_target_process_events={summary_target_count} "
        f"but kind=process,is_target_extension_event=True count="
        f"{evidence_target_count}. Both counters must derive from the same "
        "predicate (entry.related_extension_id == "
        "report.target_extension_id)."
    )


# ---------------------------------------------------------------------------
# W22-3 attribution-count-parity-output-channel — mirrors W17-1 paterni
# for ``kind="output_channel_appendline"`` evidence events captured by the
# harness extension's createOutputChannel proxy (ADR 0006 §3-§4). Same
# parity contract: producer-side stamp at
# ``executor/flows/playwright/attribution/links.py`` and
# ``count_target_output_events(...)`` in ``health/summary.py`` derive from
# the same predicate (``entry.extension_id == target_extension_id``).
# ---------------------------------------------------------------------------


def test_build_evidence_bundle_output_event_flags_target_extension() -> None:
    """A ``kind="output_channel_appendline"`` event whose ``extension_id``
    matches the report's ``target_extension_id`` is flagged
    ``is_target_extension_event=True``.
    """
    output_event = OutputSignalEvent(
        timestamp="2026-05-14T10:00:00.000",
        channel="Python",
        text="Activating extension ms-python.python",
        extension_id="ms-python.python",
    )
    report = ActivationReport(
        target_extension_id="ms-python.python",
        monitoring_start=1700_000_000.0,
        output_signal_events=[output_event],
    )

    events, _ = links.build_evidence_bundle(report)

    output_events = [
        event for event in events if event.kind == "output_channel_appendline"
    ]
    assert len(output_events) == 1
    assert output_events[0].is_target_extension_event is True


def test_build_evidence_bundle_output_event_does_not_flag_non_target() -> None:
    """A ``kind="output_channel_appendline"`` event for a non-target
    extension stays unflagged.
    """
    output_event = OutputSignalEvent(
        timestamp="2026-05-14T10:00:00.000",
        channel="Other",
        text="some unrelated output",
        extension_id="other.extension",
    )
    report = ActivationReport(
        target_extension_id="ms-python.python",
        monitoring_start=1700_000_000.0,
        output_signal_events=[output_event],
    )

    events, _ = links.build_evidence_bundle(report)

    output_events = [
        event for event in events if event.kind == "output_channel_appendline"
    ]
    assert len(output_events) == 1
    assert output_events[0].is_target_extension_event is False


def test_build_evidence_bundle_output_event_unflagged_when_no_target_set() -> None:
    """Empty ``target_extension_id`` keeps the flag False (mirrors
    ``count_target_output_events`` guard).
    """
    output_event = OutputSignalEvent(
        timestamp="2026-05-14T10:00:00.000",
        channel="Python",
        text="any text",
        extension_id="ms-python.python",
    )
    report = ActivationReport(
        target_extension_id="",
        monitoring_start=1700_000_000.0,
        output_signal_events=[output_event],
    )

    events, _ = links.build_evidence_bundle(report)

    output_events = [
        event for event in events if event.kind == "output_channel_appendline"
    ]
    assert len(output_events) == 1
    assert output_events[0].is_target_extension_event is False


def test_build_evidence_bundle_target_output_parity_invariant() -> None:
    """W22-3 parity invariant: count of target-flagged
    ``kind="output_channel_appendline"`` evidence events equals
    ``count_target_output_events(report.output_signal_events, target_id)``.

    Mirrors W17-1 parity invariant for ``kind="activation"`` events
    (commit ``8c26d02`` + self-stamp ``0a8f59e``). Both counters derive
    from the same predicate (``entry.extension_id ==
    report.target_extension_id``) so downstream rule helpers see the
    same truth for Output channel writes captured via ADR 0006 §3-§4
    harness extension proxy.
    """
    from executor.flows.playwright.health.summary import (
        count_target_output_events,
    )

    target_id = "ms-python.python"
    output_events = [
        OutputSignalEvent(
            timestamp="2026-05-14T10:00:01.000",
            channel="Python",
            text="activating",
            extension_id=target_id,
        ),
        OutputSignalEvent(
            timestamp="2026-05-14T10:00:02.000",
            channel="Other",
            text="unrelated",
            extension_id="other.extension",
        ),
        OutputSignalEvent(
            timestamp="2026-05-14T10:00:03.000",
            channel="Python",
            text="interpreter selected",
            extension_id=target_id,
        ),
    ]
    report = ActivationReport(
        target_extension_id=target_id,
        monitoring_start=1700_000_000.0,
        output_signal_events=output_events,
    )

    events, _ = links.build_evidence_bundle(report)
    target_flagged_evidence = [
        event
        for event in events
        if event.kind == "output_channel_appendline" and event.is_target_extension_event
    ]

    summary_target_count = count_target_output_events(output_events, target_id)
    evidence_target_count = len(target_flagged_evidence)

    assert summary_target_count == 2
    assert evidence_target_count == summary_target_count, (
        "W22-3 parity invariant violated (output channel events): "
        f"count_target_output_events={summary_target_count} "
        f"but kind=output_channel_appendline,is_target_extension_event=True "
        f"count={evidence_target_count}. Both counters must derive from "
        "the same predicate (entry.extension_id == "
        "report.target_extension_id)."
    )
