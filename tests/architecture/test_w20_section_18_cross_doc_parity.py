"""W20 §18 cross-doc parity gate.

The W20 sub-iter audit trail and live-run anchor evidence must remain
consistent across the three docs that explicitly track W20 status:
the W20 active tracker, ``REFACTOR_OPTIMIZATION.md`` §18 (plan source),
and ``POST_POC_BACKLOG.md`` W20 Pull-Forward Acceptance Bar.

Mirrors the W19-6-followup-2 paterni at
``tests/architecture/test_canonical_preamble_parity.py`` but targets
the W20 sub-iter slate specifically rather than the most-recent-merge
fingerprint. When a future sub-iter (W20-5, then post-merge audit)
adds new SHAs, this test's constants advance in the same commit.
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


# W20 sub-iter audit trail: primary + self-stamp commit SHAs.
# These must appear verbatim in the W20 tracker (single source of truth).
_W20_FULL_AUDIT_SHAS: tuple[str, ...] = (
    "66a8a0b",  # W20-0 primary (doc-reconcile)
    "5f13757",  # W20-0 self-stamp (baseline live-run captured)
    "82276cb",  # W20-1 primary (scm flip)
    "a17e595",  # W20-1 self-stamp
    "a4343d2",  # W20-2 primary (settings flip)
    "7406588",  # W20-2 self-stamp
    "d4c03b6",  # W20-3 primary (coverage matrix invariants)
    "2e39230",  # W20-3 self-stamp
    "05f47f3",  # W20-4 primary (DESIGN doc)
    "b409894",  # W20-4 self-stamp
)


# Primary commit SHAs subset — must appear in §18 + POST_POC_BACKLOG
# (those docs traditionally list primaries; self-stamps land later as
# tracker freezes). The W20 close-out commit may extend these to include
# self-stamps; advance the constant in the same commit if so.
_W20_PRIMARY_SHAS: tuple[str, ...] = (
    "66a8a0b",
    "82276cb",
    "a4343d2",
    "d4c03b6",
    "05f47f3",
)


# W20-0 baseline live-run anchor — pinned at the W20-0 self-stamp
# commit, must remain in the tracker through close-out (audit evidence
# of the baseline that gates the W20-1/W20-2 acceptance).
_W20_BASELINE_ANCHOR_FILENAME = "e89a82ca9ba8"
_W20_BASELINE_ANCHOR_SHA256 = (
    "4dd788268f7793143351721875d6ccb340bd1e01b2b0205c53a5561ed0256ffe"
)


_W20_TRACKER_PATH = "documents/active-work/W20-coverage-promotion-easy-wins.md"
_REFACTOR_OPT_PATH = "documents/REFACTOR_OPTIMIZATION.md"
_POST_POC_BACKLOG_PATH = "documents/POST_POC_BACKLOG.md"


@pytest.mark.parametrize("sha", _W20_FULL_AUDIT_SHAS)
def test_w20_tracker_contains_full_audit_trail(sha: str) -> None:
    """The W20 tracker must contain every W20 sub-iter primary AND
    self-stamp SHA verbatim.

    Each sub-iter lands a primary + self-stamp pair; the self-stamp
    flips the tracker row from `planned → closed via this commit`. At
    close-out, the placeholder ``this commit`` becomes the explicit
    SHA — that backfill is what pins the audit trail to the tracker.
    """
    text = (REPO_ROOT / _W20_TRACKER_PATH).read_text(encoding="utf-8")
    assert sha in text, (
        f"W20 tracker {_W20_TRACKER_PATH!r} is missing sub-iter SHA "
        f"{sha!r}. If the sub-iter just landed, the self-stamp commit "
        f"forgot to backfill `this commit` to the explicit SHA."
    )


@pytest.mark.parametrize("sha", _W20_PRIMARY_SHAS)
def test_section_18_contains_w20_primary_shas(sha: str) -> None:
    """``REFACTOR_OPTIMIZATION.md`` §18 must contain every W20 sub-iter
    primary commit SHA.

    §18 is the W20 plan source; sub-iter rows in §18.4 (Exit Criteria)
    and the per-iter audit cite the primary SHA at close-out. A
    primary SHA missing from §18 indicates an incomplete close-out
    or doc drift.
    """
    text = (REPO_ROOT / _REFACTOR_OPT_PATH).read_text(encoding="utf-8")
    assert sha in text, (
        f"{_REFACTOR_OPT_PATH!r} is missing W20 primary SHA {sha!r}. "
        f"The §18 self-stamp must list primary SHAs for every closed "
        f"W20 sub-iter."
    )


@pytest.mark.parametrize("sha", _W20_PRIMARY_SHAS)
def test_post_poc_backlog_contains_w20_primary_shas(sha: str) -> None:
    """``POST_POC_BACKLOG.md`` W20 Pull-Forward must contain every W20
    sub-iter primary commit SHA.

    The W20 Pull-Forward table tracks acceptance-bar closure. A primary
    SHA missing here means the closure row was never updated when the
    sub-iter landed.
    """
    text = (REPO_ROOT / _POST_POC_BACKLOG_PATH).read_text(encoding="utf-8")
    assert sha in text, (
        f"{_POST_POC_BACKLOG_PATH!r} is missing W20 primary SHA {sha!r}. "
        f"The W20 Pull-Forward Acceptance Bar row for this sub-iter "
        f"was never marked closed."
    )


def test_w20_baseline_anchor_filename_appears_in_tracker() -> None:
    """The W20-0 baseline live-run anchor filename short-SHA must
    appear in the W20 tracker.

    The W20-0 self-stamp commit pinned this anchor; a refactor that
    drops the filename token orphans the baseline evidence from the
    tracker narrative.
    """
    text = (REPO_ROOT / _W20_TRACKER_PATH).read_text(encoding="utf-8")
    assert _W20_BASELINE_ANCHOR_FILENAME in text, (
        f"W20 tracker missing baseline anchor filename "
        f"{_W20_BASELINE_ANCHOR_FILENAME!r}. The W20-0 self-stamp "
        f"commit pinned this anchor — preserve it through W20 "
        f"close-out and post-merge audit."
    )


def test_w20_baseline_anchor_sha256_appears_in_tracker() -> None:
    """The W20-0 baseline live-run JSON sha256 must appear in the
    W20 tracker — proves the live evidence still points at a
    fingerprinted artifact.
    """
    text = (REPO_ROOT / _W20_TRACKER_PATH).read_text(encoding="utf-8")
    assert _W20_BASELINE_ANCHOR_SHA256 in text, (
        f"W20 tracker missing baseline anchor sha256 "
        f"{_W20_BASELINE_ANCHOR_SHA256!r}. The W20-0 self-stamp commit "
        f"pinned this sha256; losing it severs the link from narrative "
        f"to the live JSON fingerprint."
    )


def test_w20_pull_forward_header_present_in_post_poc_backlog() -> None:
    """``POST_POC_BACKLOG.md`` must contain the ``W20 Pull-Forward
    Acceptance Bar`` section header.

    The section was promoted at W20-0 from the W20-W22 Roadmap
    Acceptance Bar (planning). Removing or renaming the section
    orphans the W20 closure tracking from POST_POC.
    """
    text = (REPO_ROOT / _POST_POC_BACKLOG_PATH).read_text(encoding="utf-8")
    assert "W20 Pull-Forward Acceptance Bar" in text, (
        f"{_POST_POC_BACKLOG_PATH!r} is missing the 'W20 Pull-Forward "
        f"Acceptance Bar' section header. The section was promoted "
        f"at W20-0 and must remain through close-out + post-merge audit."
    )


def test_section_18_w20_header_present_in_refactor_optimization() -> None:
    """``REFACTOR_OPTIMIZATION.md`` must contain a §18 header that
    names W20.

    §18 was split from the combined §18-§20 planning header at W20-0
    (W19-0 paterni mirror). Removing or renaming §18 orphans the W20
    plan narrative from the slim canonical.
    """
    text = (REPO_ROOT / _REFACTOR_OPT_PATH).read_text(encoding="utf-8")
    found_header = any(
        line.startswith("#") and "§18" in line and "W20" in line
        for line in text.splitlines()
    )
    assert found_header, (
        f"{_REFACTOR_OPT_PATH!r} is missing a '§18 ... W20' header. "
        f"The W20 plan source section was split into §18 at W20-0 "
        f"and must remain until at least the W20 close-out audit."
    )
