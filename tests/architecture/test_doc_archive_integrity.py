"""Archive snapshots must preserve readable, navigable historical detail."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

_SNAPSHOTS = (
    "documents/archive/backlog/POST_POC_BACKLOG_full_2026-06-15.md",
    "documents/archive/plans/REFACTOR_OPTIMIZATION_full_2026-06-15.md",
    "documents/archive/plans/automation_todo_2026-05-28.md",
    "documents/archive/status/REFACTOR_STATUS_full_2026-06-15.md",
)
_MARKDOWN_LINK_RE = re.compile(r"\]\(([^)]+)\)")
_EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "#")


def _local_link_targets(snapshot: Path) -> list[str]:
    targets: list[str] = []
    for raw_target in _MARKDOWN_LINK_RE.findall(snapshot.read_text(encoding="utf-8")):
        target = raw_target.strip().strip("<>")
        if not target or target.startswith(_EXTERNAL_PREFIXES):
            continue
        targets.append(target.partition("#")[0])
    return targets


@pytest.mark.parametrize("rel_path", _SNAPSHOTS)
def test_archive_snapshot_local_links_resolve(rel_path: str) -> None:
    snapshot = REPO_ROOT / rel_path
    assert snapshot.is_file(), f"required archive snapshot missing: {rel_path}"

    missing = [
        target
        for target in _local_link_targets(snapshot)
        if not (snapshot.parent / unquote(target)).resolve().exists()
    ]

    assert not missing, (
        f"{rel_path} contains local links that no longer resolve from its "
        f"archive location: {missing}"
    )
