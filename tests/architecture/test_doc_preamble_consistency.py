"""Architecture gate: canonical doc preambles must report a consistent current phase.

After a close-out PR merges to ``main``, every canonical doc preamble must
be bumped to reflect the new active phase. The W14 -> W15 transition
surfaced the drift this gate prevents: six canonical docs (``CLAUDE.md``,
``AGENTS.md``, ``documents/AGENT_CONTEXT.md``,
``documents/REFACTOR_STATUS.md``, ``documents/POST_POC_BACKLOG.md``,
``documents/REFACTOR_OPTIMIZATION.md``) all still claimed "W14 active" /
"close-out PR week14 -> main next" two days after PR #21
(``week14 -> main``) merged on ``2026-05-14``, because the preamble
refresh was tracked under W15-7 and had not yet been pulled. The W15
mid-iter hygiene pass on ``2026-05-16`` refreshed all six preambles
together and added this gate to lock the invariant.

The gate parses each doc's preamble (the first ten lines, covering the
backtick-quoted ``Last Updated: ...`` block) and asserts:

  1. Every preamble carries at least one current-phase signal (a ``W<N>``
     phase, or the active named stream from ``documents/phase.json`` when
     one is open).
  2. No single preamble reports two different current phases internally
     (e.g., "W14 active" and "W15 active" both present).
  3. Every doc agrees on the same ``W<N>`` as the current phase.
  4. The agreed ``W<N>`` matches ``documents/phase.json`` ->
     ``last_merged_weekly`` (the single source).

Patterns matched: ``W<N> active``, ``W<N> [fully] closed synthetically``
(W19-6-followup-2 added the closed-but-not-merged lifecycle state for the
pre-merge hygiene window between W<N>-final close-out and the
``weekN -> main`` PR merge), ``Last merged weekly: W<N>``,
``Active phase: W<N>``,
``Active phase: **W<N>**``, ``Active phase is W<N>``,
``Active phase is **W<N>**``. The check is read-only and does not
require Docker or a running test environment.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.architecture._phase_manifest import load_manifest, phase_number

REPO_ROOT = Path(__file__).resolve().parents[2]

_MANIFEST = load_manifest()
_ACTIVE_STREAM = _MANIFEST["active_stream"]
_ACTIVE_STREAM_ID = (
    str(_ACTIVE_STREAM["id"]) if isinstance(_ACTIVE_STREAM, dict) else None
)
_EXPECTED_WEEKLY_PHASE = phase_number(_MANIFEST["last_merged_weekly"])
_STREAM_SIGNAL = (
    re.compile(rf"\b{re.escape(_ACTIVE_STREAM_ID)}\b", re.IGNORECASE)
    if _ACTIVE_STREAM_ID
    else None
)

CANONICAL_DOCS = (
    REPO_ROOT / "CLAUDE.md",
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "documents" / "AGENT_CONTEXT.md",
    REPO_ROOT / "documents" / "REFACTOR_STATUS.md",
    REPO_ROOT / "documents" / "POST_POC_BACKLOG.md",
    REPO_ROOT / "documents" / "REFACTOR_OPTIMIZATION.md",
    REPO_ROOT / "documents" / "README.md",
)

_PREAMBLE_LINE_LIMIT = 10

_ACTIVE_PHASE_PATTERNS = (
    re.compile(r"\bW(?P<n>\d+)\s+active\b", re.IGNORECASE),
    re.compile(r"\bLast\s+merged\s+weekly:\s*W(?P<n>\d+)\b", re.IGNORECASE),
    re.compile(
        r"\bW(?P<n>\d+)\s+(?:fully\s+)?closed\s+synthetically\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"Active\s+phase(?:\s+is)?[:\s\*]+W(?P<n>\d+)",
        re.IGNORECASE,
    ),
)


def _read_preamble(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()[:_PREAMBLE_LINE_LIMIT]
    return "\n".join(lines)


def _extract_active_phases(preamble: str) -> set[int]:
    found: set[int] = set()
    for pat in _ACTIVE_PHASE_PATTERNS:
        for match in pat.finditer(preamble):
            found.add(int(match.group("n")))
    return found


def test_canonical_doc_preambles_agree_on_active_phase() -> None:
    """Every canonical doc preamble must claim the same W<N> as active.

    Drift class: after a close-out PR merges to ``main``, all six
    preambles must be refreshed together. If any doc lags (still
    claiming the previous phase), this gate fails before the next
    iteration's work builds on a misleading truth-state.
    """
    missing_files = [
        str(p.relative_to(REPO_ROOT)) for p in CANONICAL_DOCS if not p.exists()
    ]
    assert not missing_files, (
        f"Canonical doc paths in CANONICAL_DOCS do not exist on disk: "
        f"{missing_files}. Update the tuple to reflect renames/moves."
    )

    preambles: dict[Path, str] = {path: _read_preamble(path) for path in CANONICAL_DOCS}
    per_doc_phases: dict[Path, set[int]] = {
        path: _extract_active_phases(text) for path, text in preambles.items()
    }

    # A doc with no ``W<N>`` signal is tolerated only when a named stream is
    # open and the doc names it (``phase.json`` -> ``active_stream.id``).
    # When ``active_stream`` is null, every preamble must carry the weekly
    # pointer instead.
    missing_signal = [
        str(p.relative_to(REPO_ROOT))
        for p, phases in per_doc_phases.items()
        if not phases and not (_STREAM_SIGNAL and _STREAM_SIGNAL.search(preambles[p]))
    ]
    expected_signal = (
        f"'Active phase: W<N>' (or the active stream {_ACTIVE_STREAM_ID!r})"
        if _ACTIVE_STREAM_ID
        else "'Active phase: W<N>' (no named stream is currently open)"
    )
    assert not missing_signal, (
        f"Preamble missing an active-phase signal: {missing_signal}. "
        "Every canonical doc preamble must mention 'W<N> active' / "
        f"{expected_signal} "
        "so this gate can validate consistency."
    )

    internally_inconsistent = {
        str(p.relative_to(REPO_ROOT)): sorted(phases)
        for p, phases in per_doc_phases.items()
        if len(phases) > 1
    }
    assert not internally_inconsistent, (
        f"Preamble reports conflicting active phases internally: "
        f"{internally_inconsistent}. Fix the offending preamble — an "
        "internal conflict means the doc itself is inconsistent."
    )

    # Weekly-phase agreement: every doc that carries a ``W<N>`` signal must
    # claim the same one (stream-only docs are skipped — tolerated above).
    distinct: dict[int, list[str]] = {}
    for path, phases in per_doc_phases.items():
        if len(phases) != 1:
            continue
        (phase,) = phases
        distinct.setdefault(phase, []).append(str(path.relative_to(REPO_ROOT)))

    if len(distinct) > 1:
        details = "\n".join(
            f"  W{n}: " + ", ".join(sorted(docs))
            for n, docs in sorted(distinct.items())
        )
        pytest.fail(
            "Canonical doc preambles disagree on the active phase:\n"
            + details
            + "\n\nAfter a close-out PR merges, every canonical doc's "
            "preamble must be bumped together — see the W15 mid-iter "
            "hygiene pass `2026-05-16` for the precedent."
        )

    # Cross-check the docs' agreed weekly phase against the single source
    # (``documents/phase.json`` -> ``last_merged_weekly``), so a phase.json
    # bump without a doc refresh (or vice-versa) fails here.
    if len(distinct) == 1:
        (agreed_phase,) = distinct
        assert agreed_phase == _EXPECTED_WEEKLY_PHASE, (
            f"Canonical doc preambles agree on W{agreed_phase} but "
            f"documents/phase.json last_merged_weekly is "
            f"W{_EXPECTED_WEEKLY_PHASE}. Align phase.json and the doc "
            "banners in the same commit."
        )
