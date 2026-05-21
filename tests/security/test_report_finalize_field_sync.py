"""W16-3 closure for [FOLLOWUP report-finalize-top-level-field-sync-drift].

Surfaced during W14-3 post-pull production scan review on ``week14``:

* UI-launched scan
  ``activation_report_ms-python.python-2026.5.2026051301-c71107e2ff84.json``
  (``2026-05-13`` 15:36) carried ``null`` for several top-level
  ``ActivationReport`` fields even when the underlying evidence was
  present in the same payload: ``target_extension_id``,
  ``monitoring_start`` / ``monitoring_end``, ``scenarios_run`` (despite
  ``scenario_traces`` being filled), and ``harness_handshake_required``
  (despite ``setup_monitor`` stamping ``True`` at
  ``executor/flows/playwright/entrypoint/dispatch.py:137``).
* The pre-W14 W13 close-out smoke scan
  ``activation_report_ms-python.python-2026.5.2026050801-9d327b30b60f.json``
  (``2026-05-13`` 00:46) exhibits the same nulls, so this is **not a W14
  regression** — it is a finalize / ``report.save()`` drift that has
  been present at least since the W13 close-out.

**Root cause (located W16-3, 2026-05-18).** The five analyst-facing
top-level scalars existed on the in-memory ``ActivationReport`` dataclass
(``executor/flows/playwright/monitor/types.py``) but had **no slot on
the strict-forbid contract**
(``packages/analysis_contracts/contracts.ActivationReport`` —
``StrictContractModel`` with ``extra='forbid'``). The save path in
``executor/flows/playwright/report_builder.save_report_payload`` parses
the build output through ``_validate_report_against_contract`` and
persists ``parsed.model_dump(mode='json')``; any field not on the
contract was silently dropped at validation time, surfacing as a missing
key (or, for some readers, a defaulted ``null``) in the persisted JSON.

**W16-3 fix.** Two paired additions land together:

1. ``packages/analysis_contracts/contracts.ActivationReport`` adds five
   additive-optional fields (``target_extension_id``,
   ``monitoring_start``, ``monitoring_end``, ``scenarios_run``,
   ``harness_handshake_required``) with defaults that match the
   in-memory dataclass defaults so legacy fixtures keep validating.
   Schema version stays at ``2.1`` — same precedent as the W14-5
   ``executor_fingerprint`` extension.
2. ``executor/flows/playwright/report_builder.build_report_data``
   populates the five new keys from the live report on every write
   (with explicit ``float()`` / ``list()`` / ``bool()`` coercions so a
   future writer that drifts a value to ``None`` cannot re-introduce
   the null leak).

This module pins the contract round-trip directly: build a populated
``ActivationReport``, call ``save()`` to a temp path, re-read the
persisted JSON, and assert all five fields survive with their typed
values. No ``ExtensionMonitor.start()``/``stop()`` lifecycle harness
is needed — the save path is what was dropping the values, and the
save path is testable in isolation. The pre-W16-3 RED stub
``xfail``-marked itself against a hypothetical heavier harness; W16-3
discovered the root cause at the contract seam and replaced the stub
with the round-trip pin.

Note on the second W14 production observation
(``attribution_summary.target_activation_count`` stream-derived vs
evidence-kind-count mismatch from ``2026-05-14``): that drift is in a
*different* code path (``build_signal_summary`` + ``attribution_summary``
producer side) and is out of scope for W16-3. The
``[FOLLOWUP attribution-count-parity]`` follow-up captures the
remaining work — see ``documents/POST_POC_BACKLOG.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

from executor.flows.playwright.monitor.records import ScenarioTrace
from executor.flows.playwright.monitor.types import ActivationReport


def _populated_report() -> ActivationReport:
    """Build an ``ActivationReport`` with all five W16-3 fields populated.

    Mirrors what ``MonitorRuntime.start()`` (monitoring_start /
    monitoring_started_monotonic), ``MonitorRuntime.stop()``
    (monitoring_end / monitoring_ended_monotonic), and
    ``dispatch.setup_monitor`` (harness_handshake_required=True,
    target_extension_id from the CLI) collectively stamp on a real
    monitored run, plus a scenario_trace so the derived
    ``scenarios_run`` list is non-empty.
    """
    report = ActivationReport(target_extension_id="publisher.tool")
    report.monitoring_start = 1700_000_000.0
    report.monitoring_end = 1700_000_050.0
    report.harness_handshake_required = True
    report.scenario_traces = [
        ScenarioTrace(
            name="coding_session", started_at=1700_000_001.0, status="completed"
        ),
        ScenarioTrace(
            name="debug_session", started_at=1700_000_020.0, status="completed"
        ),
    ]
    # ``_synchronize_scenario_truth`` is what derives ``scenarios_run``
    # from ``scenario_traces`` on the live path. The lifecycle harness
    # invokes it via ``record_scenario_event`` / ``record_failed_scenarios``
    # / ``finalize_running_scenarios``; here we set the derived field
    # directly so the test stays decoupled from the accountant.
    report.scenarios_run = ["coding_session", "debug_session"]
    return report


def test_save_persists_target_extension_id_top_level(tmp_path: Path) -> None:
    """``target_extension_id`` survives the strict-forbid contract round-trip."""
    report = _populated_report()
    out = tmp_path / "report.json"

    report.save(out, announce=False)
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert payload["target_extension_id"] == "publisher.tool"
    # Sanity: the pre-existing alias also stays populated so analysts
    # reading either name see the same value.
    assert payload["target_extension_expected"] == "publisher.tool"


def test_save_persists_monitoring_start_end_top_level(tmp_path: Path) -> None:
    """``monitoring_start`` / ``monitoring_end`` survive as non-null floats."""
    report = _populated_report()
    out = tmp_path / "report.json"

    report.save(out, announce=False)
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert payload["monitoring_start"] == 1700_000_000.0
    assert payload["monitoring_end"] == 1700_000_050.0
    # Neither field is ``None`` in the persisted JSON — the explicit
    # ``float()`` coercion in ``build_report_data`` guards against a
    # future writer accidentally drifting the value to ``None``.
    assert payload["monitoring_start"] is not None
    assert payload["monitoring_end"] is not None


def test_save_persists_scenarios_run_derived_list(tmp_path: Path) -> None:
    """``scenarios_run`` survives as a list (not ``null``) and preserves order."""
    report = _populated_report()
    out = tmp_path / "report.json"

    report.save(out, announce=False)
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert payload["scenarios_run"] == ["coding_session", "debug_session"]


def test_save_persists_harness_handshake_required_flag(tmp_path: Path) -> None:
    """``harness_handshake_required`` survives as a literal ``True`` (not ``null``)."""
    report = _populated_report()
    out = tmp_path / "report.json"

    report.save(out, announce=False)
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert payload["harness_handshake_required"] is True


def test_save_defaults_preserve_legacy_fixture_shape(tmp_path: Path) -> None:
    """An empty ``ActivationReport`` round-trips with the five W16-3 defaults.

    Legacy fixtures (and any callsite that constructs ``ActivationReport``
    without stamping the new fields) MUST keep validating against the
    strict-forbid contract. The defaults match the in-memory dataclass
    defaults: empty string / ``0.0`` / ``[]`` / ``False``.
    """
    report = ActivationReport(target_extension_id="")
    out = tmp_path / "report.json"

    report.save(out, announce=False)
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert payload["target_extension_id"] == ""
    assert payload["monitoring_start"] == 0.0
    assert payload["monitoring_end"] == 0.0
    assert payload["scenarios_run"] == []
    assert payload["harness_handshake_required"] is False
