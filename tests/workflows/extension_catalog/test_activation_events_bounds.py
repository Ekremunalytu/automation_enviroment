"""W15-3 behavioral regression: ``activationEvents`` size caps.

Codex 2026-05-10 U8 close-out. Two layers exercised:

1. Pydantic ``ExtensionActivationEventsSchema`` / ``ExtensionDetailSchema``
   enforce per-string ``max_length`` and list ``max_length`` — boundary
   inputs (64 / 1024 / 512) pass; one-over-boundary inputs raise
   ``ValidationError``.
2. ``parse_activation_events`` short-circuits hostile input before
   Pydantic ever sees it — a 600-entry list returns 512; an event
   string whose ``event_value`` exceeds 1024 chars is silently skipped
   (mirroring the existing tolerant ``continue`` style for non-``str``
   events).

Architecture discipline is pinned by
``tests/architecture/test_activationevents_bounds.py``; this suite
proves the observable runtime contract on adversarial inputs.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from appcore.contracts.schema_defs.catalog import (
    ExtensionActivationEventsSchema,
    ExtensionDetailSchema,
)
from workflows.extension_catalog.manifest_parser import parse_activation_events


def _base_extension_payload() -> dict:
    """Minimal payload satisfying ``ExtensionDetailSchema`` required fields."""
    return {
        "id": 1,
        "name": "fixture-ext",
        "publisher": "fixture-pub",
        "version": "1.0.0",
        "engines": {"vscode": "^1.80.0"},
    }


# ---------------------------------------------------------------------------
# Pydantic boundary acceptance
# ---------------------------------------------------------------------------


def test_event_type_at_boundary_64_chars_is_accepted() -> None:
    schema = ExtensionActivationEventsSchema(
        event_type="x" * 64, event_value=None
    )
    assert len(schema.event_type) == 64


def test_event_value_at_boundary_1024_chars_is_accepted() -> None:
    schema = ExtensionActivationEventsSchema(
        event_type="onCommand", event_value="x" * 1024
    )
    assert schema.event_value is not None
    assert len(schema.event_value) == 1024


def test_activation_events_list_at_boundary_512_is_accepted() -> None:
    events = [{"event_type": "onLanguage", "event_value": "python"}] * 512
    payload = _base_extension_payload() | {"activation_events": events}
    detail = ExtensionDetailSchema.model_validate(payload)
    assert len(detail.activation_events) == 512


# ---------------------------------------------------------------------------
# Pydantic over-cap rejection
# ---------------------------------------------------------------------------


def test_event_type_one_over_boundary_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        ExtensionActivationEventsSchema(event_type="x" * 65, event_value=None)


def test_event_value_one_over_boundary_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        ExtensionActivationEventsSchema(
            event_type="onCommand", event_value="x" * 1025
        )


def test_activation_events_list_one_over_boundary_raises_validation_error() -> None:
    events = [{"event_type": "onLanguage", "event_value": "python"}] * 513
    payload = _base_extension_payload() | {"activation_events": events}
    with pytest.raises(ValidationError):
        ExtensionDetailSchema.model_validate(payload)


# ---------------------------------------------------------------------------
# Parser-level defense-in-depth
# ---------------------------------------------------------------------------


def test_parse_activation_events_slices_oversized_list_at_512() -> None:
    package_json = {
        "activationEvents": [f"onCommand:cmd.run.{i}" for i in range(600)]
    }
    parsed = parse_activation_events(package_json)
    assert parsed is not None
    assert len(parsed) == 512


def test_parse_activation_events_skips_oversized_event_value() -> None:
    """Events whose ``event_value`` would exceed the Pydantic cap are
    silently dropped at the parser, matching the existing tolerant
    ``continue`` style for non-``str`` events.
    """
    package_json = {
        "activationEvents": [
            "onCommand:" + ("x" * 1025),  # over per-string cap -> skipped
            "onLanguage:python",          # well under cap -> kept
        ]
    }
    parsed = parse_activation_events(package_json)
    assert parsed is not None
    assert parsed == [{"event_type": "onLanguage", "event_value": "python"}]
