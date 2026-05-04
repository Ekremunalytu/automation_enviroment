"""Direct unit tests for ``ReportAssembler`` (W11-2).

These tests pin the report-assembly collaborator extracted from
``ExtensionMonitor`` in W11-2. They import at the real module path
(``executor.flows.playwright.monitor_report_assembler``) rather than
through the ``monitor`` facade so that the W12 directory reshuffle
cannot silently regress this surface.

``refresh_derived_state`` calls into seven module-level helpers
(``_annotate_*``, ``derive_verified_capabilities``,
``reconcile_event_attempts``, ``summarize_event_attempts_for_report``,
``_reconcile_coverage_verification``, ``_build_signal_summary``); each
test monkeypatches the helper at the assembler's import path so the
assembler's call shape and assignment behavior are pinned without
re-exercising the helpers themselves (those have their own test
modules). ``persist`` exercises the debounce throttle directly against
a real ``ActivationReport`` and ``tmp_path`` writer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from executor.flows.playwright import monitor_report_assembler
from executor.flows.playwright.monitor_report_assembler import ReportAssembler
from executor.flows.playwright.monitor_records import ScenarioTrace
from executor.flows.playwright.monitor_types import ActivationReport


# ---------------------------------------------------------------------------
# refresh_derived_state
# ---------------------------------------------------------------------------


def _patch_refresh_helpers(monkeypatch) -> dict[str, list[Any]]:
    """Stub the seven helpers refresh_derived_state calls.

    Returns a mutable record dict the test can assert against. Each
    stub records ``(args, kwargs)`` for its name and returns a
    deterministic sentinel that the assembler must assign to the right
    report field.
    """
    calls: dict[str, list[Any]] = {
        "_annotate_network_events": [],
        "_annotate_file_events": [],
        "_annotate_process_events": [],
        "derive_verified_capabilities": [],
        "reconcile_event_attempts": [],
        "summarize_event_attempts_for_report": [],
        "_reconcile_coverage_verification": [],
        "_build_signal_summary": [],
    }

    def _record(name: str, ret: Any):
        def _stub(*args, **kwargs):
            calls[name].append((args, kwargs))
            return ret

        return _stub

    monkeypatch.setattr(
        monitor_report_assembler,
        "_annotate_network_events",
        _record("_annotate_network_events", ["net-out"]),
    )
    monkeypatch.setattr(
        monitor_report_assembler,
        "_annotate_file_events",
        _record("_annotate_file_events", ["file-out"]),
    )
    monkeypatch.setattr(
        monitor_report_assembler,
        "_annotate_process_events",
        _record("_annotate_process_events", ["proc-out"]),
    )
    # Two of the attempted capabilities will be in the derived set so we can
    # assert official vs heuristic split logic.
    monkeypatch.setattr(
        monitor_report_assembler,
        "derive_verified_capabilities",
        _record("derive_verified_capabilities", ["cap.read", "cap.write"]),
    )
    monkeypatch.setattr(
        monitor_report_assembler,
        "reconcile_event_attempts",
        _record("reconcile_event_attempts", ["evt-attempts"]),
    )
    monkeypatch.setattr(
        monitor_report_assembler,
        "summarize_event_attempts_for_report",
        _record("summarize_event_attempts_for_report", {"summary": True}),
    )
    monkeypatch.setattr(
        monitor_report_assembler,
        "_reconcile_coverage_verification",
        _record(
            "_reconcile_coverage_verification",
            ({"summary": "S"}, [{"row": 1}], {"official": {"x": 1}}),
        ),
    )
    monkeypatch.setattr(
        monitor_report_assembler,
        "_build_signal_summary",
        _record("_build_signal_summary", {"signal": "sig"}),
    )

    # ``canonical_evidence_links`` is a derived property that walks the
    # (now stubbed) event lists; with sentinel return values like
    # ``["net-out"]`` it would crash inside ``_build_evidence_bundle``.
    # Pin the property to a deterministic value so the assembler's
    # ``evidence_links = report.canonical_evidence_links`` line is
    # exercised without dragging the real bundle builder in.
    monkeypatch.setattr(
        ActivationReport,
        "canonical_evidence_links",
        property(lambda self: [{"link": "stub"}]),
    )

    return calls


def _make_report(**overrides: Any) -> ActivationReport:
    """Build a minimal ActivationReport for assembler tests.

    Only writes real fields. ``official_attempted_capabilities`` is a
    derived property on ``ActivationReport``; tests that need a specific
    value patch it via :func:`_patch_official_attempted` below.
    """

    base = ActivationReport(target_extension_id="publisher.tool")
    base.network_events = []
    base.file_events = []
    base.process_events = []
    base.activated = []
    base.scenario_traces = [ScenarioTrace(name="s1", started_at=0.0)]
    base.heuristic_attempted_capabilities = ["cap.write"]
    base.verified_capabilities = []
    base.heuristic_verified_capabilities = []
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def _patch_official_attempted(monkeypatch, value: list[str]) -> None:
    """Override the ``official_attempted_capabilities`` derived property.

    The property normally filters ``attempted_capabilities`` through the
    coverage matrix. Tests that want to assert promotion split logic need
    a deterministic value without setting up the matrix; a class-scoped
    monkeypatch (auto-reverted at test teardown) is the cleanest path.
    """

    monkeypatch.setattr(
        ActivationReport,
        "official_attempted_capabilities",
        property(lambda self: list(value)),
    )


def test_refresh_calls_three_event_annotators_with_report_state(monkeypatch) -> None:
    calls = _patch_refresh_helpers(monkeypatch)
    report = _make_report()
    assembler = ReportAssembler(report=report, report_path=None)

    assembler.refresh_derived_state()

    # Each annotator received the matching events list, the activation list,
    # the scenario traces, and the target_extension_id — in that order.
    assert len(calls["_annotate_network_events"]) == 1
    args, _ = calls["_annotate_network_events"][0]
    assert args[1] is report.activated
    assert args[2] is report.scenario_traces
    assert args[3] == "publisher.tool"
    assert len(calls["_annotate_file_events"]) == 1
    assert len(calls["_annotate_process_events"]) == 1


def test_refresh_writes_annotator_returns_back_onto_report(monkeypatch) -> None:
    _patch_refresh_helpers(monkeypatch)
    report = _make_report()
    assembler = ReportAssembler(report=report, report_path=None)

    assembler.refresh_derived_state()

    assert report.network_events == ["net-out"]
    assert report.file_events == ["file-out"]
    assert report.process_events == ["proc-out"]


def test_refresh_promotes_only_official_attempted_into_verified(
    monkeypatch,
) -> None:
    _patch_refresh_helpers(monkeypatch)
    # derive_* returns ["cap.read", "cap.write"]; official_attempted only
    # contains "cap.read", so verified_capabilities must end up as ["cap.read"]
    # and "cap.write" must NOT leak into the official list.
    _patch_official_attempted(monkeypatch, ["cap.read", "cap.untouched"])
    report = _make_report()
    assembler = ReportAssembler(report=report, report_path=None)

    assembler.refresh_derived_state()

    assert report.verified_capabilities == ["cap.read"]
    assert "cap.write" not in report.verified_capabilities


def test_refresh_promotes_heuristic_separately_from_official(monkeypatch) -> None:
    _patch_refresh_helpers(monkeypatch)
    # heuristic_attempted_capabilities is a real field set by _make_report
    # (["cap.write"]). Pin official as a disjoint set so we can assert the
    # heuristic track does not absorb "cap.read".
    _patch_official_attempted(monkeypatch, ["cap.read"])
    report = _make_report()
    assembler = ReportAssembler(report=report, report_path=None)

    assembler.refresh_derived_state()

    # derive_* returns ["cap.read", "cap.write"]; heuristic_attempted only
    # contains "cap.write", so heuristic_verified must end up as ["cap.write"]
    # and "cap.read" must NOT leak into the heuristic list.
    assert report.heuristic_verified_capabilities == ["cap.write"]
    assert "cap.read" not in report.heuristic_verified_capabilities


def test_refresh_assigns_event_attempts_from_reconcile_return(monkeypatch) -> None:
    calls = _patch_refresh_helpers(monkeypatch)
    report = _make_report()
    assembler = ReportAssembler(report=report, report_path=None)

    assembler.refresh_derived_state()

    assert report.event_attempts == ["evt-attempts"]
    # And the reconcile helper saw the report instance.
    assert calls["reconcile_event_attempts"][0][0][0] is report


def test_refresh_populates_coverage_tuple(monkeypatch) -> None:
    _patch_refresh_helpers(monkeypatch)
    report = _make_report()
    assembler = ReportAssembler(report=report, report_path=None)

    assembler.refresh_derived_state()

    assert report.coverage_summary == {"summary": "S"}
    assert report.coverage_matrix == [{"row": 1}]
    assert report.coverage_tracks == {"official": {"x": 1}}


def test_refresh_writes_signal_summary_and_evidence_links(monkeypatch) -> None:
    _patch_refresh_helpers(monkeypatch)
    report = _make_report()
    assembler = ReportAssembler(report=report, report_path=None)

    assembler.refresh_derived_state()

    assert report.signal_summary == {"signal": "sig"}
    # evidence_links must mirror canonical_evidence_links — both stubbed.
    assert report.evidence_links == [{"link": "stub"}]
    assert report.evidence_links == report.canonical_evidence_links


def test_refresh_summarize_called_for_both_tracks(monkeypatch) -> None:
    calls = _patch_refresh_helpers(monkeypatch)
    report = _make_report()
    assembler = ReportAssembler(report=report, report_path=None)

    assembler.refresh_derived_state()

    tracks = sorted(
        kw["track"] for _, kw in calls["summarize_event_attempts_for_report"]
    )
    assert tracks == ["heuristic", "official"]
    # And both writes landed on the report.
    assert report.official_event_coverage == {"summary": True}
    assert report.heuristic_workflow_coverage == {"summary": True}


# ---------------------------------------------------------------------------
# persist
# ---------------------------------------------------------------------------


def test_persist_no_op_when_report_path_is_none() -> None:
    report = ActivationReport(target_extension_id="publisher.tool")
    assembler = ReportAssembler(report=report, report_path=None)

    # Should not raise and should not throw even with force=True; the
    # throttle stays at the default 0.0 because the early return fires
    # before any time.time() reading.
    assembler.persist(force=True)
    assert assembler._last_persist_at == 0.0


def test_persist_writes_when_force_is_true(tmp_path, monkeypatch) -> None:
    report = ActivationReport(target_extension_id="publisher.tool")
    target = tmp_path / "report.json"
    saves: list[Path] = []

    def _fake_save(self, path, *, announce: bool = False) -> None:
        saves.append(Path(path))

    monkeypatch.setattr(ActivationReport, "save", _fake_save)
    assembler = ReportAssembler(report=report, report_path=target)

    assembler.persist(force=True)

    assert saves == [target]
    assert assembler._last_persist_at > 0.0


def test_persist_throttles_back_to_back_unforced_calls(tmp_path, monkeypatch) -> None:
    report = ActivationReport(target_extension_id="publisher.tool")
    # Single-element counts so modulo guards do not trip (1 % 5 != 0,
    # 1 % 2 != 0); only the time-window guard governs the second call.
    report.network_events = [object()]
    report.file_events = [object()]
    report.scenario_traces = [ScenarioTrace(name="s1", started_at=0.0)]
    target = tmp_path / "report.json"
    saves: list[Path] = []

    def _fake_save(self, path, *, announce: bool = False) -> None:
        saves.append(Path(path))

    monkeypatch.setattr(ActivationReport, "save", _fake_save)
    assembler = ReportAssembler(report=report, report_path=target)

    # First call (force=True) writes and bumps _last_persist_at.
    assembler.persist(force=True)
    # Second call (force=False) must short-circuit: counts are all
    # non-modulo and the throttle window is < 1s.
    assembler.persist(force=False)

    assert len(saves) == 1


def test_persist_writes_when_network_events_count_is_modulo_5(
    tmp_path, monkeypatch
) -> None:
    report = ActivationReport(target_extension_id="publisher.tool")
    # Five network events trips the modulo-5 path even when the throttle
    # window has not elapsed.
    report.network_events = [object()] * 5
    target = tmp_path / "report.json"
    saves: list[int] = []

    def _fake_save(self, path, *, announce: bool = False) -> None:
        saves.append(len(self.network_events))

    monkeypatch.setattr(ActivationReport, "save", _fake_save)
    assembler = ReportAssembler(report=report, report_path=target)

    # Pre-bump _last_persist_at so the time-window guard would otherwise
    # short-circuit; modulo-5 must override.
    import time

    assembler._last_persist_at = time.time()

    assembler.persist(force=False)

    assert saves == [5]


def test_persist_writes_when_file_events_count_is_modulo_5(
    tmp_path, monkeypatch
) -> None:
    report = ActivationReport(target_extension_id="publisher.tool")
    report.file_events = [object()] * 5
    target = tmp_path / "report.json"
    saves: list[int] = []

    def _fake_save(self, path, *, announce: bool = False) -> None:
        saves.append(len(self.file_events))

    monkeypatch.setattr(ActivationReport, "save", _fake_save)
    assembler = ReportAssembler(report=report, report_path=target)

    import time

    assembler._last_persist_at = time.time()

    assembler.persist(force=False)

    assert saves == [5]


def test_persist_writes_when_scenario_traces_count_is_modulo_2(
    tmp_path, monkeypatch
) -> None:
    report = ActivationReport(target_extension_id="publisher.tool")
    report.scenario_traces = [
        ScenarioTrace(name="s1", started_at=0.0),
        ScenarioTrace(name="s2", started_at=0.0),
    ]
    target = tmp_path / "report.json"
    saves: list[int] = []

    def _fake_save(self, path, *, announce: bool = False) -> None:
        saves.append(len(self.scenario_traces))

    monkeypatch.setattr(ActivationReport, "save", _fake_save)
    assembler = ReportAssembler(report=report, report_path=target)

    import time

    assembler._last_persist_at = time.time()

    assembler.persist(force=False)

    assert saves == [2]


def test_persist_swallows_oserror_and_does_not_advance_throttle(
    tmp_path, monkeypatch
) -> None:
    report = ActivationReport(target_extension_id="publisher.tool")
    target = tmp_path / "report.json"

    def _raise(self, path, *, announce: bool = False) -> None:
        raise OSError("disk full")

    log_messages: list[str] = []

    def _capture_log(message: str) -> None:
        log_messages.append(message)

    monkeypatch.setattr(ActivationReport, "save", _raise)
    monkeypatch.setattr(monitor_report_assembler, "_log", _capture_log)

    assembler = ReportAssembler(report=report, report_path=target)
    # Should not raise.
    assembler.persist(force=True)

    # Throttle must NOT advance on a failed save (regression-pin for the
    # try/except shape preserved across the W11-2 move).
    assert assembler._last_persist_at == 0.0
    # Operator-visible log emitted.
    assert any("Live report persistence failed" in msg for msg in log_messages)


def test_persist_short_circuits_when_no_threshold_trips_and_window_open(
    tmp_path, monkeypatch
) -> None:
    """No force, no modulo trip, throttle window still open => skip."""

    report = ActivationReport(target_extension_id="publisher.tool")
    # Single-element counts so modulo guards do not trip.
    report.network_events = [object()]
    report.file_events = [object()]
    report.scenario_traces = [ScenarioTrace(name="s1", started_at=0.0)]
    target = tmp_path / "report.json"
    saves: list[int] = []

    def _fake_save(self, path, *, announce: bool = False) -> None:
        saves.append(1)

    monkeypatch.setattr(ActivationReport, "save", _fake_save)
    assembler = ReportAssembler(report=report, report_path=target)

    # Bump throttle so (now - last) < 1.0 short-circuits the unforced path.
    import time

    assembler._last_persist_at = time.time()

    assembler.persist(force=False)

    assert saves == []


# ---------------------------------------------------------------------------
# misc invariants
# ---------------------------------------------------------------------------


def test_assembler_holds_report_by_reference() -> None:
    """The assembler must mutate the same ActivationReport the facade owns.

    This is the crucial invariant that lets the W11-1 facade pin file's
    bound-method-identity assertions still describe a meaningful wiring:
    the runtime, the facade, and the assembler all see the same report.
    """

    report = ActivationReport(target_extension_id="publisher.tool")
    assembler = ReportAssembler(report=report, report_path=None)

    assert assembler._report is report


def test_assembler_init_sets_last_persist_at_to_zero() -> None:
    report = ActivationReport(target_extension_id="publisher.tool")
    assembler = ReportAssembler(report=report, report_path=None)

    assert assembler._last_persist_at == 0.0


@pytest.mark.parametrize("explicit_path", [None, Path("relative/report.json")])
def test_assembler_accepts_optional_report_path(
    explicit_path: Path | None,
) -> None:
    report = ActivationReport(target_extension_id="publisher.tool")
    assembler = ReportAssembler(report=report, report_path=explicit_path)

    assert assembler._report_path == explicit_path
