"""Adaptive early-give-up for the layered stimulus plan.

When the target extension produces NO observable reaction across
``_NO_REACTION_GIVEUP_ATTEMPTS`` consecutive attempts (e.g. GitHub.copilot-chat,
which cannot auth/network in the sandbox), ``run_stimulus_plan`` stops driving
the remaining attempts so they do not burn wall-clock toward the automation
timeout. Any single real target reaction resets the counter, so a responsive
extension still runs the full plan.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from executor.flows.playwright.stimulus import passes as passes_module


def _make_payload(n: int) -> SimpleNamespace:
    return SimpleNamespace(
        selected_scenarios=[f"s{i}" for i in range(n)],
        event_attempts=[
            {
                "attempt_id": f"att-{i}",
                "executor_action": "command:auto",
                "event_family": "onCommand",
                "legacy_scenarios": [f"s{i}"],
            }
            for i in range(n)
        ],
        stimulus_passes=[
            {
                "pass_id": "ui_first_user_session",
                "order": 1,
                "label": "UI first user session",
                "attempt_ids": [f"att-{i}" for i in range(n)],
                "prerequisite_keys": [],
            }
        ],
        prerequisite_results=[],
    )


def _patch_common(monkeypatch: pytest.MonkeyPatch) -> None:
    # No real Playwright page; every attempt "succeeds" as a no-op, and dedupe
    # is disabled so every attempt actually executes (distinct execution path).
    monkeypatch.setattr(passes_module, "execute_attempt", lambda *a, **k: None)
    monkeypatch.setattr(passes_module, "dedupe_execution_key", lambda *a, **k: "")


def test_gives_up_when_target_never_reacts(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_common(monkeypatch)
    # Target never reacts: the cheap reaction count stays flat.
    monkeypatch.setattr(passes_module, "_cheap_target_reaction_count", lambda _m: 0)

    n = passes_module._NO_REACTION_GIVEUP_ATTEMPTS + 5
    result = passes_module.run_stimulus_plan(
        page=None, payload=_make_payload(n), monitor=None
    )

    giveup = [
        item
        for item in result.skipped_scenarios
        if item.reason_code == passes_module._EARLY_GIVEUP_REASON
    ]
    assert giveup, (
        "a non-responsive target must trigger early give-up on the remaining "
        "attempts instead of grinding through the whole plan"
    )
    # Only the tail past the threshold is skipped; the bulk still ran.
    assert 1 <= len(giveup) <= 6, (
        f"give-up should skip only the post-threshold tail; got {len(giveup)}"
    )
    assert all(item.detail for item in giveup), "give-up detail must be populated"


def test_no_giveup_when_target_reacts(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_common(monkeypatch)
    # Reaction count grows on every probe -> the consecutive counter resets each
    # attempt and the threshold is never reached.
    counter = {"n": 0}

    def _growing(_m: object) -> int:
        counter["n"] += 1
        return counter["n"]

    monkeypatch.setattr(passes_module, "_cheap_target_reaction_count", _growing)

    n = passes_module._NO_REACTION_GIVEUP_ATTEMPTS + 5
    result = passes_module.run_stimulus_plan(
        page=None, payload=_make_payload(n), monitor=None
    )

    giveup = [
        item
        for item in result.skipped_scenarios
        if item.reason_code == passes_module._EARLY_GIVEUP_REASON
    ]
    assert giveup == [], "a reacting target must run the full plan (no early give-up)"


class _FakeMonitor:
    """Minimal monitor capturing the automation events run_stimulus_plan emits."""

    def __init__(self) -> None:
        self.automation_events: list[tuple[str, str]] = []
        self.report = SimpleNamespace(target_file_events=[], target_network_events=[])

    def record_stimulus_pass_event(self, *a: object, **k: object) -> None:
        return None

    def record_event_attempt_start(self, *a: object, **k: object) -> None:
        return None

    def record_event_attempt_end(self, *a: object, **k: object) -> None:
        return None

    def record_automation_event(self, kind: str, message: str, **k: object) -> None:
        self.automation_events.append((kind, message))


def test_giveup_records_automation_event(monkeypatch: pytest.MonkeyPatch) -> None:
    """The give-up must emit a ``stimulus_early_giveup`` automation event so the
    report honestly explains why the remaining plan was skipped."""
    _patch_common(monkeypatch)
    monkeypatch.setattr(passes_module, "_cheap_target_reaction_count", lambda _m: 0)
    mon = _FakeMonitor()

    n = passes_module._NO_REACTION_GIVEUP_ATTEMPTS + 5
    passes_module.run_stimulus_plan(page=None, payload=_make_payload(n), monitor=mon)

    kinds = [kind for kind, _ in mon.automation_events]
    assert "stimulus_early_giveup" in kinds, (
        f"give-up must record a stimulus_early_giveup event; got {kinds}"
    )


def test_cheap_target_reaction_count_handles_missing_monitor() -> None:
    assert passes_module._cheap_target_reaction_count(None) == 0
    # Monitor without a report attribute -> 0, never raises.
    assert passes_module._cheap_target_reaction_count(SimpleNamespace()) == 0
    # Monitor whose report exposes the cheap target-event lists.
    monitor = SimpleNamespace(
        report=SimpleNamespace(target_file_events=[1, 2, 3], target_network_events=[1])
    )
    assert passes_module._cheap_target_reaction_count(monitor) == 4
