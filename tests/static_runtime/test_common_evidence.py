"""Tests for the shared static-rule evidence helpers (ES-3a).

Pins the two security-relevant guarantees of ``static_runtime.rules._common``:
secret redaction (AGENTS rule 11) and the contract length clamp on evidence
snippets, plus that the shared typosquat allowlist loads from its new home.
"""

from __future__ import annotations

import re
from typing import cast
from unittest.mock import Mock

from static_runtime.rules._common import (
    file_evidence,
    find_local_pattern_cluster,
    safe_snippet,
)


def test_safe_snippet_redacts_secrets() -> None:
    # A db_url-shaped secret embedded in a quoted snippet must be redacted.
    raw = 'config: "postgresql://user:hunter2@db.internal/app"'
    out = safe_snippet(raw)
    assert "hunter2" not in out
    assert "[REDACTED:db_url]" in out


def test_safe_snippet_clamps_to_contract_bound() -> None:
    out = safe_snippet("x" * 1000)
    assert len(out) == 400  # StaticEvidenceRef.snippet max_length


def test_file_evidence_redacts_snippet() -> None:
    ref = file_evidence(
        "bundle.js",
        "source_file",
        snippet='token="postgresql://u:p@h/d"',
    )
    assert ref.relative_path == "bundle.js"
    assert ref.tool == "inhouse"
    assert ref.snippet is not None and "[REDACTED:db_url]" in ref.snippet


def test_popular_extensions_allowlist_loads_from_new_home() -> None:
    # Guards the ES-3a allowlist move (analysis_engine/allowlists ->
    # analysis_contracts/data): the file must still load and carry a known id.
    from packages.analysis_contracts.typosquat_match import popular_extensions

    entries = popular_extensions()
    assert len(entries) > 0
    assert "ms-python.python" in entries


def test_pattern_cluster_stops_after_a_missing_required_conjunct() -> None:
    later_pattern = Mock()
    later_pattern.finditer.side_effect = AssertionError(
        "later patterns must not scan after a required conjunct is absent"
    )

    cluster = find_local_pattern_cluster(
        "const ordinary = true;",
        (re.compile(r"globalState"), cast(re.Pattern[str], later_pattern)),
        max_span=1024,
    )

    assert cluster is None
    later_pattern.finditer.assert_not_called()
