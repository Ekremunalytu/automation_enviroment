"""Canonical preamble parity gate.

The 10 current canonical preamble docs all carry a ``Last Updated: ...``
backtick banner summarizing the most recently merged phase. This gate pins
the current most-recent-merge fingerprint across every current canonical
preamble and follows the active weekly tracker as the phase changes.

To advance the fingerprint after the next merge:
  - Update ``_EXPECTED_MERGE_FINGERPRINT`` below to the new
    most-recent-merge string.
  - Update the canonical docs' headlines in the same commit set.
  - Update ``_CANONICAL_PREAMBLE_DOCS`` if the active weekly tracker changes.
  - The test should pass green only after both docs and pins are aligned.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_CANONICAL_PREAMBLE_DOCS: tuple[str, ...] = (
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    "documents/AGENT_CONTEXT.md",
    "documents/REFACTOR_STATUS.md",
    "documents/REFACTOR_OPTIMIZATION.md",
    "documents/POST_POC_BACKLOG.md",
    "documents/active-work/README.md",
    "documents/active-work/W18-W22-roadmap.md",
    "documents/active-work/W21-coverage-promotion-mid-tier.md",
)

# Most-recent-merge fingerprint pinned after W20 close-out
# (PR #29 ``week20 -> main`` MERGED 2026-05-26 via ``64a3c3d``).
# Bump this when the next phase merges; bump every current canonical
# doc headline in the same commit.
_EXPECTED_MERGE_FINGERPRINT = "PR #29"
_EXPECTED_MERGE_SHA = "64a3c3d"

# Drift markers — phrases that mean the preamble is stale relative to
# the current merge fingerprint. If any of these reappear in the
# *headline region* of a canonical doc, the next-phase merge happened
# without a corresponding preamble refresh. Body-level audit-trail
# mentions of these phrases (e.g., describing what W20-0 doc-reconcile
# flipped) are historical narrative and not flagged here.
#
# Lowercase ``pending user approval`` catches stale in-banner "PR pending"
# claims authored before a merge. Current pre-merge W21 PR-readiness uses
# uppercase ``PENDING USER APPROVAL`` deliberately; the case-sensitive match
# avoids flagging that forward-looking W21 state.
_STALE_MARKERS: tuple[str, ...] = (
    "pending user approval",
    "Active phase: W19",
)

# Number of lines from the top of each doc to scan for the stale markers.
# This covers the ``Last Updated: ...`` backtick banner plus the
# top-of-file Operating Rules / Status block where the present-tense
# phase claim lives. Audit-trail mentions appear deeper in the body.
_HEADLINE_SCAN_LINES = 200


def test_all_canonical_preamble_docs_carry_merge_fingerprint() -> None:
    """Every canonical preamble doc must reference the current most-recent-merge PR + SHA."""
    missing_fingerprint: list[str] = []
    missing_sha: list[str] = []
    for relative_path in _CANONICAL_PREAMBLE_DOCS:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        if _EXPECTED_MERGE_FINGERPRINT not in text:
            missing_fingerprint.append(relative_path)
        if _EXPECTED_MERGE_SHA not in text:
            missing_sha.append(relative_path)
    assert not missing_fingerprint, (
        f"These canonical preamble docs are missing the current merge "
        f"fingerprint ({_EXPECTED_MERGE_FINGERPRINT!r}): {missing_fingerprint}. "
        f"Either the doc drifted, or the next phase merged without "
        f"refreshing its banner — update both the doc and "
        f"`_EXPECTED_MERGE_FINGERPRINT` in this test together."
    )
    assert not missing_sha, (
        f"These canonical preamble docs are missing the current merge SHA "
        f"({_EXPECTED_MERGE_SHA!r}): {missing_sha}. Update both the doc and "
        f"`_EXPECTED_MERGE_SHA` in this test together."
    )


def test_no_canonical_preamble_doc_carries_stale_markers() -> None:
    """Headline region of each canonical doc must not carry stale "PR pending" / "Active phase: W19" claims."""
    offenders: list[str] = []
    for relative_path in _CANONICAL_PREAMBLE_DOCS:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        headline_region = "\n".join(text.splitlines()[:_HEADLINE_SCAN_LINES])
        for marker in _STALE_MARKERS:
            if marker in headline_region:
                offenders.append(f"  {relative_path}: contains {marker!r}")
    assert not offenders, (
        "Canonical preamble drift detected (stale markers found):\n"
        + "\n".join(offenders)
        + "\n\nThe most recent phase merge happened without refreshing the "
        "preamble. Flip these markers to their post-merge equivalents in "
        "the same PR that merged the phase, or as a follow-up doc-only "
        "commit if you've discovered drift post-merge."
    )


def test_all_canonical_preamble_doc_paths_exist() -> None:
    """Sanity guard: every entry in ``_CANONICAL_PREAMBLE_DOCS`` must point to a real file.

    If a future refactor renames or moves one of these docs without
    updating this test, the other gates above would silently pass with
    empty content for the missing file. This guard catches that drift.
    """
    missing = [
        relative_path
        for relative_path in _CANONICAL_PREAMBLE_DOCS
        if not (REPO_ROOT / relative_path).is_file()
    ]
    assert not missing, (
        f"Canonical preamble doc paths no longer exist: {missing}. "
        "Update `_CANONICAL_PREAMBLE_DOCS` to match the rename/move."
    )
