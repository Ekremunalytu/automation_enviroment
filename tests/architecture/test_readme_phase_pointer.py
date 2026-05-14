"""README phase pointer pin.

The repo-root ``README.md`` is the newcomer-facing phase summary while
``documents/REFACTOR_STATUS.md`` owns current closure state. During W13 this
test compared the highest W13-N token. After PR #20 merged and the
``week14`` branch was cut on `2026-05-13`, W14 is active and W14-1 is the
first pulled sub-iter, so the invariant becomes: README must carry the W13
close-out merge fact and the active W14 tracker / branch-cut pointer from
the status banner.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
REFACTOR_STATUS_PATH = REPO_ROOT / "documents" / "REFACTOR_STATUS.md"


def _first_last_updated_line(text: str) -> str:
    """Return the first banner line that begins with the ``Last Updated:`` marker.

    Both slim canonicals follow the pattern::

        `Last Updated: 2026-05-NN (W13 closed; ...)`

    The active phase and close-out merge tokens we care about live inside that
    line — searching the whole file would also pick up cross-references in old
    phase summaries, which would weaken the assertion.
    """
    for line in text.splitlines():
        # Skip leading whitespace and the optional backtick that wraps the
        # banner; match on the literal ``Last Updated:`` prefix.
        stripped = line.lstrip().lstrip("`").lstrip()
        if stripped.startswith("Last Updated:"):
            return stripped
    raise AssertionError(
        "REFACTOR_STATUS.md must carry a `Last Updated: ...` banner as its "
        "first non-empty content line; this convention is the anchor "
        "this test couples README to."
    )


def test_readme_phase_pointer_tracks_active_w14_status() -> None:
    """README must expose the same active W14 pointer as REFACTOR_STATUS."""
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    assert "W14 active" in status_banner, (
        "REFACTOR_STATUS.md banner should name the active W14 state after the "
        f"`week14` branch cut on 2026-05-13. Banner line: {status_banner!r}."
    )
    for token in (
        "W14",
        "active-work/W14-codex-acceptance-observability.md",
        "week14",
    ):
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"external readers see the active W14 pointer. Banner "
            f"line: {status_banner!r}."
        )


def test_readme_phase_pointer_mentions_w13_closeout_merge() -> None:
    """README must carry the W13 close-out merge fact from REFACTOR_STATUS."""
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    for token in ("PR #20", "week13 -> main", "772deb3"):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner should include {token!r} while W14 is "
            f"active so the W13 close-out fact does not drift. Banner line: "
            f"{status_banner!r}."
        )
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"the W13 close-out state does not drift. Banner line: "
            f"{status_banner!r}."
        )
