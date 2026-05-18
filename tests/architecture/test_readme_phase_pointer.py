"""README phase pointer pin.

The repo-root ``README.md`` is the newcomer-facing phase summary while
``documents/REFACTOR_STATUS.md`` owns current closure state. After PR #23
merged on ``2026-05-18``, W17 is active **on the `week17` branch per user
direction** (W11-W16 paterni preserved), so the invariant becomes:
README must carry the W13 + W14 + W15 + W16 close-out merge facts (still
cited from the REFACTOR_STATUS banner) and the active W17 tracker pointer
from the status banner.
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


def test_readme_phase_pointer_tracks_active_w17_status() -> None:
    """README must expose the same active W17 pointer as REFACTOR_STATUS."""
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    assert "W17 active" in status_banner, (
        "REFACTOR_STATUS.md banner should name the active W17 state after "
        "PR #23 merged on 2026-05-18. W17 lives on the `week17` branch per "
        "user direction — W11-W16 paterni preserved. "
        f"Banner line: {status_banner!r}."
    )
    for token in (
        "W17",
        "active-work/W17-carryover-and-lifecycle-harness.md",
        "week17",
    ):
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"external readers see the active W17 pointer. Banner "
            f"line: {status_banner!r}."
        )


def test_readme_phase_pointer_mentions_w13_closeout_merge() -> None:
    """README must carry the W13 close-out merge fact from REFACTOR_STATUS."""
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    for token in ("PR #20", "week13 -> main", "772deb3"):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner should include {token!r} while W17 is "
            f"active so the W13 close-out fact does not drift. Banner line: "
            f"{status_banner!r}."
        )
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"the W13 close-out state does not drift. Banner line: "
            f"{status_banner!r}."
        )


def test_readme_phase_pointer_mentions_w14_closeout_merge() -> None:
    """README must carry the W14 close-out merge fact from REFACTOR_STATUS.

    Added alongside the W14 → W15 transition on `2026-05-16` so the next
    transition (W15 → W16) inherits the same drift-prevention pattern for
    the previous close-out (W14 PR #21 / week14 -> main / `4e03c8d`).
    """
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    for token in ("PR #21", "week14 -> main", "4e03c8d"):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner should include {token!r} while W17 is "
            f"active so the W14 close-out fact does not drift. Banner line: "
            f"{status_banner!r}."
        )
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"the W14 close-out state does not drift. Banner line: "
            f"{status_banner!r}."
        )


def test_readme_phase_pointer_mentions_w15_closeout_merge() -> None:
    """README must carry the W15 close-out merge fact from REFACTOR_STATUS.

    Added alongside the W15 → W16 transition on `2026-05-18` so the next
    transition (W16 → W17) inherits the same drift-prevention pattern for
    the previous close-out (W15 PR #22 / week15 -> main / `6161472`).
    """
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    for token in ("PR #22", "week15 -> main", "6161472"):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner should include {token!r} while W17 is "
            f"active so the W15 close-out fact does not drift. Banner line: "
            f"{status_banner!r}."
        )
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"the W15 close-out state does not drift. Banner line: "
            f"{status_banner!r}."
        )


def test_readme_phase_pointer_mentions_w16_closeout_merge() -> None:
    """README must carry the W16 close-out merge fact from REFACTOR_STATUS.

    Added alongside the W16 → W17 transition on `2026-05-18` so the next
    transition (W17 → W18) inherits the same drift-prevention pattern for
    the previous close-out (W16 PR #23 / week16 -> main / `1b6d43f`).
    """
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    for token in ("PR #23", "week16 -> main", "1b6d43f"):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner should include {token!r} while W17 is "
            f"active so the W16 close-out fact does not drift. Banner line: "
            f"{status_banner!r}."
        )
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"the W16 close-out state does not drift. Banner line: "
            f"{status_banner!r}."
        )
