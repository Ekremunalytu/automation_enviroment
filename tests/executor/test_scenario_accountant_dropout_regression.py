"""W19-1 — RED regression fixture for the unaccounted_dropout class.

Pins the live-run dropout shape observed `2026-05-21` against
`ms-python.python @ 992ad028f3df`. Symptom-only / root-cause-blind:
asserts the surface shape (no scenario should reach the analyst with
`reason_code="unaccounted_dropout"` — the upstream emit-site must
classify it) without prescribing the upstream fix-site.

Strict xfail semantics: W19-2 lands the emit-site fix and regenerates
the slim baseline fixture (`w19_baseline_ms_python_python.json`) from
a fresh analyze API run. At that point these tests flip xfail → PASS;
strict mode turns an unexpected PASS into a CI break (the W19-2
self-stamp commit removes the xfail markers and narrows the
whitelist to the new reason_code).

See `documents/active-work/W19-live-run-root-cause.md` for the W19-1
Per-Item Detail block and the canonical baseline JSON source SHA256
(also pinned in `fixtures/activation_reports/*.sha256`).
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

# W19-1 broad whitelist; W19-2 narrows to the single new reason_code
# emitted by the chosen upstream fix-site. Members below are the
# already-classified reason codes the codebase emits today —
# `unaccounted_dropout` is intentionally absent (it is the fallback
# this regression fixture forbids).
_W19_1_ACCEPTABLE_REASONS = frozenset(
    {
        "dependency_missing",
        "trigger_timeout",
        "precondition_unmet",
        "not_executed",
        "harness_unavailable",
        "dispatch_outcome_none",
        "aborted_after_fatal_ui_crash",
    }
)


def _load_baseline() -> dict:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.xfail(
    strict=True,
    reason="W19-2 emit-site fix bekleniyor; W19-1 RED fixture",
)
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
    assert record["reason_code"] in _W19_1_ACCEPTABLE_REASONS, (
        f"{scenario_name} beklenmedik reason_code: "
        f"{record['reason_code']!r} (whitelist: "
        f"{sorted(_W19_1_ACCEPTABLE_REASONS)})"
    )


@pytest.mark.xfail(
    strict=True,
    reason="W19-2 emit-site fix bekleniyor; W19-1 RED fixture",
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
