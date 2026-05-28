"""Sandbox-evasion signal taxonomy (ADR 0015 W22-5 contract).

This module is the W22-5 [GOAL sandbox-evasion-canary-fixture] anchor.
It carries the load-bearing taxonomy short-names + the canonical
signal data shape so the W22-5 canary fixture
(`tests/security/test_sandbox_evasion_canary.py`) and the future
W23+ runtime detection paths can both reference one source of truth.

The five families come from ADR 0015 §Sandbox-Evasion Pattern
Taxonomy:

- E1 ``webdriver_presence``       — ``navigator.webdriver`` interrogation
- E2 ``cdp_fingerprint``          — well-known CDP-leak global probes
- E3 ``timing_probe``             — ``performance.now()`` / ``Date.now()``
                                    jitter sampling
- E4 ``platform_identity``        — UA / ``navigator.platform`` checks
- E5 ``process_introspection``    — ``/proc`` reads for analyzer-
                                    characteristic process names

W22-5 scope (this module + the canary fixture): the family short-
names + the signal data shape are pinned. Detection / suppression
logic lands in W23+ per ADR 0015 §Implementation Roadmap and brings
its own recorder implementation; the W22-5 canary asserts on the
fixture-data level only (i.e., "a probe of family X would carry
the X short-name and a non-empty detail string").
"""

from __future__ import annotations

from dataclasses import dataclass

# Load-bearing: the W22-5 canary fixture asserts this tuple is
# byte-identical with the ADR 0015 taxonomy. A future rename forces
# a coordinated ADR amendment + canary update + this module update.
EVASION_FAMILY_TAXONOMY: tuple[str, ...] = (
    "webdriver_presence",
    "cdp_fingerprint",
    "timing_probe",
    "platform_identity",
    "process_introspection",
)


@dataclass(frozen=True)
class EvasionSignal:
    """The data shape an analyzer-side observer records when a probe occurs.

    Constructed in the canary fixture from synthetic probe data; the
    W23+ runtime detection paths will construct it from real probe
    observations.
    """

    family: str
    detail: str

    def __post_init__(self) -> None:
        if self.family not in EVASION_FAMILY_TAXONOMY:
            raise ValueError(
                f"Unknown evasion family {self.family!r}. "
                f"Must be one of {EVASION_FAMILY_TAXONOMY} per ADR 0015."
            )
        if not self.detail:
            raise ValueError(
                "EvasionSignal.detail must be a non-empty probe descriptor."
            )
