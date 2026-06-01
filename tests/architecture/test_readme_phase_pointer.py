"""README phase pointer pin.

The repo-root ``README.md`` is the newcomer-facing phase summary while
``documents/REFACTOR_STATUS.md`` owns current closure state. The invariant:
README + the REFACTOR_STATUS banner must both carry (a) the current weekly
pointer (the most-recently-merged weekly close-out) and (b) every prior
weekly close-out merge fact, so the historical chain does not drift as
phases advance.

Both the current pointer and the prior-close-out chain are sourced from the
single manifest ``documents/phase.json`` (``last_merged_weekly`` +
``history``). The former per-phase functions (one each for W13..W21) are
now a single parametrized test; pytest node ids (``[W13]``..) preserve the
per-phase identity.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.architecture._phase_manifest import (
    REPO_ROOT,
    load_manifest,
    merge_fingerprint,
    source_branch,
)

README_PATH = REPO_ROOT / "README.md"
REFACTOR_STATUS_PATH = REPO_ROOT / "documents" / "REFACTOR_STATUS.md"

_MANIFEST = load_manifest()
_LAST_MERGED_WEEKLY = _MANIFEST["last_merged_weekly"]
_HISTORY = _MANIFEST["history"]


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


def test_readme_phase_pointer_tracks_active_weekly_status() -> None:
    """README must expose the same current weekly pointer as the
    REFACTOR_STATUS banner. Sourced from ``documents/phase.json`` ->
    ``last_merged_weekly``.
    """
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    weekly_id = _LAST_MERGED_WEEKLY["id"]
    weekly_sha = _LAST_MERGED_WEEKLY["sha"]
    week_branch = source_branch(_LAST_MERGED_WEEKLY)
    tracker_token = str(_LAST_MERGED_WEEKLY["tracker"]).removeprefix("documents/")

    for token in (weekly_id, weekly_sha):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner must name the current weekly phase "
            f"token {token!r} (from phase.json last_merged_weekly). Banner "
            f"line: {status_banner!r}."
        )
    for token in (weekly_id, tracker_token, week_branch):
        assert token in readme_text, (
            f"README.md must mention {token!r} in its current phase block so "
            "external readers see the current weekly pointer."
        )


@pytest.mark.parametrize("entry", _HISTORY, ids=[e["id"] for e in _HISTORY])
def test_readme_carries_prior_closeout_merge(entry: dict[str, Any]) -> None:
    """README + REFACTOR_STATUS must both carry every prior weekly close-out
    merge fact (PR + branch + SHA) from ``documents/phase.json`` ->
    ``history``, so the historical chain does not drift as phases advance.
    Replaces the former per-phase functions (W13..W21); node ids preserve
    per-phase identity.
    """
    readme_text = README_PATH.read_text(encoding="utf-8")
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    for token in (merge_fingerprint(entry), entry["branch"], entry["sha"]):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner must include {token!r} so the "
            f"{entry['id']} close-out fact does not drift. Banner line: "
            f"{status_banner!r}."
        )
        assert token in readme_text, (
            f"README.md must mention {token!r} so the {entry['id']} close-out "
            "fact does not drift."
        )
