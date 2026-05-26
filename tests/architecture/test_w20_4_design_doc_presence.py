"""W20-4 DESIGN doc presence pin.

W20-4 (``[DESIGN taxonomy-comments-testing-readiness]``, commit
``05f47f3``) landed ``documents/architecture/comments-testing-readiness.md``
as the W21 plumbing template — surveys the VS Code Comments API +
Test Controller API surface, identifies stubbed vs missing plumbing,
and proposes the W21-1 (testing) + W21-2 (comments) implementation
shape.

This test pins the doc's existence + key shape so a future refactor
that relocates / deletes / rewrites it surfaces in the test suite
rather than only when W21 starts and looks for the template.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


_W20_4_DESIGN_DOC_PATH = "documents/architecture/comments-testing-readiness.md"


def test_w20_4_design_doc_exists() -> None:
    """The W20-4 DESIGN doc must exist at the canonical path.

    Landed at W20-4 commit ``05f47f3``; unblocks W21-1 + W21-2. A
    relocation must update this test in the same commit.
    """
    doc_path = REPO_ROOT / _W20_4_DESIGN_DOC_PATH
    assert doc_path.exists(), (
        f"W20-4 DESIGN doc missing at {_W20_4_DESIGN_DOC_PATH!r}. "
        f"Landed at commit 05f47f3 to unblock W21-1 (testing) + W21-2 "
        f"(comments); a relocation or rewrite must update this pin."
    )


def test_w20_4_design_doc_carries_design_status_marker() -> None:
    """The W20-4 DESIGN doc must declare itself ``Status: DESIGN``.

    The marker signals doc-only intent (no code lands here); the
    W21 plumbing iters lift the surface from this template. If the
    doc evolves into a different artifact shape (ADR, implementation
    note), this gate fires to force an explicit update.
    """
    doc_path = REPO_ROOT / _W20_4_DESIGN_DOC_PATH
    text = doc_path.read_text(encoding="utf-8")
    assert "Status: DESIGN" in text, (
        f"W20-4 DESIGN doc at {_W20_4_DESIGN_DOC_PATH!r} is missing "
        f"the 'Status: DESIGN' marker. The W20-4 sub-iter paterni "
        f"requires this marker to communicate doc-only intent."
    )


def test_w20_4_design_doc_covers_both_target_api_surfaces() -> None:
    """The W20-4 DESIGN doc must reference the VS Code Comments API
    AND the VS Code Test API.

    Both surfaces are required by the W21 plumbing slate (W21-1
    testing + W21-2 comments). Dropping one orphans the W21 pull
    from its unblocker template.
    """
    doc_path = REPO_ROOT / _W20_4_DESIGN_DOC_PATH
    text = doc_path.read_text(encoding="utf-8")
    assert "createCommentController" in text or "Comments API" in text, (
        f"{_W20_4_DESIGN_DOC_PATH!r} must reference the VS Code "
        f"Comments API surface — required by W21-2."
    )
    assert (
        "createTestController" in text
        or "Test Controller" in text
        or "Test API" in text
    ), (
        f"{_W20_4_DESIGN_DOC_PATH!r} must reference the VS Code "
        f"Test API surface — required by W21-1."
    )
