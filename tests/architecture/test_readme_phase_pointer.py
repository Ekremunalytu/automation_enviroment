"""README phase pointer pin.

The repo-root ``README.md`` is the newcomer-facing phase summary while
``documents/REFACTOR_STATUS.md`` owns current closure state. After PR #29
merged on ``2026-05-26``, W21 advanced on the `week21` branch per user
direction (W11-W20 paterni preserved); the invariant becomes: README
must carry the W13 + W14 + W15 + W16 + W17 + W18 + W19 + W20 close-out
merge facts (still cited from the REFACTOR_STATUS banner) and the
current W21 tracker pointer from the status banner.
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


def test_readme_phase_pointer_tracks_active_w21_status() -> None:
    """README must expose the same current W21 pointer as REFACTOR_STATUS."""
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    # W21-0 in-flight lifecycle and the W21-N closed-but-not-merged pre-merge
    # hygiene window both need to satisfy this gate. Accept all forms so
    # the gate spans the entire W21 lifetime (in-flight + pre-merge + closed).
    # The W21-0 banner uses ``W21-0 doc-reconcile in-flight`` (W19-0 / W20-0
    # paterni mirror) — accept that specific phrase plus the simpler
    # ``W21 active`` / ``W21 in-flight`` / closed forms used at later
    # sub-iters and after PR merge.
    assert any(
        marker in status_banner
        for marker in (
            "W21 active",
            "W21 in-flight",
            "W21-0 in-flight",
            "W21-0 doc-reconcile in-flight",
            "W21 fully closed synthetically",
            "W21 closed synthetically",
        )
    ), (
        "REFACTOR_STATUS.md banner should name the current W21 state after "
        "PR #29 merged on 2026-05-26. W21 lives on the `week21` branch per "
        "user direction — W11-W20 paterni preserved. "
        f"Banner line: {status_banner!r}."
    )
    for token in (
        "W21",
        "active-work/W21-coverage-promotion-mid-tier.md",
        "week21",
    ):
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"external readers see the current W21 pointer. Banner "
            f"line: {status_banner!r}."
        )


def test_readme_phase_pointer_mentions_w13_closeout_merge() -> None:
    """README must carry the W13 close-out merge fact from REFACTOR_STATUS."""
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    for token in ("PR #20", "week13 -> main", "772deb3"):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner should include {token!r} while W21 is "
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
            f"REFACTOR_STATUS.md banner should include {token!r} while W21 is "
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
            f"REFACTOR_STATUS.md banner should include {token!r} while W21 is "
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
            f"REFACTOR_STATUS.md banner should include {token!r} while W21 is "
            f"active so the W16 close-out fact does not drift. Banner line: "
            f"{status_banner!r}."
        )
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"the W16 close-out state does not drift. Banner line: "
            f"{status_banner!r}."
        )


def test_readme_phase_pointer_mentions_w17_closeout_merge() -> None:
    """README must carry the W17 close-out merge fact from REFACTOR_STATUS.

    Added alongside the W17 → W18 transition on `2026-05-21` so the next
    transition (W18 → W19) inherits the same drift-prevention pattern for
    the previous close-out (W17 PR #25 / week17 -> main / `bff565d`).
    """
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    for token in ("PR #25", "week17 -> main", "bff565d"):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner should include {token!r} while W21 is "
            f"active so the W17 close-out fact does not drift. Banner line: "
            f"{status_banner!r}."
        )
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"the W17 close-out state does not drift. Banner line: "
            f"{status_banner!r}."
        )


def test_readme_phase_pointer_mentions_w18_closeout_merge() -> None:
    """README must carry the W18 close-out merge fact from REFACTOR_STATUS.

    Added alongside the W18 → W19 transition on `2026-05-21` so the next
    transition (W19 → W20) inherits the same drift-prevention pattern for
    the previous close-out (W18 PR #26 / week18 -> main / `9874e79`).
    """
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    for token in ("PR #26", "week18 -> main", "9874e79"):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner should include {token!r} while W21 is "
            f"active so the W18 close-out fact does not drift. Banner line: "
            f"{status_banner!r}."
        )
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"the W18 close-out state does not drift. Banner line: "
            f"{status_banner!r}."
        )


def test_readme_phase_pointer_mentions_w19_closeout_merge() -> None:
    """README must carry the W19 close-out merge fact from REFACTOR_STATUS.

    Added alongside the W19 → W20 transition on `2026-05-26` so the next
    transition (W20 → W21) inherits the same drift-prevention pattern for
    the previous close-out (W19 PR #28 / week19 -> main / `c879603`).
    """
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    for token in ("PR #28", "week19 -> main", "c879603"):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner should include {token!r} while W21 is "
            f"active so the W19 close-out fact does not drift. Banner line: "
            f"{status_banner!r}."
        )
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"the W19 close-out state does not drift. Banner line: "
            f"{status_banner!r}."
        )


def test_readme_phase_pointer_mentions_w20_closeout_merge() -> None:
    """README must carry the W20 close-out merge fact from REFACTOR_STATUS.

    Added alongside the W20 → W21 transition on `2026-05-27` so the next
    transition (W21 → W22) inherits the same drift-prevention pattern for
    the previous close-out (W20 PR #29 / week20 -> main / `64a3c3d`).
    """
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    for token in ("PR #29", "week20 -> main", "64a3c3d"):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner should include {token!r} while W21 is "
            f"active so the W20 close-out fact does not drift. Banner line: "
            f"{status_banner!r}."
        )
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            f"the W20 close-out state does not drift. Banner line: "
            f"{status_banner!r}."
        )
