"""End-to-end PoC acceptance tests for T1 malicious canaries.

For each T1 canary under ``extensions/malicious/``, load its offline
``activation_report.json`` fixture, run the production detection registry
against it, and assert that every rule_id declared in the canary's
``LABEL.yaml`` ``expected_detections.must_fire`` list actually fires.

This wires the W7 PoC acceptance bar (``REFACTOR_OPTIMIZATION.md`` §10.7)
into CI so that detection-rule regressions on Must-class adversaries
(A1/A2/A4/A6) cannot ship silently.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.analysis_contracts import ActivationReport
from packages.analysis_contracts.detection import RuleExecutionStatus, Verdict
from packages.analysis_engine.rules.registry import get_production_rules
from packages.analysis_engine.runner import run_detection

REPO_ROOT = Path(__file__).resolve().parents[2]
MALICIOUS_ROOT = REPO_ROOT / "extensions" / "malicious"


def _t1_canaries() -> list[tuple[str, dict[str, object], Path]]:
    canaries: list[tuple[str, dict[str, object], Path]] = []
    for label_path in sorted(MALICIOUS_ROOT.glob("*/LABEL.yaml")):
        manifest = json.loads(label_path.read_text(encoding="utf-8"))
        if manifest.get("tier") != "T1":
            continue
        report_path = label_path.parent / "activation_report.json"
        if not report_path.exists():
            continue
        canaries.append((manifest["id"], manifest, report_path))
    return canaries


_CANARIES = _t1_canaries()


@pytest.mark.parametrize(
    ("canary_id", "manifest", "report_path"),
    _CANARIES,
    ids=[canary_id for canary_id, _, _ in _CANARIES],
)
def test_t1_canary_must_fire_rules_actually_fire(
    canary_id: str,
    manifest: dict[str, object],
    report_path: Path,
) -> None:
    activation_report = ActivationReport.model_validate_json(
        report_path.read_text(encoding="utf-8")
    )

    detection_report = run_detection(activation_report, get_production_rules())

    fired_rule_ids = {
        record.rule_id
        for record in detection_report.rules_executed
        if record.status == RuleExecutionStatus.FIRED
    }
    expected_must_fire = set(manifest["expected_detections"]["must_fire"])

    missing = expected_must_fire - fired_rule_ids
    assert not missing, (
        f"{canary_id}: expected rules to fire but they were silent: {sorted(missing)}; "
        f"fired={sorted(fired_rule_ids)}"
    )


@pytest.mark.parametrize(
    ("canary_id", "manifest", "report_path"),
    _CANARIES,
    ids=[canary_id for canary_id, _, _ in _CANARIES],
)
def test_t1_canary_must_not_fire_rules_stay_silent(
    canary_id: str,
    manifest: dict[str, object],
    report_path: Path,
) -> None:
    must_not_fire = set(manifest["expected_detections"].get("must_not_fire", []))
    if not must_not_fire:
        pytest.skip("canary declares no must_not_fire expectations")

    activation_report = ActivationReport.model_validate_json(
        report_path.read_text(encoding="utf-8")
    )
    detection_report = run_detection(activation_report, get_production_rules())

    fired_rule_ids = {
        record.rule_id
        for record in detection_report.rules_executed
        if record.status == RuleExecutionStatus.FIRED
    }
    leaked = must_not_fire & fired_rule_ids
    assert not leaked, (
        f"{canary_id}: rules fired that should have stayed silent: {sorted(leaked)}"
    )


@pytest.mark.parametrize(
    ("canary_id", "manifest", "report_path"),
    _CANARIES,
    ids=[canary_id for canary_id, _, _ in _CANARIES],
)
def test_t1_canary_verdict_is_not_clean(
    canary_id: str,
    manifest: dict[str, object],
    report_path: Path,
) -> None:
    """A T1 malicious canary that fires its expected rules must not roll up
    to ``CLEAN``. ``MALICIOUS`` or ``SUSPICIOUS`` are both acceptable
    (lifecycle gating may downgrade malicious to suspicious for non-PRODUCTION
    rules; T1 canaries here all map to PRODUCTION rules)."""

    activation_report = ActivationReport.model_validate_json(
        report_path.read_text(encoding="utf-8")
    )
    detection_report = run_detection(activation_report, get_production_rules())

    assert detection_report.verdict not in {
        Verdict.CLEAN,
        Verdict.CLEAN_WITH_NOTES,
    }, (
        f"{canary_id}: verdict={detection_report.verdict} "
        f"(expected MALICIOUS/SUSPICIOUS/INCONCLUSIVE)"
    )


def test_at_least_one_t1_canary_was_discovered() -> None:
    """Guard against an empty parametrize set masking a missing fixture tree."""

    assert _CANARIES, "no T1 canary fixtures discovered under extensions/malicious/"
