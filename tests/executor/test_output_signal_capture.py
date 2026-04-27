"""PR345 PR5 + ADR 0006: target Output channel capture coverage.

Covers the Python-side parser (``parse_output_signal_events``), the
attribution helper (``annotate_output_signal_events``), the EvidenceEvent
routing (``_build_evidence_bundle``), and the tightened
``ActivationReport.target_extension_observed`` predicate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PLAYWRIGHT_DIR = (
    Path(__file__).resolve().parents[2] / "executor" / "flows" / "playwright"
)
if str(PLAYWRIGHT_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_DIR))

import monitor  # noqa: E402
from output_signals import (  # noqa: E402
    ATTRIBUTION_WINDOW_S,
    annotate_output_signal_events,
    parse_output_signal_events,
)


def _harness_marker_line(payload: dict) -> str:
    return f"[extrace-harness] {json.dumps(payload)}"


def test_harness_output_channel_hook_emits_marker_per_appendline() -> None:
    """JS-emitted markers parse into one OutputSignalEvent per appendLine."""
    output = "\n".join(
        [
            _harness_marker_line(
                {
                    "kind": "output_channel_appendline",
                    "channel": "Pylance",
                    "text": "indexed 1234 symbols",
                    "ts": 1_700_000_001_000,
                    "collector": "harness_extension",
                }
            ),
            "[2026-04-26 09:00:01.500] some other exthost line",
            _harness_marker_line(
                {
                    "kind": "output_channel_appendline",
                    "channel": "ExtraceTarget",
                    "text": "boot complete",
                    "ts": 1_700_000_002_000,
                    "collector": "harness_extension",
                }
            ),
        ]
    )

    events = parse_output_signal_events(output)
    assert len(events) == 2
    assert [evt.channel for evt in events] == ["Pylance", "ExtraceTarget"]
    assert events[0].text == "indexed 1234 symbols"
    assert events[1].text == "boot complete"
    # Lines without a harness marker are ignored; lines with a different
    # harness kind (stimulus phase markers from PR2) must also be skipped.
    extra = parse_output_signal_events(
        _harness_marker_line({"kind": "stimulus", "phase": "start"})
    )
    assert extra == []


def test_harness_output_channel_event_attribution_filters_to_target() -> None:
    """Events near a target activation are marked target-owned; others are not."""
    output = "\n".join(
        [
            _harness_marker_line(
                {
                    "kind": "output_channel_appendline",
                    "channel": "ExtraceTarget",
                    "text": "near target",
                    # 2 seconds after target activation epoch.
                    "ts": 1_700_000_002_000,
                    "collector": "harness_extension",
                }
            ),
            _harness_marker_line(
                {
                    "kind": "output_channel_appendline",
                    "channel": "Pylance",
                    "text": "far from target",
                    # 3600 seconds after target activation; outside the window.
                    "ts": 1_700_003_600_000,
                    "collector": "harness_extension",
                }
            ),
        ]
    )
    events = parse_output_signal_events(output, monitoring_start=1_700_000_000.0)

    # Build target activation timestamp from the SAME epoch -> naive
    # local-ISO formatter the parser uses, so the attribution helper sees
    # both event and activation in the same TZ interpretation.
    from datetime import datetime as _dt

    activation_ts = _dt.fromtimestamp(1_700_000_000.0).isoformat(
        timespec="milliseconds"
    )
    target_activation = monitor.ActivationEntry(
        extension_id="acme.target",
        activation_event="onStartupFinished",
        timestamp=activation_ts,
        source="log",
    )
    other_activation = monitor.ActivationEntry(
        extension_id="ms-python.python",
        activation_event="onStartupFinished",
        timestamp=activation_ts,
        source="log",
    )

    annotate_output_signal_events(
        events,
        activations=[target_activation, other_activation],
        target_extension_id="acme.target",
        monitoring_start=1_700_000_000.0,
    )

    near = events[0]
    far = events[1]
    assert near.is_target_extension_event is True
    assert near.attribution_status == "near_target_activation"
    assert near.extension_id == "acme.target"
    assert near.activation_event == "onStartupFinished"
    assert near.attribution_basis.startswith("within ")
    assert far.is_target_extension_event is False
    assert far.attribution_status == "unattributed"
    assert far.extension_id == ""


def test_target_extension_observed_includes_output_signal_events() -> None:
    """An activation entry alone keeps the legacy True; an output signal alone now also flips."""
    # Case 1: legacy path stays — activation present, no output events.
    legacy = monitor.ActivationReport(
        target_extension_id="acme.target",
        activated=[monitor.ActivationEntry(extension_id="acme.target")],
    )
    assert legacy.target_extension_observed is True

    # Case 2: no activation, no file/network — but a target-owned output signal flips it.
    only_output = monitor.ActivationReport(
        target_extension_id="acme.target",
        output_signal_events=[
            monitor.OutputSignalEvent(
                channel="ExtraceTarget",
                text="hello",
                extension_id="acme.target",
                is_target_extension_event=True,
                attribution_status="near_target_activation",
            )
        ],
    )
    assert only_output.target_extension_observed is True
    assert len(only_output.target_output_signal_events) == 1

    # Case 3: target_id missing → False regardless.
    no_target = monitor.ActivationReport(
        target_extension_id="",
        output_signal_events=[
            monitor.OutputSignalEvent(
                channel="ExtraceTarget",
                text="hello",
                is_target_extension_event=True,
            )
        ],
    )
    assert no_target.target_extension_observed is False


def test_evidence_bundle_routes_output_signal_events_with_harness_collector() -> None:
    """_build_evidence_bundle emits EvidenceEvent kind=output_channel_appendline."""
    report = monitor.ActivationReport(
        target_extension_id="acme.target",
        monitoring_start=100.0,
        activated=[
            monitor.ActivationEntry(
                extension_id="acme.target",
                activation_event="onStartupFinished",
                timestamp="2026-01-01 10:00:00.500",
                source="log",
            )
        ],
        output_signal_events=[
            monitor.OutputSignalEvent(
                timestamp="2026-01-01T10:00:01.000",
                rel_time_s=1.0,
                channel="ExtraceTarget",
                text="boot complete",
                extension_id="acme.target",
                activation_event="onStartupFinished",
                is_target_extension_event=True,
                attribution_status="near_target_activation",
                attribution_basis="within 0.500s of target activation",
            )
        ],
    )

    evidence_events = report.evidence_events
    output_events = [
        evt for evt in evidence_events if evt.kind == "output_channel_appendline"
    ]
    assert len(output_events) == 1
    evidence = output_events[0]
    assert evidence.collector == "harness_extension"
    assert evidence.actor == "harness"
    assert evidence.is_target_extension_event is True
    assert evidence.attribution_status == "near_target_activation"
    assert evidence.raw_context["channel"] == "ExtraceTarget"
    assert evidence.raw_context["text"] == "boot complete"


def test_harness_lifecycle_diagnostic_appendline_parses_as_output_signal() -> None:
    # W8-0: harness extension activate() phases (enter/exit + marker write)
    # are written as appendLine on a dedicated "ExTrace Harness" output
    # channel. The existing PR345 PR5 hook captures every appendLine; the
    # Python parser converts it into an OutputSignalEvent whose `text`
    # carries the JSON-stringified diagnostic payload.
    diag_payload = {
        "phase": "activate_enter",
        "pid": 4321,
        "ts": 1_700_000_001_000,
    }
    output = _harness_marker_line(
        {
            "kind": "output_channel_appendline",
            "channel": "ExTrace Harness",
            "text": json.dumps(diag_payload),
            "ts": 1_700_000_001_000,
            "collector": "harness_extension",
        }
    )

    events = parse_output_signal_events(output)
    assert len(events) == 1
    assert events[0].channel == "ExTrace Harness"
    parsed = json.loads(events[0].text)
    assert parsed["phase"] == "activate_enter"
    assert parsed["pid"] == 4321


def test_attribution_window_picks_nearest_activation() -> None:
    """When multiple target activations are present, attribution picks nearest by abs delta."""
    output = "\n".join(
        [
            _harness_marker_line(
                {
                    "kind": "output_channel_appendline",
                    "channel": "ExtraceTarget",
                    "text": "between two activations",
                    "ts": 1_700_000_005_000,
                    "collector": "harness_extension",
                }
            ),
        ]
    )
    events = parse_output_signal_events(output, monitoring_start=1_700_000_000.0)

    from datetime import datetime as _dt

    earlier_ts = _dt.fromtimestamp(1_700_000_004.0).isoformat(
        timespec="milliseconds"
    )  # 1s before event (event at +5)
    later_ts = _dt.fromtimestamp(1_700_000_008.0).isoformat(
        timespec="milliseconds"
    )  # 3s after event
    earlier = monitor.ActivationEntry(
        extension_id="acme.target",
        activation_event="onStartupFinished",
        timestamp=earlier_ts,
        source="log",
    )
    later = monitor.ActivationEntry(
        extension_id="acme.target",
        activation_event="onCommand:run",
        timestamp=later_ts,
        source="log",
    )

    annotate_output_signal_events(
        events,
        activations=[earlier, later],
        target_extension_id="acme.target",
        monitoring_start=1_700_000_000.0,
    )

    # The earlier activation is closer (1s vs 3s) so its activation_event wins.
    assert events[0].is_target_extension_event is True
    assert events[0].activation_event == "onStartupFinished"
    # Verify the window guard: window is ATTRIBUTION_WINDOW_S; both activations fit.
    assert ATTRIBUTION_WINDOW_S >= 3.0
