"""Regression guard: the command/trigger effect waits stay host-side.

These settle waits used to poll the renderer (``page.wait_for_timeout``), so
their wall-clock cost was measured in *renderer* time — under cumulative load a
nominal 3s settle ballooned to ~8.5s, and a layered scan spent ~400s in these
waits alone. They now sleep host-side (``page=None``) at a flat nominal cost.
A ``monitor.capture_runtime_snapshot()`` early-exit was tried and reverted —
each snapshot does a renderer round-trip + full exthost-log reparse (~8s under
load), which inflated every wait to ~50s. This test pins the host-side cost so
neither regression can creep back.
"""

from __future__ import annotations

import pytest

from executor.flows.playwright import wait_helpers


@pytest.fixture
def recorded_waits(monkeypatch):
    """Replace the sleep primitive so tests are instant and record each call."""
    calls: list[tuple[object, int]] = []

    def _fake_wait(page: object, timeout_ms: int) -> None:
        calls.append((page, timeout_ms))

    monkeypatch.setattr(wait_helpers, "_wait", _fake_wait)
    return calls


class _Page:
    """A live-looking page; if a wait reached it, ``wait_for_timeout`` records."""

    def __init__(self) -> None:
        self.renderer_waits = 0

    def wait_for_timeout(self, ms: int) -> None:
        self.renderer_waits += 1


@pytest.mark.parametrize(
    "wait_fn",
    [wait_helpers.wait_for_command_effect, wait_helpers.wait_for_trigger_effect],
)
def test_effect_wait_is_host_side_and_full_duration(recorded_waits, wait_fn) -> None:
    result = wait_fn(_Page())
    assert result.status == "completed"
    # 1500ms / 100ms poll = 15 cycles (trimmed from 3000ms for scan speed), and
    # every one must be host-side (page=None) — never routed back through the
    # renderer where it inflates under load.
    assert len(recorded_waits) == 15
    assert all(page is None for page, _ in recorded_waits)
    assert all(timeout == 100 for _, timeout in recorded_waits)


def test_effect_wait_does_not_touch_the_renderer(monkeypatch) -> None:
    # With the real _wait in place but no host sleep patched, prove the wait
    # never calls page.wait_for_timeout (the load-coupled path).
    monkeypatch.setattr(wait_helpers.time, "sleep", lambda _s: None)
    page = _Page()
    result = wait_helpers.wait_for_trigger_effect(page)
    assert result.status == "completed"
    assert page.renderer_waits == 0
