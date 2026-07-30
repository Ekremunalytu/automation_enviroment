"""Load the machine-readable phase state used by documentation guards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_MANIFEST_PATH = REPO_ROOT / "documents" / "phase.json"


def load_manifest() -> dict[str, Any]:
    """Parse and return ``documents/phase.json``."""
    return json.loads(PHASE_MANIFEST_PATH.read_text(encoding="utf-8"))


def merge_fingerprint(entry: dict[str, Any]) -> str:
    """Render the ``PR #<n>`` fingerprint for a close-out entry."""
    return f"PR #{entry['pr']}"


def source_branch(entry: dict[str, Any]) -> str:
    """The ``weekN`` source-branch token from a ``weekN -> main`` branch."""
    return str(entry["branch"]).split(" -> ", 1)[0]


def phase_number(entry: dict[str, Any]) -> int:
    """The integer ``N`` from a ``W<N>`` phase id."""
    return int(str(entry["id"]).removeprefix("W"))
