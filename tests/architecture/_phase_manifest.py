"""Single-source loader for ``documents/phase.json``.

``documents/phase.json`` is the machine-readable source of the phase
"preamble" truth — the most-recently-merged weekly close-out (PR + SHA),
the ``W13..`` close-out history chain, and the active named stream. The
doc-preamble gates in this package read from here instead of
hand-maintaining duplicate ``PR #NN`` / ``<sha>`` literals, so advancing a
phase is a one-file edit (``phase.json``) plus the doc banners.

This is a non-test helper module (``python_files`` only collects
``test_*.py``), imported as ``tests.architecture._phase_manifest`` — the
same shape as ``tests/security/helpers.py``.
"""

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
