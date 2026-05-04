"""W10-2 contract tests: ``_TriggerPayloadDraft`` removed; the planner now
builds ``TriggerPayload`` directly via ``model_construct`` and re-validates
on the way out.

Also pins the W10-2 rider: ``glob_to_bait_filename`` is the public API;
``_glob_to_bait_filename`` is gone.
"""

from __future__ import annotations

import pytest

from packages.analysis_contracts import TriggerPayload
from packages.analysis_planner import (
    glob_to_bait_filename,
    select_scenarios,
)


def test_trigger_payload_draft_alias_is_removed() -> None:
    """The historic ``_TriggerPayloadDraft`` shadow type must not be
    importable from anywhere — the planner builds ``TriggerPayload``
    directly now."""
    with pytest.raises(ImportError):
        from packages.analysis_planner.selection import (  # noqa: F401
            _TriggerPayloadDraft,
        )


def test_glob_to_bait_filename_public_api_works() -> None:
    """``_glob_to_bait_filename`` was promoted to the public surface so
    ``workflows/marketplace/triggers.py`` no longer imports a private
    helper (ADR 0005 §3 fix)."""
    assert glob_to_bait_filename("*.csv") == "bait.csv"
    assert glob_to_bait_filename("*.{png,jpg}") == "bait.png"
    assert glob_to_bait_filename("**/*.csv") == "bait.csv"
    assert glob_to_bait_filename("config.yaml") == "config.yaml"
    assert glob_to_bait_filename("file?.txt") is None


def test_private_glob_helper_no_longer_exists() -> None:
    """Stale private alias must be gone — defends against accidental
    re-introduction of the underscore-prefixed import."""
    from packages.analysis_planner import io

    assert not hasattr(io, "_glob_to_bait_filename")
    assert hasattr(io, "glob_to_bait_filename")


def test_workflows_triggers_facade_does_not_re_export_private_glob() -> None:
    from workflows.marketplace import triggers

    assert "_glob_to_bait_filename" not in triggers.__all__
    assert "glob_to_bait_filename" in triggers.__all__


def test_select_scenarios_returns_validated_trigger_payload() -> None:
    """Planner output must be a fully-validated TriggerPayload (the
    one-shot ``model_validate`` at the planner exit boundary kicks in).
    """
    payload = select_scenarios(
        activation_events=[{"event_type": "onLanguage", "event_value": "python"}],
        publisher_name="ms-python.python",
    )
    assert isinstance(payload, TriggerPayload)
    assert payload.target_extension_id == "ms-python.python"
    # Round-trip equivalence guards against mutation residue from the
    # model_construct accumulator phase.
    round_trip = TriggerPayload.model_validate(payload.model_dump())
    assert round_trip == payload
