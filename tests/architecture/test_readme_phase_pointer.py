"""W13-11 (d) — README phase pointer regex pin (steal-paired from W13-13 F4).

The repo-root ``README.md`` carries a Current Phase section that
summarises which W13-N sub-iters are closed. Pre-W13-11 it had drifted
seven sub-iters behind — stalled at "W13-1..W13-4 are closed and W13-5
is expected to pull..." while ``documents/REFACTOR_STATUS.md``'s
``Last Updated`` header was already at W13-11. The W13-13 close-gate
plan (``documents/active-work/W13-test-expansion-observability.md::
W13-13 — Worker-start cancel-race CAS``) originally bundled an F4
README sweep PLUS this regex pin to prevent future drift; the W13-11
push of 2026-05-12 pulled both into W13-11 so the README sweep stays
paired with its banner-cascade fix-up (sub-commit 8 = sweep, sub-commit
12 = this pin).

The pin enforces a one-line invariant: the highest ``W13-N`` token
appearing anywhere in ``README.md`` must be at least as recent as the
highest ``W13-N`` token in the first ``Last Updated:`` line of
``documents/REFACTOR_STATUS.md``. The slim canonical ``REFACTOR_STATUS.md``
is the canonical source of truth for current phase state, so any time
its banner ratchets to a new W13-N the README must catch up in the
same commit family or this test fails.

Why a max-of-W13-N comparison rather than text-by-text parity? The two
files speak different audiences — README is short-form for newcomers,
STATUS is granular for in-flight work. Coupling them on free text
would generate constant noise; coupling on the highest W13-N
maintained on each side gives us the property we actually want
(README never falls behind) without forcing prose matching.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
REFACTOR_STATUS_PATH = REPO_ROOT / "documents" / "REFACTOR_STATUS.md"

_W13_N_RE = re.compile(r"W13-(\d+)")


def _max_w13_n(text: str) -> int:
    """Highest ``W13-N`` (as int N) referenced anywhere in ``text``.

    Returns ``0`` if the text contains no ``W13-N`` token. Range tokens
    like ``W13-1..W13-7`` produce both endpoints because the regex
    matches each ``W13-N`` occurrence independently.
    """
    return max((int(m) for m in _W13_N_RE.findall(text)), default=0)


def _first_last_updated_line(text: str) -> str:
    """Return the first banner line that begins with the ``Last Updated:`` marker.

    Both slim canonicals follow the pattern::

        `Last Updated: 2026-05-NN (W12 closed; ...)`

    The W13-N tokens we care about live inside that line — searching
    the whole file would also pick up cross-references to old W13-N in
    deferred / archived notes, which would weaken the assertion.
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


def test_readme_phase_pointer_not_behind_refactor_status() -> None:
    """W13-11 (d): README must not reference a W13-N strictly lower than REFACTOR_STATUS's banner.

    The pin is asymmetric on purpose. README is allowed to mention a
    *higher* W13-N than the banner (e.g. while a new sub-iter is being
    planned and the README is updated ahead of the slim canonical), but
    not lower — that direction is the drift we are trying to prevent.
    """
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")

    readme_max = _max_w13_n(readme_text)
    status_banner = _first_last_updated_line(status_text)
    status_banner_max = _max_w13_n(status_banner)

    assert status_banner_max > 0, (
        f"REFACTOR_STATUS.md `Last Updated:` banner has no W13-N token. "
        f"Banner line: {status_banner!r}. Either the file structure has "
        f"changed (banner moved out of the first non-empty content line) "
        f"or W13 has fully closed and the test should be extended to "
        f"cover the next phase namespace."
    )
    assert readme_max >= status_banner_max, (
        f"README.md is behind REFACTOR_STATUS.md: README highest W13-N "
        f"is W13-{readme_max}, but REFACTOR_STATUS.md banner mentions "
        f"W13-{status_banner_max}. Update README.md's Current Phase "
        f"block (line ~58) in the same commit family that ratchets "
        f"REFACTOR_STATUS.md so external readers never see a stale "
        f"phase summary. Banner line: {status_banner!r}."
    )


def test_readme_phase_pointer_explicitly_mentions_latest_status_w13_n() -> None:
    """W13-11 (d) — companion pin: the exact ``W13-{status_max}`` token must appear in README.

    The previous test passes if README contains any token >= the status
    banner max; this one additionally requires the *specific* highest
    token. A future regression that overshoots — e.g. README mentions a
    placeholder ``W13-99`` for staging but forgets the actual latest —
    would slip through the first test. Pinning the exact match is the
    direct expression of "README must point at the same W13-N as the
    banner."
    """
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")

    status_banner = _first_last_updated_line(status_text)
    status_banner_max = _max_w13_n(status_banner)
    expected_token = f"W13-{status_banner_max}"

    assert expected_token in readme_text, (
        f"README.md does not mention {expected_token!r} anywhere; the "
        f"REFACTOR_STATUS.md banner names it as the latest sub-iter. "
        f"Add an explicit reference to {expected_token} in the Current "
        f"Phase block so the slim-canonical drift surface stays closed. "
        f"Banner line: {status_banner!r}."
    )
