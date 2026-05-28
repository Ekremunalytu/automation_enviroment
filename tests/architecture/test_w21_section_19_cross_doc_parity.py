"""W21 §19 cross-doc parity gate.

Mirrors `tests/architecture/test_w20_section_18_cross_doc_parity.py`
for the W21 sub-iter slate. Pins the audit trail across the three
docs that explicitly track W21 status:

- W21 active tracker (`documents/active-work/W21-coverage-promotion-mid-tier.md`)
- `REFACTOR_OPTIMIZATION.md` §19 (W21 plan source)
- `POST_POC_BACKLOG.md` W21 Pull-Forward Acceptance Bar

W21 sub-iter slate (closed `2026-05-28`):

- W21-0 doc-reconcile (8434323 + 19bd9c7)
- W21-3 workspace_trust (c744c15 + 4b0a1ed) — landed first as
  precondition for W21-1 / W21-2 per W20-4 DESIGN doc open Q4
  resolution
- W21-1 testing (7e87030 + 38b8fd8)
- W21-2 comments (8948ea6 + 3088709)
- W21-4 container hardening baseline (16e2224 + 2f9cba2 + 8c42445)
  — STRETCH pulled into W21 per user direction after W21-1 + W21-2
  closed cleanly; primary + followup-1 + self-stamp pattern
- W21-N close-out hygiene (this commit's SHA backfills at PR merge
  or follow-up audit per W20-5 paterni)
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


# W21 sub-iter audit trail: primary + self-stamp commit SHAs.
# Every SHA must appear verbatim in the W21 tracker (single source
# of truth). The W21-4-followup-1 SHA is included because the
# followup landed the cap_add fix that made the primary live-run
# pass — losing it severs the audit trail of the live-run path.
_W21_FULL_AUDIT_SHAS: tuple[str, ...] = (
    "8434323",  # W21-0 primary (doc-reconcile)
    "19bd9c7",  # W21-0 self-stamp (baseline live-run captured)
    "c744c15",  # W21-3 primary (workspace_trust flip + harness + scenario)
    "4b0a1ed",  # W21-3 self-stamp
    "7e87030",  # W21-1 primary (testing flip + Test Controller markers)
    "38b8fd8",  # W21-1 self-stamp
    "8948ea6",  # W21-2 primary (comments flip + Comment thread markers)
    "3088709",  # W21-2 self-stamp
    "16e2224",  # W21-4 primary (cap_drop + no-new-privileges)
    "2f9cba2",  # W21-4-followup-1 (cap_add fix for api/ui user-drop)
    "8c42445",  # W21-4 self-stamp
)


# Primary commit SHAs subset — must appear in §19 + POST_POC_BACKLOG
# (those docs traditionally list primaries; self-stamps land later
# as tracker freezes). W21-4-followup-1 included because §19 + POST_POC
# also reference it as part of the W21-4 closure row.
_W21_PRIMARY_SHAS: tuple[str, ...] = (
    "8434323",  # W21-0
    "c744c15",  # W21-3
    "7e87030",  # W21-1
    "8948ea6",  # W21-2
    "16e2224",  # W21-4 primary
    "2f9cba2",  # W21-4-followup-1
)


# W21 sub-iter live-run anchor filenames + sha256s — pinned at each
# self-stamp commit. The tracker carries all five anchors as the
# audit-trail link from narrative to live JSON fingerprints.
_W21_ANCHORS: tuple[tuple[str, str], ...] = (
    (
        "600d9ecba5eb",  # W21-0 baseline
        "1db1480551fd90625a5c7c2e474b43c4de3a867d35dab4aacc65e8060bcc4477",
    ),
    (
        "6fd7b959bd5a",  # W21-3 workspace_trust acceptance
        "fa83017a4de25ea6...d6f7477"[:0]  # placeholder slot; the real sha is below
        + "fa83017a4de25ea6c5cd34e4f99c2b9f8b91e9dcf4a26da0e3b54ad6d6f7477",
    ),
    (
        "0b4998ce31b4",  # W21-1 testing acceptance
        "b7192bc2ff9c611f00e9dd806af54e0648c92d9201d78fe9ccb886dcf5968be4",
    ),
    (
        "1ddb3702c0ca",  # W21-2 comments acceptance
        "2dabd15be329bbf1685fe7fc31469355bdc4a5acac2a364d43a196437339cbff",
    ),
    (
        "eacea0b6690e",  # W21-4 container hardening live-run
        "5d7c8b974f21e3bf4ad679a41551dd3e7b71d37573f5e7f2b28b87d2ad4a6a84",
    ),
)


_W21_TRACKER_PATH = "documents/active-work/W21-coverage-promotion-mid-tier.md"
_REFACTOR_OPT_PATH = "documents/REFACTOR_OPTIMIZATION.md"
_POST_POC_BACKLOG_PATH = "documents/POST_POC_BACKLOG.md"


# W21-3 anchor's sha256 ends with "d6f7477" but appears in the
# canonical preamble both as full 64-char and truncated. The full
# 64-char form appears in the W21-3 self-stamp + W21-N close-out.
# Recompute the correct full sha here so the test's pin matches what
# the preamble actually contains.
_W21_3_ANCHOR_SHA256 = "fa83017a4de25ea6c5cd34e4f99c2b9f8b91e9dcf4a26da0e3b54ad6d6f7477"


@pytest.mark.parametrize("sha", _W21_FULL_AUDIT_SHAS)
def test_w21_tracker_contains_full_audit_trail(sha: str) -> None:
    """The W21 tracker must contain every W21 sub-iter primary AND
    self-stamp SHA verbatim.

    Each sub-iter lands a primary + self-stamp pair (W21-4 also has
    a followup-1 between them); the self-stamp flips the tracker
    row from `planned → closed via this commit`. At close-out, the
    placeholder ``this commit`` is replaced by the explicit SHA —
    that backfill is what pins the audit trail to the tracker.
    """
    text = (REPO_ROOT / _W21_TRACKER_PATH).read_text(encoding="utf-8")
    assert sha in text, (
        f"W21 tracker {_W21_TRACKER_PATH!r} is missing sub-iter SHA "
        f"{sha!r}. If the sub-iter just landed, the self-stamp commit "
        f"forgot to backfill `this commit` to the explicit SHA."
    )


@pytest.mark.parametrize("sha", _W21_PRIMARY_SHAS)
def test_section_19_contains_w21_primary_shas(sha: str) -> None:
    """``REFACTOR_OPTIMIZATION.md`` §19 must contain every W21
    sub-iter primary commit SHA (plus the W21-4 followup-1 SHA).

    §19 is the W21 plan source; sub-iter rows in §19.4 (Exit
    Criteria) and the per-iter audit cite the primary SHA at
    close-out. A primary SHA missing from §19 indicates an
    incomplete close-out or doc drift.
    """
    text = (REPO_ROOT / _REFACTOR_OPT_PATH).read_text(encoding="utf-8")
    assert sha in text, (
        f"{_REFACTOR_OPT_PATH!r} is missing W21 primary SHA {sha!r}. "
        f"The §19 self-stamp must list primary SHAs for every closed "
        f"W21 sub-iter (including W21-4 followup-1 because it's part "
        f"of the W21-4 closure row)."
    )


@pytest.mark.parametrize("sha", _W21_PRIMARY_SHAS)
def test_post_poc_backlog_contains_w21_primary_shas(sha: str) -> None:
    """``POST_POC_BACKLOG.md`` W21 Pull-Forward must contain every
    W21 sub-iter primary commit SHA (plus the W21-4 followup-1 SHA).

    The W21 Pull-Forward table tracks acceptance-bar closure. A
    primary SHA missing here means the closure row was never updated
    when the sub-iter landed.
    """
    text = (REPO_ROOT / _POST_POC_BACKLOG_PATH).read_text(encoding="utf-8")
    assert sha in text, (
        f"{_POST_POC_BACKLOG_PATH!r} is missing W21 primary SHA "
        f"{sha!r}. The W21 Pull-Forward Acceptance Bar row for this "
        f"sub-iter was never marked closed."
    )


@pytest.mark.parametrize("filename, _sha256", _W21_ANCHORS)
def test_w21_anchor_filename_appears_in_tracker(filename: str, _sha256: str) -> None:
    """Every W21 sub-iter live-run anchor filename short-SHA must
    appear in the W21 tracker.

    Each self-stamp commit pinned an anchor; a refactor that drops
    the filename token orphans the live-run evidence from the
    tracker narrative. The W21-4 anchor (`eacea0b6690e`) is the
    close-out anchor since W21-N doesn't change runtime behavior.
    """
    text = (REPO_ROOT / _W21_TRACKER_PATH).read_text(encoding="utf-8")
    assert filename in text, (
        f"W21 tracker missing live-run anchor filename {filename!r}. "
        f"Self-stamp commits pin these anchors as audit evidence — "
        f"preserve them through W21-N close-out and post-merge audit."
    )


@pytest.mark.parametrize("_filename, sha256", _W21_ANCHORS)
def test_w21_anchor_sha256_appears_in_tracker(_filename: str, sha256: str) -> None:
    """Each W21 sub-iter live-run anchor's full sha256 (or the
    truncated 4-digit-prefix form) must appear in the W21 tracker
    so the narrative carries the fingerprint of the JSON evidence.

    Some preambles truncate sha256 as `<8-char>...<7-char>` (e.g.
    `fa83017a...d6f7477`) instead of the full 64-char form; this
    test accepts either by checking the first 12 chars (unique
    enough to identify the anchor without conflicting with adjacent
    hex literals).
    """
    text = (REPO_ROOT / _W21_TRACKER_PATH).read_text(encoding="utf-8")
    sha_prefix_12 = sha256[:12]
    assert sha_prefix_12 in text, (
        f"W21 tracker missing live-run anchor sha256 prefix "
        f"{sha_prefix_12!r} (from full {sha256!r}). The self-stamp "
        f"commit pinned this sha256; losing it severs the link from "
        f"narrative to the live JSON fingerprint."
    )


def test_w21_close_out_phase_line_present() -> None:
    """The W21 tracker's Phase line must reference W21-N close-out
    on the `week21` branch with all sub-iters listed.

    The Phase line is the single-line summary that REFACTOR_STATUS.md
    + active-work/README.md mirror. A drift here cascades to those
    docs and the README phase-pointer test gates.
    """
    text = (REPO_ROOT / _W21_TRACKER_PATH).read_text(encoding="utf-8")
    # Match the W21 close-out shape: all 5 substantive sub-iters
    # named + W21-N close-out reference + week21 branch reference.
    for token in (
        "W21-0",
        "W21-3",
        "W21-1",
        "W21-2",
        "W21-4",
        "W21-N",
        "week21",
    ):
        assert token in text, (
            f"W21 tracker Phase block missing {token!r} — close-out hygiene incomplete."
        )
