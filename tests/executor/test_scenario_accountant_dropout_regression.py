"""W19-1 — Regression fixture for the unaccounted_dropout class.

Originally landed at commit `6a21cf3` (W19-1 primary) as a RED
xfail/strict fixture against the pre-fix live-run shape captured at
W19-0 baseline (Codex live-run 2026-05-21 of `ms-python.python @
992ad028f3df`). W19-2 (`<W19-2-primary-SHA>`) landed the upstream
emit-site fix at `executor/flows/playwright/stimulus/passes.py`
(layered-passes reconciliation now emits a classified
`covered_via_layered_attempts` reason_code for scenarios whose
declared activation events were attempted via `extra:` / `command:`
actions but whose handler was not directly invoked under this
execution mode), regenerated the slim baseline JSON to the post-fix
shape, removed the xfail markers, and narrowed the whitelist to the
single new reason_code.

Symptom-only / root-cause-blind: asserts the surface shape (no
scenario reaches the analyst with `reason_code="unaccounted_dropout"`;
both `debug_session` + `refactor_workflow` surface with the W19-2
classification) without reaching into the upstream mechanism. The
mechanism is independently pinned by synthetic unit tests at
`tests/security/test_scenario_dropout_repro.py`
(`test_layered_attempts_coverage_emits_specific_reason_code` +
`test_layered_attempts_coverage_pre_recorded_reason_wins`).

See `documents/active-work/W19-live-run-root-cause.md` for the W19-1
+ W19-2 Per-Item Detail blocks and the baseline JSON synthesis note
(live re-run verification deferred to W19-6 close-out; tracked
inline in `_meta.synthesis_note` of the fixture JSON).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "activation_reports"
    / "w19_baseline_ms_python_python.json"
)

# W19-2 narrowed whitelist (post-fix): only the single new reason_code
# emitted by the upstream fix-site at
# ``executor/flows/playwright/stimulus/passes.py`` covered_only branch.
# `unaccounted_dropout` is intentionally absent (it is the accountant
# fallback this regression fixture forbids).
_W19_2_ACCEPTABLE_REASONS = frozenset({"covered_via_layered_attempts"})


def _load_baseline() -> dict:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("scenario_name", ["debug_session", "refactor_workflow"])
def test_scenario_not_marked_unaccounted_dropout(scenario_name: str) -> None:
    baseline = _load_baseline()
    by_name = {entry["name"]: entry for entry in baseline["skipped_scenarios"]}
    record = by_name.get(scenario_name)
    assert record is not None, (
        f"{scenario_name} skipped_scenarios içinde değil (baseline shape drift?)"
    )
    assert record["reason_code"] != "unaccounted_dropout", (
        f"{scenario_name} hâlâ son-mil fallback "
        f"({record['reason_code']!r}); upstream emit-site fix bekleniyor"
    )
    assert record["reason_code"] in _W19_2_ACCEPTABLE_REASONS, (
        f"{scenario_name} beklenmedik reason_code: "
        f"{record['reason_code']!r} (whitelist: "
        f"{sorted(_W19_2_ACCEPTABLE_REASONS)})"
    )


def test_aggregate_unaccounted_dropout_is_zero() -> None:
    baseline = _load_baseline()
    dropout_count = sum(
        1
        for entry in baseline["skipped_scenarios"]
        if entry.get("reason_code") == "unaccounted_dropout"
    )
    assert dropout_count == 0, (
        f"{dropout_count} senaryo hâlâ son-mil fallback ile yüzeyleniyor "
        f"(baseline shape: "
        f"{[e['name'] for e in baseline['skipped_scenarios']]})"
    )
