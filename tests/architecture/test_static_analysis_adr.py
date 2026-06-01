"""ES-0 static-analysis pre-check ADR existence + content invariants (ADR 0016).

Pins the four locked design decisions recorded in
`documents/adrs/0016-static-analysis-pre-check-stage.md` so the
ES-1..ES-5 implementation sub-iters all inherit a stable, machine-
checkable contract. The design intent was recovered from the abandoned
`extrace-static` branch (frozen in
`documents/active-work/extrace-static-stream-handoff.md`); this gate
keeps the re-homed ADR from silently drifting or being deleted.

What's pinned:

1. The ADR 0016 file exists at the expected path so a future edit that
   removes or relocates it trips this gate before the dependent sub-iters
   build on a missing decision record.
2. The ADR 0016 body carries each locked decision's load-bearing tokens
   (block-and-warn + `rejected_static`, the hardened
   `automation_static_analyzer` envelope, schema-first, the in-house +
   Semgrep MVP, the `extrace.s2.typosquat` promoted blocker) so weakening
   any of the four would force an ADR amendment here.
3. The ADR 0016 body cites the frozen handoff as Source and enumerates
   the ES-0..ES-5 roadmap so future iters cannot strip the trail.

What's intentionally NOT pinned here:

- The implementation details (contract field sets, container compose
  keys, rule bodies, Semgrep ruleset) land with their own dedicated
  tests in ES-1..ES-5.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_PATH = REPO_ROOT / "documents" / "adrs" / "0016-static-analysis-pre-check-stage.md"


def test_adr_0016_exists() -> None:
    """ADR 0016 must remain at the expected path so the static-analysis
    pre-check sub-iters (ES-1..ES-5) have a documented source-of-truth
    for the four locked design decisions.
    """
    assert ADR_PATH.exists(), (
        f"ADR 0016 not found at {ADR_PATH.relative_to(REPO_ROOT)}. "
        "The Static Analysis Pre-Check Stream depends on the decisions "
        "recorded here — restore the ADR before re-running."
    )


def test_adr_0016_documents_locked_decisions() -> None:
    """ADR 0016 must explicitly carry the four locked decisions' tokens,
    the handoff Source cross-reference, and the ES-0..ES-5 roadmap so a
    future scope flip surfaces here alongside the implementation sub-iters.
    """
    text = ADR_PATH.read_text(encoding="utf-8")
    required_tokens = (
        # Decision 1 — block-and-warn semantics.
        "Block-and-warn",
        "rejected_static",
        "_PROMOTED_HIGH_BLOCKERS",
        "extrace.s2.typosquat",
        # Decision 2 — separate hardened container + envelope.
        "automation_static_analyzer",
        "network_mode",
        "cap_drop",
        "no-new-privileges",
        # Decision 3 — schema-first.
        "Schema-first",
        # Decision 4 — in-house rules + Semgrep MVP.
        "Semgrep",
        # Roadmap + regression-mitigation traceability.
        "ES-0",
        "ES-1",
        "ES-3b",
        "ES-5",
        # Source + related promotion.
        "extrace-static-stream-handoff.md",
        "ADR 0002",
        "ADR 0013",
    )
    missing = [token for token in required_tokens if token not in text]
    assert not missing, (
        "ADR 0016 must carry the four locked decisions + the handoff "
        "Source + the ES-0..ES-5 roadmap so the implementation sub-iters "
        f"inherit a stable contract. Missing tokens: {missing!r}."
    )
