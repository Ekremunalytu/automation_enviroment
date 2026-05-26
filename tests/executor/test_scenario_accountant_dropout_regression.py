"""W19-1 — Regression fixture for the unaccounted_dropout class.

Originally landed at commit `6a21cf3` (W19-1 primary) as a RED
xfail/strict fixture against the pre-fix live-run shape captured at
W19-0 baseline (Codex live-run 2026-05-21 of `ms-python.python @
992ad028f3df`). W19-2 (`89b64da`) landed the upstream emit-site
fix at `executor/flows/playwright/stimulus/passes.py` (layered-passes
reconciliation now emits a classified `covered_via_layered_attempts`
reason_code for scenarios whose declared activation events were
attempted via `extra:` / `command:` actions but whose handler was
not directly invoked under this execution mode), regenerated the
slim baseline JSON to the post-fix shape (initially synthesized),
removed the xfail markers, and narrowed the whitelist to the single
new reason_code. W19-2-followup-2 re-anchored the slim baseline JSON
from synthesized to live-lifted from
`activation_report_ms-python.python-2026.5.2026052501-c2bf28ca9506.json`
(sha256 `e9e60b2e42...`) — a UI-driven analyze API re-run at
2026-05-25 22:23 confirmed Hat-1 GREEN
(`unaccounted_dropout` count = 0; 16 of 16 key fields byte-identical
with the pre-fix anchor except the W19-2 reason_code).

Symptom-only / root-cause-blind: asserts the surface shape (no
scenario reaches the analyst with `reason_code="unaccounted_dropout"`;
both `debug_session` + `refactor_workflow` surface with the W19-2
classification) without reaching into the upstream mechanism. The
mechanism is independently pinned by synthetic unit tests at
`tests/security/test_scenario_dropout_repro.py`
(`test_layered_attempts_coverage_emits_specific_reason_code` +
`test_layered_attempts_coverage_pre_recorded_reason_wins`).

See `documents/active-work/W19-live-run-root-cause.md` for the W19-1
+ W19-2 + W19-2-followup-2 Per-Item Detail blocks and the live
Hat-1 GREEN gate satisfaction record.
"""

from __future__ import annotations

import json
import re
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


# Lowercase 64-char hex — the canonical sha256 form produced by
# `shasum -a 256`. Any future fixture re-anchor MUST populate the
# `_meta.source_sha256` field with a hash in this shape so that
# downstream auditors can re-verify the slim excerpt against its
# source JSON deterministically.
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def test_baseline_meta_source_sha256_is_canonical_hex() -> None:
    """W19-2-followup-2: the slim baseline excerpt's `_meta.source_sha256`
    MUST be a 64-char lowercase hex string (live-anchored shape).

    During the W19-2 primary landing window the fixture briefly carried
    a SYNTHESIZED placeholder string ('n/a — synthesized, not lifted
    from a live JSON') while the live re-run gate was deferred. The
    W19-2-followup-2 live re-anchor flipped the field to a real
    `shasum -a 256` hash. This invariant pin guards against silently
    regressing back to a placeholder (or any malformed value) on a
    future re-anchor — every re-lift must produce a verifiable hash
    against the source filename pinned alongside in `_meta.source_filename`
    and the sibling `.sha256` file.
    """
    baseline = _load_baseline()
    meta = baseline.get("_meta", {})
    source_sha256 = meta.get("source_sha256", "")
    assert _SHA256_RE.match(source_sha256), (
        "_meta.source_sha256 must be 64-char lowercase hex (a live "
        f"`shasum -a 256` hash); got {source_sha256!r}. If a placeholder "
        "is needed during a deferred-verification window, gate this test "
        "explicitly rather than letting the placeholder ride."
    )
    source_filename = meta.get("source_filename", "")
    assert source_filename and source_filename.endswith(".json"), (
        "_meta.source_filename must name a real activation_report_*.json; "
        f"got {source_filename!r}."
    )
