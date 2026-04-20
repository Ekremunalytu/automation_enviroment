from __future__ import annotations

from pathlib import Path

import pytest

from tests.security.helpers import MALICIOUS_ROOT, analyze_fixture, load_manifest


def _fixture_dirs() -> list[Path]:
    return sorted(
        entry
        for entry in MALICIOUS_ROOT.iterdir()
        if entry.is_dir() and (entry / "LABEL.yaml").exists()
    )


@pytest.mark.parametrize("fixture_dir", _fixture_dirs(), ids=lambda path: path.name)
def test_rule_validation_matches_manifest_expectations(fixture_dir: Path) -> None:
    manifest = load_manifest(fixture_dir)
    bundle = analyze_fixture(fixture_dir)
    fired_rule_ids = {finding.rule_id for finding in bundle.detection_report.findings}

    expected = manifest["expected_detections"]
    must_fire = expected["must_fire"]
    must_not_fire = expected["must_not_fire"]

    assert set(must_fire).issubset(fired_rule_ids)
    assert set(must_not_fire).isdisjoint(fired_rule_ids)
