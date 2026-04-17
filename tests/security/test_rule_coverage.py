from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MALICIOUS_ROOT = REPO_ROOT / "extensions" / "malicious"
EXPECTED_POC_CLASSES = {"A1", "A2", "A4", "A6"}


def _manifests() -> list[dict[str, object]]:
    manifests: list[dict[str, object]] = []
    for label_path in sorted(MALICIOUS_ROOT.glob("*/LABEL.yaml")):
        manifests.append(json.loads(label_path.read_text(encoding="utf-8")))
    return manifests


def test_poc_canary_set_covers_the_expected_adversary_classes() -> None:
    manifests = _manifests()
    classes = {
        manifest["category"]["adversary_class"]
        for manifest in manifests
        if manifest["tier"] == "T1"
    }
    assert EXPECTED_POC_CLASSES.issubset(classes)


def test_every_t1_fixture_declares_at_least_one_detection_contract() -> None:
    manifests = _manifests()
    t1_manifests = [manifest for manifest in manifests if manifest["tier"] == "T1"]

    assert t1_manifests, "Week 5 requires at least one T1 canary manifest."
    for manifest in t1_manifests:
        must_fire = manifest["expected_detections"]["must_fire"]
        assert (
            must_fire
        ), f"{manifest['id']} must declare at least one rule expectation."


def test_live_fixtures_are_not_present_in_the_poc_scaffold() -> None:
    manifests = _manifests()
    assert all(manifest["tier"] != "T3" for manifest in manifests)
