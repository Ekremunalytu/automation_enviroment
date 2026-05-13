"""W12-3 — typed `EvidenceEvent.raw_context` discriminated union.

The contract field used to be ``dict[str, Any]``; W12-3 hoists the producer-
side fixed-shape dicts into a discriminated union keyed by ``event_class``.
These cases pin the discriminator dispatch, the ``extra='forbid'`` boundary
on each variant, and one full ``EvidenceEvent`` round-trip so callers can
rely on attribute access (``event.raw_context.event_class``) instead of
``dict.get``.

W14-4 [FOLLOWUP evidence-event-kind-raw-context-invariant]: the
``EvidenceEvent.kind`` field must belong to the closed allowlist
``packages.analysis_contracts.contracts._EVIDENCE_EVENT_KIND_TO_EVENT_CLASS``
and its mapping target must match ``raw_context.event_class``. Before
W14-4 the two fields could drift silently (e.g. ``kind="network"`` +
``event_class="file"``) and downstream rule helpers in
``packages/analysis_engine/rules/_common.py`` masked the mismatch via
getattr defaults, producing false-negative detections. The 9-kind
closed allowlist (7 strict 1:1 + 2 alias kinds ``extension_host``
→ ``activation`` and ``log`` → ``scenario``) is pinned exhaustively:
one positive case per kind, every (kind, wrong-event_class) pair as a
negative case, plus an unrecognized-kind reject and a default-
raw_context fallback case.
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


_KIND_TO_VARIANT: tuple[tuple[str, type, dict[str, object]], ...] = (
    ("scenario", ScenarioRawContext, {}),
    ("activation", ActivationRawContext, {}),
    ("network", NetworkRawContext, {}),
    ("file", FileRawContext, {}),
    ("process", ProcessRawContext, {"pid": 1}),
    ("ui_blocker", UiBlockerRawContext, {}),
    ("output_channel_appendline", OutputChannelRawContext, {}),
)

# W14-4: full allowlist mirrors contracts._EVIDENCE_EVENT_KIND_TO_EVENT_CLASS.
# 7 strict 1:1 kinds + 2 alias kinds (extension_host → activation,
# log → scenario) sharing an existing raw_context variant.
_KIND_TO_EXPECTED_EVENT_CLASS: tuple[tuple[str, str, type, dict[str, object]], ...] = (
    ("scenario", "scenario", ScenarioRawContext, {}),
    ("activation", "activation", ActivationRawContext, {}),
    ("extension_host", "activation", ActivationRawContext, {}),
    ("log", "scenario", ScenarioRawContext, {}),
    ("network", "network", NetworkRawContext, {}),
    ("file", "file", FileRawContext, {}),
    ("process", "process", ProcessRawContext, {"pid": 1}),
    ("ui_blocker", "ui_blocker", UiBlockerRawContext, {}),
    ("output_channel_appendline", "output_channel_appendline", OutputChannelRawContext, {}),
)

_ALL_KINDS: tuple[str, ...] = tuple(kind for kind, _, _ in _KIND_TO_VARIANT)
_ALL_EVENT_CLASSES: tuple[str, ...] = tuple(
    dict.fromkeys(
        event_class for _, event_class, _, _ in _KIND_TO_EXPECTED_EVENT_CLASS
    )
)
_EXTRAS_FOR_EVENT_CLASS: dict[str, dict[str, object]] = {
    event_class: extra
    for _, event_class, _, extra in _KIND_TO_EXPECTED_EVENT_CLASS
}


def _evidence_payload(
    raw_context: dict[str, object], *, kind: str = "network"
) -> dict[str, object]:
    return {
        "event_id": "evt-0001",
        "kind": kind,
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
                },
                kind="file",
            )
        )


def test_process_variant_requires_pid() -> None:
    with pytest.raises(ValidationError):
        EvidenceEvent.model_validate(
            _evidence_payload({"event_class": "process"}, kind="process")
        )
    event = EvidenceEvent.model_validate(
        _evidence_payload({"event_class": "process", "pid": 4321}, kind="process")
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
            },
            kind="scenario",
        )
    )
    assert isinstance(event.raw_context, ScenarioRawContext)
    assert event.raw_context.event_class == "scenario"
    assert event.raw_context.status == "completed"


def test_discriminator_dispatches_by_event_class() -> None:
    for kind, expected_cls, extra in _KIND_TO_VARIANT:
        payload = {"event_class": kind, **extra}
        event = EvidenceEvent.model_validate(_evidence_payload(payload, kind=kind))
        assert isinstance(event.raw_context, expected_cls), (
            f"{kind!r} should dispatch to {expected_cls.__name__}, "
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


# ---------------------------------------------------------------------------
# W14-4 [FOLLOWUP evidence-event-kind-raw-context-invariant]
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "event_class", "expected_cls", "extra"),
    _KIND_TO_EXPECTED_EVENT_CLASS,
    ids=[
        f"kind={kind}-event_class={event_class}"
        for kind, event_class, _, _ in _KIND_TO_EXPECTED_EVENT_CLASS
    ],
)
def test_evidence_event_kind_matches_event_class_accepts_all_pairs(
    kind: str, event_class: str, expected_cls: type, extra: dict[str, object]
) -> None:
    """W14-4: every kind in the closed allowlist is accepted when paired
    with its expected event_class. The 9-entry table mirrors
    ``contracts._EVIDENCE_EVENT_KIND_TO_EVENT_CLASS``: 7 strict 1:1 kinds
    plus the 2 alias kinds (``extension_host`` and ``log``).
    """
    event = EvidenceEvent.model_validate(
        _evidence_payload({"event_class": event_class, **extra}, kind=kind)
    )
    assert event.kind == kind
    assert event.raw_context.event_class == event_class
    assert isinstance(event.raw_context, expected_cls)


def _mismatch_pairs() -> list[tuple[str, str, dict[str, object]]]:
    """Cartesian product of (kind, event_class) where the kind's expected
    event_class differs from the supplied event_class.

    9 kinds x 7 event_classes = 63 pairs; remove the 9 matching pairs
    (one per kind, where the kind's expected event_class equals the
    supplied event_class) to get 54 mismatch pairs. Each pair carries
    the extra fields the discriminator needs for the target variant to
    validate up to the invariant check (e.g. ``ProcessRawContext``
    requires ``pid``).
    """
    pairs: list[tuple[str, str, dict[str, object]]] = []
    for kind, expected_event_class, _cls, _extra in _KIND_TO_EXPECTED_EVENT_CLASS:
        for event_class in _ALL_EVENT_CLASSES:
            if event_class == expected_event_class:
                continue
            pairs.append(
                (kind, event_class, dict(_EXTRAS_FOR_EVENT_CLASS[event_class]))
            )
    return pairs


_MISMATCH_PAIRS = _mismatch_pairs()


@pytest.mark.parametrize(
    ("kind", "event_class", "extra"),
    _MISMATCH_PAIRS,
    ids=[
        f"kind={kind}-event_class={event_class}"
        for kind, event_class, _ in _MISMATCH_PAIRS
    ],
)
def test_evidence_event_rejects_kind_event_class_mismatch(
    kind: str, event_class: str, extra: dict[str, object]
) -> None:
    """W14-4: every mismatched (kind, event_class) pair is rejected.

    9 kinds x 6 wrong event_class each = 54 cases. The invariant landed
    in [packages/analysis_contracts/contracts.py] as a
    ``@model_validator(mode="after")`` on ``EvidenceEvent`` and turns a
    silently-accepted producer drift into a Pydantic ``ValidationError``
    at ingest.
    """
    with pytest.raises(ValidationError) as exc_info:
        EvidenceEvent.model_validate(
            _evidence_payload({"event_class": event_class, **extra}, kind=kind)
        )
    message = str(exc_info.value)
    assert "expects raw_context.event_class" in message, message


def test_evidence_event_rejects_unknown_kind() -> None:
    """W14-4: a kind outside the closed allowlist is rejected with the
    allowlist surface in the error message, so a future producer that
    introduces a new kind without registering it in
    ``_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS`` fails at ingest instead of
    drifting downstream.
    """
    with pytest.raises(ValidationError) as exc_info:
        EvidenceEvent.model_validate(
            _evidence_payload(
                {"event_class": "scenario"}, kind="unrecognized_kind"
            )
        )
    assert "is not a recognized kind" in str(exc_info.value), str(exc_info.value)


def test_evidence_event_rejects_missing_raw_context_when_kind_set() -> None:
    """W14-4 edge: omitting raw_context falls back to ScenarioRawContext
    (event_class='scenario'); setting kind to anything that does not
    map to 'scenario' trips the invariant. This is the exact shape that
    producer code emits when it forgets to populate raw_context for a
    non-scenario event.
    """
    with pytest.raises(ValidationError) as exc_info:
        EvidenceEvent.model_validate({"event_id": "evt-0002", "kind": "network"})
    assert "expects raw_context.event_class" in str(exc_info.value), str(
        exc_info.value
    )
