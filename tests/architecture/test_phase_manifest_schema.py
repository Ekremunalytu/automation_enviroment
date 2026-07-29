"""Schema guard for the phase manifest (``documents/phase.json``).

``phase.json`` is the single source the doc-preamble gates read
(``test_canonical_preamble_parity``, ``test_readme_phase_pointer``,
``test_doc_preamble_consistency``). This gate validates the source's
shape so a malformed/incomplete manifest fails loudly here rather than as
a confusing downstream gate error.
"""

from __future__ import annotations

import re
from typing import Any

from tests.architecture._phase_manifest import (
    REPO_ROOT,
    load_manifest,
    phase_number,
)

_PHASE_ID = re.compile(r"^W\d+$")
_SHA = re.compile(r"^[0-9a-f]{7,40}$")
_BRANCH = re.compile(r"^week\d+ -> main$")


def _assert_closeout(entry: dict[str, Any], where: str) -> None:
    assert isinstance(entry, dict), f"{where} must be an object"
    assert _PHASE_ID.fullmatch(str(entry.get("id"))), (
        f"{where}.id must be 'W<N>': {entry.get('id')!r}"
    )
    assert isinstance(entry.get("pr"), int), f"{where}.pr must be an int"
    assert _BRANCH.fullmatch(str(entry.get("branch"))), (
        f"{where}.branch must be 'weekN -> main': {entry.get('branch')!r}"
    )
    assert _SHA.fullmatch(str(entry.get("sha"))), (
        f"{where}.sha must be a 7-40 char hex sha: {entry.get('sha')!r}"
    )


def test_phase_manifest_has_required_shape() -> None:
    manifest = load_manifest()
    assert set(manifest) >= {"last_merged_weekly", "history", "active_stream"}, (
        f"phase.json missing required top-level keys; has {sorted(manifest)}"
    )
    last_merged = manifest["last_merged_weekly"]
    _assert_closeout(last_merged, "last_merged_weekly")
    tracker = last_merged.get("tracker")
    assert tracker, "last_merged_weekly.tracker required"
    assert (REPO_ROOT / tracker).is_file(), (
        f"last_merged_weekly.tracker does not exist on disk: {tracker!r}"
    )


def test_phase_manifest_history_is_ordered_and_unique() -> None:
    manifest = load_manifest()
    history = manifest["history"]
    assert isinstance(history, list) and history, (
        "phase.json history must be a non-empty list"
    )
    for index, entry in enumerate(history):
        _assert_closeout(entry, f"history[{index}]")

    numbers = [phase_number(entry) for entry in history]
    assert numbers == sorted(numbers), (
        f"history must be ascending by phase number: {numbers}"
    )
    assert len(set(numbers)) == len(numbers), (
        f"history has duplicate phase numbers: {numbers}"
    )

    # The current last-merged weekly must not also appear in history — it
    # lives in last_merged_weekly until the next phase merges and demotes it.
    last_merged_number = phase_number(manifest["last_merged_weekly"])
    assert last_merged_number not in numbers, (
        f"last_merged_weekly W{last_merged_number} must not also appear in history"
    )
    assert max(numbers) < last_merged_number, (
        f"history max W{max(numbers)} must be < last_merged_weekly "
        f"W{last_merged_number}"
    )


def test_phase_manifest_active_stream_is_null_or_has_existing_tracker() -> None:
    manifest = load_manifest()
    stream = manifest["active_stream"]
    if stream is None:
        return

    assert isinstance(stream, dict), "active_stream must be null or an object"
    assert stream.get("id"), "active_stream.id required"
    tracker = stream.get("tracker")
    assert tracker, "active_stream.tracker required"
    assert (REPO_ROOT / tracker).is_file(), (
        f"active_stream.tracker does not exist on disk: {tracker!r}"
    )
