"""W12-3 — typed `EvidenceEvent.raw_context` discriminated union.

The contract field used to be ``dict[str, Any]``; W12-3 hoists the producer-
side fixed-shape dicts into a discriminated union keyed by ``event_class``.
These cases pin the discriminator dispatch, the ``extra='forbid'`` boundary
on each variant, and one full ``EvidenceEvent`` round-trip so callers can
rely on attribute access (``event.raw_context.event_class``) instead of
``dict.get``.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.analysis_contracts import EvidenceEvent
from packages.analysis_contracts.evidence import (
    ActivationRawContext,
    FileRawContext,
    NetworkRawContext,
    OutputChannelRawContext,
    ProcessRawContext,
    ScenarioRawContext,
    UiBlockerRawContext,
)


def _evidence_payload(raw_context: dict[str, object]) -> dict[str, object]:
    return {
        "event_id": "evt-0001",
        "kind": "network",
        "raw_context": raw_context,
    }


def test_network_variant_validates_known_payload() -> None:
    event = EvidenceEvent.model_validate(
        _evidence_payload(
            {
                "event_class": "network",
                "event_type": "http_request",
                "http_method": "POST",
                "http_status_code": 200,
            }
        )
    )
    assert isinstance(event.raw_context, NetworkRawContext)
    assert event.raw_context.event_type == "http_request"
    assert event.raw_context.http_method == "POST"
    assert event.raw_context.http_status_code == 200


def test_network_variant_rejects_unknown_key() -> None:
    # `host` lives on `EvidenceEvent`, not on NetworkRawContext — extra='forbid'
    # rejects it inside raw_context to keep variant surfaces tight.
    with pytest.raises(ValidationError):
        EvidenceEvent.model_validate(
            _evidence_payload({"event_class": "network", "host": "evil.invalid"})
        )


def test_file_variant_rejects_network_only_keys() -> None:
    # The discriminator picks FileRawContext, but `http_method` is not in its
    # field set — extra='forbid' must reject it.
    with pytest.raises(ValidationError):
        EvidenceEvent.model_validate(
            _evidence_payload(
                {
                    "event_class": "file",
                    "secondary_path": "/workspace/x",
                    "http_method": "POST",
                }
            )
        )


def test_process_variant_requires_pid() -> None:
    with pytest.raises(ValidationError):
        EvidenceEvent.model_validate(_evidence_payload({"event_class": "process"}))
    event = EvidenceEvent.model_validate(
        _evidence_payload({"event_class": "process", "pid": 4321})
    )
    assert isinstance(event.raw_context, ProcessRawContext)
    assert event.raw_context.pid == 4321


def test_scenario_variant_round_trip() -> None:
    event = EvidenceEvent.model_validate(
        _evidence_payload(
            {
                "event_class": "scenario",
                "status": "completed",
                "started_at": 1.0,
                "ended_at": 2.5,
            }
        )
    )
    assert isinstance(event.raw_context, ScenarioRawContext)
    assert event.raw_context.event_class == "scenario"
    assert event.raw_context.status == "completed"


def test_discriminator_dispatches_by_event_class() -> None:
    cases: list[tuple[str, type, dict[str, object]]] = [
        ("network", NetworkRawContext, {}),
        ("file", FileRawContext, {}),
        ("process", ProcessRawContext, {"pid": 1}),
        ("scenario", ScenarioRawContext, {}),
        ("activation", ActivationRawContext, {}),
        ("ui_blocker", UiBlockerRawContext, {}),
        ("output_channel_appendline", OutputChannelRawContext, {}),
    ]
    for event_class, expected_cls, extra in cases:
        payload = {"event_class": event_class, **extra}
        event = EvidenceEvent.model_validate(_evidence_payload(payload))
        assert isinstance(event.raw_context, expected_cls), (
            f"{event_class!r} should dispatch to {expected_cls.__name__}, "
            f"got {type(event.raw_context).__name__}"
        )


def test_unknown_event_class_rejected() -> None:
    with pytest.raises(ValidationError):
        EvidenceEvent.model_validate(_evidence_payload({"event_class": "bogus"}))


def test_evidence_event_round_trip_with_typed_raw_context() -> None:
    event = EvidenceEvent.model_validate(
        {
            "event_id": "file-0001",
            "kind": "file",
            "raw_context": {
                "event_class": "file",
                "secondary_path": "/workspace/secrets.env",
                "flags": "rw",
                "observer": "fanotify",
                "source": "harness",
            },
        }
    )
    assert event.kind == "file"
    assert isinstance(event.raw_context, FileRawContext)
    assert event.raw_context.secondary_path == "/workspace/secrets.env"
    # Round-trip through model_dump preserves the discriminator.
    dumped = event.model_dump()
    assert dumped["raw_context"]["event_class"] == "file"
    assert dumped["raw_context"]["secondary_path"] == "/workspace/secrets.env"
