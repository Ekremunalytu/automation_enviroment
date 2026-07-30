"""Keep README's current pointer aligned without turning it into a ledger."""

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
    """Return the first ``Last Updated:`` banner."""
    for line in text.splitlines():
        stripped = line.lstrip().lstrip("`").lstrip()
        if stripped.startswith("Last Updated:"):
            return stripped
    raise AssertionError(
        "REFACTOR_STATUS.md must carry a `Last Updated: ...` banner as its "
        "first non-empty content line; this convention is the anchor "
        "this test couples README to."
    )


def test_readme_phase_pointer_tracks_active_weekly_status() -> None:
    """README and status must expose the manifest's current weekly pointer."""
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
def test_status_carries_prior_closeout_merge(entry: dict[str, Any]) -> None:
    """The canonical status banner, not README, owns weekly history."""
    status_text = REFACTOR_STATUS_PATH.read_text(encoding="utf-8")
    status_banner = _first_last_updated_line(status_text)

    for token in (merge_fingerprint(entry), entry["branch"], entry["sha"]):
        assert token in status_banner, (
            f"REFACTOR_STATUS.md banner must include {token!r} so the "
            f"{entry['id']} close-out fact does not drift. Banner line: "
            f"{status_banner!r}."
        )
