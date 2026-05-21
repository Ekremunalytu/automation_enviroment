"""W14-4 fixture-drift detector: every committed ``activation_report.json``
fixture must validate cleanly through ``ActivationReport.model_validate``.

Closes the fixture-side surface of `[FOLLOWUP
evidence-event-kind-raw-context-invariant]`. The W14-4 pull surfaced
five drifted evidence events across three malicious-canary fixtures
+ two inline test builders (file-kind events missing
``raw_context.event_class``); the drift was caught only because
unrelated security tests happened to load those fixtures. This gate
walks the full fixture surface so a future producer or hand-authored
fixture drift fails fast and locally.

The parametrize id includes the relative path so a CI failure points
straight at the offending fixture.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from packages.analysis_contracts import ActivationReport


REPO_ROOT = Path(__file__).resolve().parents[3]


def _collect_fixture_reports() -> list[Path]:
    """Return every commit-included ``activation_report*.json`` fixture.

    Two surfaces are walked:
    + ``tests/platform/contracts/fixtures/activation_reports/*.json`` —
      benign / canonical fixtures used by detection-engine + contract
      regression tests.
    + ``extensions/*/activation_report.json`` and
      ``extensions/malicious/*/activation_report.json`` — malicious-canary
      fixtures that the rule-validation lane consumes.

    Generated artifacts under ``output/`` are intentionally skipped
    (local-only, not committed).
    """
    contract_fixtures = sorted(
        (
            REPO_ROOT
            / "tests"
            / "platform"
            / "contracts"
            / "fixtures"
            / "activation_reports"
        ).glob("*.json")
    )
    malicious_canaries = sorted(
        REPO_ROOT.glob("extensions/malicious/*/activation_report.json")
    )
    benign_canaries = sorted(
        REPO_ROOT.glob("extensions/extrace.*/activation_report.json")
    )
    return contract_fixtures + malicious_canaries + benign_canaries


_FIXTURE_PATHS = _collect_fixture_reports()


@pytest.mark.parametrize(
    "fixture_path",
    _FIXTURE_PATHS,
    ids=[path.relative_to(REPO_ROOT).as_posix() for path in _FIXTURE_PATHS],
)
def test_fixture_activation_report_validates_under_w14_4_invariant(
    fixture_path: Path,
) -> None:
    """W14-4: load the fixture and validate it through ``ActivationReport``.

    Surfaces three failure modes:
    + Pydantic ``ValidationError`` on any field (kind↔event_class
      invariant, discriminator mismatch, missing required field).
    + JSON syntax failure.
    + Non-dict top-level payload.
    """
    import json

    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), (
        f"{fixture_path.relative_to(REPO_ROOT)} must contain a JSON object "
        "at the top level"
    )
    ActivationReport.model_validate(payload)


def test_fixture_surface_is_not_empty() -> None:
    """Pin that the gate above is iterating over at least one fixture.

    Without this, a refactor that moves the fixture directory would
    silently pass the parametrize-driven test by collecting zero cases.
    """
    assert _FIXTURE_PATHS, (
        "No activation_report.json fixtures found under "
        "tests/platform/contracts/fixtures/ or extensions/. The W14-4 "
        "drift detector cannot operate on an empty surface."
    )
