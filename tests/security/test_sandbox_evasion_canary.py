"""W22-5 sandbox-evasion canary fixture (ADR 0015).

Observer-side synthetic-probe coverage of the five evasion families
named in `documents/adrs/0015-sandbox-evasion-defense-policy.md`:

- E1 `webdriver_presence`
- E2 `cdp_fingerprint`
- E3 `timing_probe`
- E4 `platform_identity`
- E5 `process_introspection`

What W22-5 acceptance signals (per ADR 0015 §Operational notes):

- Each family's short-name is preserved through the
  `EvasionSignal` data shape so future W23+ runtime detection paths
  can be assert-tested against the same constant.
- An unknown family short-name is rejected at construction time, so
  a future taxonomy rename surfaces here in addition to the ADR
  invariant gate at
  `tests/architecture/test_sandbox_evasion_adr.py`.

What W22-5 explicitly does NOT validate (per ADR 0015 §Negative
Consequences):

- Suppression effectiveness — the actual masking code (Playwright
  page init scripts, launcher overrides) is W23+ scope.
- Runtime probe detection — the recorder integration point lands
  in W23+ alongside the detection logic.
"""

from __future__ import annotations

import pytest

from packages.analysis_planner.evasion_signals import (
    EVASION_FAMILY_TAXONOMY,
    EvasionSignal,
)


# Synthetic probe descriptors — one per family. The detail string is a
# representative example of what an analyzer-side observer would
# record when the corresponding evasion probe fires inside an
# untrusted extension.
_PROBE_FIXTURES: tuple[tuple[str, str], ...] = (
    (
        "webdriver_presence",
        "extension read navigator.webdriver via property accessor",
    ),
    (
        "cdp_fingerprint",
        "extension probed window.cdc_adoQpoasnfa76pfcZLmcfl_Array",
    ),
    (
        "timing_probe",
        "extension sampled performance.now() jitter across 100 frames",
    ),
    (
        "platform_identity",
        "extension read navigator.userAgent + navigator.platform pair",
    ),
    (
        "process_introspection",
        "extension attempted read of /proc/self/cmdline for playwright marker",
    ),
)


def test_evasion_family_taxonomy_matches_adr_0015() -> None:
    """The five family short-names in `EVASION_FAMILY_TAXONOMY` MUST
    be byte-identical with the ADR 0015 §Sandbox-Evasion Pattern
    Taxonomy enumeration.

    If this fails, either the ADR was edited (forcing a coordinated
    code update) or the module drifted (forcing the canary's contract
    to be re-aligned with the ADR).
    """
    expected = (
        "webdriver_presence",
        "cdp_fingerprint",
        "timing_probe",
        "platform_identity",
        "process_introspection",
    )
    assert expected == EVASION_FAMILY_TAXONOMY, (
        "EVASION_FAMILY_TAXONOMY drifted from ADR 0015. Coordinate "
        "the ADR amendment with the module + canary updates."
    )


@pytest.mark.parametrize(
    ("family", "detail"),
    _PROBE_FIXTURES,
    ids=lambda value: value if isinstance(value, str) and "_" in value else "detail",
)
def test_synthetic_probe_records_the_expected_family(
    family: str,
    detail: str,
) -> None:
    """For each ADR 0015 family, a synthetic probe constructed from a
    representative detail string MUST produce a valid `EvasionSignal`
    whose family attribute is the load-bearing short-name.

    Acceptance per ADR 0015 §Operational notes: "the analyzer
    correctly records that a probe occurred". W23+ runtime detection
    will construct `EvasionSignal` instances from real probe
    observations; the data shape must be ready before that.
    """
    signal = EvasionSignal(family=family, detail=detail)
    assert signal.family == family
    assert signal.detail == detail


def test_evasion_signal_rejects_unknown_family() -> None:
    """A typo or stale family short-name must be rejected at
    construction time. This is the canary's second safety net (the
    first being `test_evasion_family_taxonomy_matches_adr_0015`).
    """
    with pytest.raises(ValueError, match="Unknown evasion family"):
        EvasionSignal(family="not_a_real_family", detail="anything")


def test_evasion_signal_rejects_empty_detail() -> None:
    """A probe with no detail string would record an opaque signal
    that downstream W23+ classifiers could not act on. Reject at
    construction time so the canary's recorded shape stays useful.
    """
    with pytest.raises(ValueError, match="non-empty probe descriptor"):
        EvasionSignal(family="webdriver_presence", detail="")
