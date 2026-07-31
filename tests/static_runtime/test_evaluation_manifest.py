"""SMF corpus contract, safety, provenance, and parity tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from packages.analysis_contracts.static_evaluation import CorpusManifest, CorpusSample
from static_runtime.evaluation import hash_tree, validate_runtime_paths
from static_runtime.rule_inventory import build_rule_bundle_inventory

CORPUS_ROOT = Path(__file__).resolve().parents[1] / "static_corpus"


def test_starter_manifest_has_balanced_hashed_tuning_and_holdout_samples() -> None:
    manifest = CorpusManifest.model_validate_json(
        (CORPUS_ROOT / "manifest.json").read_bytes()
    )
    assert len(manifest.samples) == 12
    assert sum(sample.split == "tuning" for sample in manifest.samples) == 8
    assert sum(sample.split == "holdout" for sample in manifest.samples) == 4
    assert (
        sum(
            sample.label in {"malicious_behavior", "vulnerable"}
            for sample in manifest.samples
        )
        == 6
    )
    assert {
        "artifact_role",
        "network_context",
        "manifest",
        "coverage",
        "dependency",
        "obfuscation",
        "credential_flow",
        "download_flow",
        "webview",
        "workspace_trust",
        "dormancy_platform",
    } <= {family for sample in manifest.samples for family in sample.families}
    assert (
        sum(
            sample.label in {"benign", "coverage_control"}
            for sample in manifest.samples
        )
        == 6
    )
    for sample in manifest.samples:
        assert (
            hash_tree(CORPUS_ROOT / "samples" / sample.relative_path) == sample.sha256
        )

    inventory = build_rule_bundle_inventory()
    manifest.validate_rule_ids(
        {
            entry.rule_id
            for entry in (*inventory.inhouse_rules, *inventory.semgrep_rules)
        }
    )


def test_sample_rejects_traversal_hash_and_contradictory_expectations() -> None:
    base = {
        "sample_id": "bad",
        "relative_path": "sample",
        "sha256": "0" * 64,
        "split": "tuning",
        "label": "benign",
        "families": ["coverage"],
        "variant": "control",
        "provenance": "repository fixture",
        "safety_state": "benign_control",
        "expected_gate": "allow",
    }
    with pytest.raises(ValidationError):
        CorpusSample.model_validate({**base, "relative_path": "../escape"})
    with pytest.raises(ValidationError):
        CorpusSample.model_validate({**base, "relative_path": "/absolute/sample"})
    with pytest.raises(ValidationError):
        CorpusSample.model_validate({**base, "sha256": "ABC"})
    with pytest.raises(ValidationError):
        CorpusSample.model_validate(
            {
                **base,
                "must_fire": ["extrace.s1.generic_publisher"],
                "must_not_fire": ["extrace.s1.generic_publisher"],
            }
        )

    for required_field in ("sha256", "provenance", "safety_state"):
        missing = dict(base)
        missing.pop(required_field)
        with pytest.raises(ValidationError):
            CorpusSample.model_validate(missing)


def test_manifest_rejects_duplicate_ids_and_unknown_rules() -> None:
    document = json.loads((CORPUS_ROOT / "manifest.json").read_text(encoding="utf-8"))
    document["samples"].append(dict(document["samples"][0]))
    with pytest.raises(ValidationError):
        CorpusManifest.model_validate(document)

    manifest = CorpusManifest.model_validate_json(
        (CORPUS_ROOT / "manifest.json").read_bytes()
    )
    manifest.samples[0].must_fire.append("extrace.unknown.rule")
    with pytest.raises(ValueError, match="unknown rule ids"):
        manifest.validate_rule_ids(set())


def test_evaluator_runtime_paths_stay_in_mounts(tmp_path: Path) -> None:
    corpus_mount = tmp_path / "corpus"
    results_mount = tmp_path / "results"
    validate_runtime_paths(
        manifest_path=corpus_mount / "manifest.json",
        corpus_root=corpus_mount / "samples",
        output_json=results_mount / "all.json",
        output_markdown=results_mount / "all.md",
        corpus_mount=corpus_mount,
        results_mount=results_mount,
    )
    with pytest.raises(ValueError, match="manifest path"):
        validate_runtime_paths(
            manifest_path=tmp_path / "outside.json",
            corpus_root=corpus_mount / "samples",
            output_json=results_mount / "all.json",
            output_markdown=results_mount / "all.md",
            corpus_mount=corpus_mount,
            results_mount=results_mount,
        )
    with pytest.raises(ValueError, match="JSON output"):
        validate_runtime_paths(
            manifest_path=corpus_mount / "manifest.json",
            corpus_root=corpus_mount / "samples",
            output_json=tmp_path / "outside.json",
            output_markdown=results_mount / "all.md",
            corpus_mount=corpus_mount,
            results_mount=results_mount,
        )
