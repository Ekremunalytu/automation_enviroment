"""W15+ RED stub for [FOLLOWUP report-finalize-top-level-field-sync-drift].

Surfaced during W14-3 post-pull production scan review on `week14`:

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

The same-scan UI flow is unaffected because it consumes the derived
``automation_health`` block (which populates correctly: ``status``,
``target_activation_count``, ``skipped_scenarios`` are all present).
Downstream analyzers that read the top-level fields directly are the
blocked surface; closing this is W15+ work.

This module is a placeholder RED stub. A real reproducer needs to drive
``ExtensionMonitor.start()`` → ``stop()`` → ``report.save()`` so the
finalize / save-out synchronization seam is exercised, which in turn
requires a heavier test harness than what is currently scoped (real
``Playwright.Page`` mock, harness secret staging, etc.). When the W15+
fix lands under
`[FOLLOWUP report-finalize-top-level-field-sync-drift]`
(`documents/POST_POC_BACKLOG.md` Contracts / Reports / Detection),
replace the ``xfail``-marked stub below with the real lifecycle
reproducer asserting every top-level field survives ``report.save()``.

The ``xfail`` marker keeps CI green until the lifecycle harness is
authored; on landing the stub flips to ``XPASS`` (assertion via the
real lifecycle) and the marker can be stripped.
"""

from __future__ import annotations

import pytest


@pytest.mark.xfail(
    strict=False,
    reason=(
        "W15+ FOLLOWUP report-finalize-top-level-field-sync-drift; "
        "real reproducer needs an ExtensionMonitor.start()/stop()/save() "
        "lifecycle harness. See POST_POC_BACKLOG.md Contracts / Reports / "
        "Detection for the backlog hand-off."
    ),
)
def test_extension_monitor_finalize_populates_top_level_fields() -> None:
    """W15+ placeholder.

    Real reproducer (post-fix) will:
    1. Construct an ``ExtensionMonitor`` against a synthetic Playwright
       page mock.
    2. Stage a harness secret + drive ``setup_monitor`` so
       ``harness_handshake_required`` is flagged ``True``.
    3. Start monitoring, record at least two completed scenarios, stop
       monitoring, and call ``mon.stop()`` → ``report.save()``.
    4. Re-load the persisted JSON and assert every top-level field
       survived:
       - ``target_extension_id`` populated.
       - ``monitoring_start`` / ``monitoring_end`` are non-null floats.
       - ``scenarios_run`` derived from ``scenario_traces`` via
         ``_synchronize_scenario_truth``.
       - ``harness_handshake_required`` is ``True`` (not ``null``).

    Until the lifecycle harness lands this stub raises so the ``xfail``
    marker records the test as expected-failure rather than skipped.
    """
    raise NotImplementedError(
        "W15+ RED stub: ExtensionMonitor lifecycle harness pending under "
        "[FOLLOWUP report-finalize-top-level-field-sync-drift]."
    )
