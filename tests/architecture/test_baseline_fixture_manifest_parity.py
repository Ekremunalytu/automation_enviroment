"""Architecture regression: BASELINE_EXTENSION_FIXTURES ↔
EXPECTED_ACTIVATION_EVENT_TYPES key parity.

`tests/platform/contracts/test_analysis_fixture_baselines.py` declares
two coupled top-level structures:

  - `BASELINE_EXTENSION_FIXTURES` — list of `(publisher, name, version)`
    tuples consumed by the resolve/round-trip suite.
  - `EXPECTED_ACTIVATION_EVENT_TYPES` — dict keyed on `f"{publisher}.{name}"`
    that the round-trip test looks up unconditionally:
    `parsed_event_types >= EXPECTED_ACTIVATION_EVENT_TYPES[extension_id]`.

If a new fixture lands in `BASELINE_EXTENSION_FIXTURES` without a
matching entry in `EXPECTED_ACTIVATION_EVENT_TYPES`, the round-trip
test fails with a bare `KeyError` at iteration time. The reverse drift
(a stale entry in `EXPECTED_ACTIVATION_EVENT_TYPES` for a removed
fixture) silently accumulates dead config. Both directions slipped
through casual review when the W13-8 GREEN sub-commit added three new
fixtures — this gate pins the invariant so future contributors get a
clear, named failure instead of a `KeyError`.
"""

from __future__ import annotations

from tests.platform.contracts.test_analysis_fixture_baselines import (
    BASELINE_EXTENSION_FIXTURES,
    EXPECTED_ACTIVATION_EVENT_TYPES,
)


def _baseline_extension_ids() -> set[str]:
    return {f"{publisher}.{name}" for publisher, name, _ in BASELINE_EXTENSION_FIXTURES}


def test_every_baseline_fixture_has_an_expected_activation_event_type_entry() -> None:
    baseline_ids = _baseline_extension_ids()
    expected_ids = set(EXPECTED_ACTIVATION_EVENT_TYPES)

    missing = baseline_ids - expected_ids

    assert not missing, (
        "BASELINE_EXTENSION_FIXTURES contains extension ids that are not "
        "keyed in EXPECTED_ACTIVATION_EVENT_TYPES; the round-trip test will "
        "raise KeyError at iteration time. Add the missing entries to "
        "EXPECTED_ACTIVATION_EVENT_TYPES (use `set()` for declarative-only "
        f"fixtures): {sorted(missing)}"
    )


def test_expected_activation_event_types_has_no_orphan_entries() -> None:
    baseline_ids = _baseline_extension_ids()
    expected_ids = set(EXPECTED_ACTIVATION_EVENT_TYPES)

    extras = expected_ids - baseline_ids

    assert not extras, (
        "EXPECTED_ACTIVATION_EVENT_TYPES has keys with no matching entry in "
        "BASELINE_EXTENSION_FIXTURES; the orphan entries are dead config. "
        f"Either re-register the fixture or remove the entry: {sorted(extras)}"
    )
