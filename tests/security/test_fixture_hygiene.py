from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MALICIOUS_ROOT = REPO_ROOT / "extensions" / "malicious"
ALLOWED_T3_REFERENCES = {
    MALICIOUS_ROOT,
    REPO_ROOT / "tests" / "security",
    REPO_ROOT / "documents" / "adrs" / "0004-malicious-fixture-policy.md",
    REPO_ROOT / "Makefile",
}


def _fixture_dirs() -> list[Path]:
    return sorted(
        entry
        for entry in MALICIOUS_ROOT.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    )


def _load_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_every_malicious_fixture_directory_has_a_manifest() -> None:
    fixture_dirs = _fixture_dirs()
    assert fixture_dirs, (
        "extensions/malicious/ must contain at least one fixture scaffold."
    )

    for fixture_dir in fixture_dirs:
        assert (fixture_dir / "LABEL.yaml").is_file(), (
            f"{fixture_dir.name} is missing LABEL.yaml"
        )


@pytest.mark.parametrize("fixture_dir", _fixture_dirs(), ids=lambda path: path.name)
def test_manifests_follow_the_repo_fixture_contract(fixture_dir: Path) -> None:
    manifest = _load_manifest(fixture_dir / "LABEL.yaml")

    assert manifest["id"] == fixture_dir.name
    assert manifest["tier"] in {"T1", "T2", "T3"}
    assert manifest["category"]["adversary_class"] in {
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
        "A6",
        "A7",
    }
    assert isinstance(manifest["category"]["taxonomy"], list)
    assert isinstance(manifest["expected_detections"]["must_fire"], list)
    assert isinstance(manifest["expected_detections"]["must_not_fire"], list)

    if manifest["tier"] == "T1":
        assert manifest["source"]["kind"] == "internal_canary"
        assert manifest["declawing"] is None


def test_t3_fixtures_are_not_referenced_outside_allowed_paths() -> None:
    t3_fixture_ids = {
        _load_manifest(fixture_dir / "LABEL.yaml")["id"]
        for fixture_dir in _fixture_dirs()
        if _load_manifest(fixture_dir / "LABEL.yaml")["tier"] == "T3"
    }
    assert not t3_fixture_ids, "T3 fixtures are not expected in the PoC scaffold."
    if not t3_fixture_ids:
        return

    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(
            allowed in path.parents or path == allowed
            for allowed in ALLOWED_T3_REFERENCES
        ):
            continue
        if path.suffix in {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".vsix"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for fixture_id in t3_fixture_ids:
            assert fixture_id not in text, f"T3 fixture {fixture_id} leaked into {path}"
