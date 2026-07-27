"""W26 / Stream 3 (B6): the run_quality anchor reads a frozen log-capture
snapshot, not the live filesystem.

The primary B6 flicker driver (found by the 2026-06-26 verification workflow)
was ``ActivationReport._log_capture_health`` re-``stat()``-ing the exthost log on
*every* property access, so ``extension_host_log_missing`` flickered run-to-run
and the multiple reads in ``print_summary`` + ``save`` could disagree within one
report. Finalization now freezes the view onto ``log_capture_health_snapshot``;
the property returns it when frozen, else falls back to a live read (mandatory
for ``log_health`` + fixture paths that never call ``stop()``).
"""

from __future__ import annotations

import pytest

import executor.flows.playwright.monitor.types as types_mod
from executor.flows.playwright.monitor.types import ActivationReport


def test_frozen_snapshot_is_returned_verbatim() -> None:
    report = ActivationReport()
    snapshot = {"extension_host_log_found": True, "extension_host_log_present": True}
    report.log_capture_health_snapshot = snapshot
    assert report._log_capture_health is snapshot


def test_frozen_snapshot_never_touches_the_live_filesystem(monkeypatch) -> None:
    report = ActivationReport()
    report.log_capture_health_snapshot = {"extension_host_log_present": True}

    def _boom():  # pragma: no cover - must never be called
        raise AssertionError("a frozen snapshot must not re-read the live FS")

    monkeypatch.setattr(types_mod, "resolve_monitor_api", _boom)

    # Repeated reads (the property is consulted by automation_health /
    # run_quality / run_quality_reasons / run_quality_reason_partition / log_health
    # — historically up to 6 live reads per finalize) stay stable and FS-free.
    first = report._log_capture_health
    second = report._log_capture_health
    assert first == second == {"extension_host_log_present": True}
    # automation_health also funnels through _log_capture_health: still FS-free.
    assert isinstance(report.automation_health, dict)


def test_live_fallback_when_unfrozen(monkeypatch) -> None:
    report = ActivationReport()
    assert report.log_capture_health_snapshot is None

    monkeypatch.setattr(types_mod, "resolve_monitor_api", lambda: _FakeApi())
    monkeypatch.setattr(
        types_mod,
        "summarize_extension_host_logs",
        lambda offsets, paths: {"source": "live", "paths": list(paths)},
    )
    assert report._log_capture_health == {"source": "live", "paths": ["/log/a"]}


def test_unfrozen_property_re_reads_changing_live_values(monkeypatch) -> None:
    # Proves the fallback really is live (and therefore why freezing matters):
    # without a snapshot, two accesses can disagree as the FS changes.
    report = ActivationReport()
    seq = iter([{"n": 1}, {"n": 2}])
    monkeypatch.setattr(types_mod, "resolve_monitor_api", lambda: _FakeApi())
    monkeypatch.setattr(
        types_mod, "summarize_extension_host_logs", lambda offsets, paths: next(seq)
    )
    assert report._log_capture_health == {"n": 1}
    assert report._log_capture_health == {"n": 2}

    # Freezing collapses that to a single stable value.
    report.log_capture_health_snapshot = {"n": 99}
    assert report._log_capture_health == {"n": 99}
    assert report._log_capture_health == {"n": 99}


class _FakeApi:
    def find_exthost_logs(self):
        return ["/log/a"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
