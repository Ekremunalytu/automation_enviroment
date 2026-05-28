"""W22-4 sandbox-evasion defense ADR existence + content invariants (ADR 0015).

Pins the taxonomy + policy stance recorded in
`documents/adrs/0015-sandbox-evasion-defense-policy.md` so the W22-5
canary fixture (`tests/security/test_sandbox_evasion_canary.py`) and
the W23+ runtime implementation both inherit a stable, machine-
checkable contract for the load-bearing family short-names.

What's pinned:

1. The ADR 0015 file exists at the expected path so a future edit
   that removes or relocates it trips this gate before the W22-5
   canary's per-family assertions regress.
2. The ADR 0015 body carries each family's stable short-name
   (`webdriver_presence`, `cdp_fingerprint`, `timing_probe`,
   `platform_identity`, `process_introspection`) so a rename would
   force an ADR amendment alongside the canary update.
3. The ADR 0015 body cites ADR 0002 §3 as the promotion source and
   states the W23+ implementation deferral so future iters cannot
   silently strip the roadmap context.

What's intentionally NOT pinned here:

- The W23+ runtime implementation details (launcher overrides,
  page-init scripts, signal recorders) are out of scope until those
  modules land and bring their own dedicated regression tests.
- The W22-5 canary's per-test assertions; those live with W22-5
  itself at `tests/security/test_sandbox_evasion_canary.py`.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_PATH = REPO_ROOT / "documents" / "adrs" / "0015-sandbox-evasion-defense-policy.md"


def test_adr_0015_exists() -> None:
    """ADR 0015 file must remain at the expected path so the
    W22-5 canary fixture has a documented source-of-truth for the
    family short-names it asserts on.
    """
    assert ADR_PATH.exists(), (
        f"ADR 0015 not found at {ADR_PATH.relative_to(REPO_ROOT)}. "
        "W22-5 [GOAL sandbox-evasion-canary-fixture] depends on the "
        "taxonomy recorded here — restore the ADR before re-running."
    )


def test_adr_0015_documents_taxonomy_short_names() -> None:
    """ADR 0015 must explicitly carry every family's stable short-
    name + the ADR 0002 §3 promotion link + the W23+ deferral so a
    future rename / scope flip surfaces here alongside the W22-5
    canary's per-family assertions.
    """
    text = ADR_PATH.read_text(encoding="utf-8")
    required_tokens = (
        # Family short-names — load-bearing for W22-5 canary fixture.
        "webdriver_presence",
        "cdp_fingerprint",
        "timing_probe",
        "platform_identity",
        "process_introspection",
        # Family enumeration shape (E1..E5).
        "E1",
        "E2",
        "E3",
        "E4",
        "E5",
        # Promotion source + roadmap deferral.
        "ADR 0002",
        "W23",
        # Defense surface primitives.
        "page.addInitScript",
        # Canary entry-point reference for W22-5 traceability.
        "test_sandbox_evasion_canary.py",
    )
    missing = [token for token in required_tokens if token not in text]
    assert not missing, (
        "ADR 0015 must carry the taxonomy short-names + promotion "
        "source + W23+ deferral + canary entry-point so the W22-5 "
        f"fixture inherits a stable contract. Missing tokens: {missing!r}."
    )
