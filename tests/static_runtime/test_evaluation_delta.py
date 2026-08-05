"""SAP-6 evaluation delta contracts, comparison, and path safety."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from packages.analysis_contracts.static_detection import (
    StaticGateDecision,
    StaticScanCoverage,
)
from packages.analysis_contracts.static_evaluation import (
    EvaluationArtifactSummary,
    EvaluationResult,
    IntegerDelta,
    RuleMetric,
    SampleEvaluation,
)
from scripts.static_eval_delta import build_delta, validate_paths

_TUNING_IDS = [
    "tuning-artifact-native",
    "tuning-artifact-png",
    "tuning-network-runtime",
    "tuning-doc-url",
    "tuning-obfuscation",
    "tuning-credential-flow",
    "tuning-manifest-malformed",
    "tuning-clean",
    "tuning-transitive-loader",
    "tuning-echo-deduplication",
]
_HOLDOUT_IDS = [
    "holdout-download-exec",
    "holdout-webview-control",
    "holdout-workspace-process",
    "holdout-platform-control",
]


def _metric(*, tp: int, fp: int, fn: int, tn: int) -> RuleMetric:
    precision = tp / (tp + fp) if tp + fp else "not_applicable"
    recall = tp / (tp + fn) if tp + fn else "not_applicable"
    false_positive_rate = fp / (fp + tn) if fp + tn else "not_applicable"
    noise = fp / (tp + fp) if tp + fp else "not_applicable"
    return RuleMetric(
        key="samples",
        true_positive=tp,
        false_positive=fp,
        false_negative=fn,
        true_negative=tn,
        precision=precision,
        recall=recall,
        false_positive_rate=false_positive_rate,
        noise=noise,
    )


def _sample(sample_id: str, *, candidate: bool) -> SampleEvaluation:
    split = "holdout" if sample_id.startswith("holdout-") else "tuning"
    expected = StaticGateDecision.ALLOW
    observed = expected
    fired: list[str] = []
    label = "benign"
    coverage = StaticScanCoverage(files_discovered=2, files_scanned=2, files_parsed=2)
    summary = EvaluationArtifactSummary(
        retained_finding_count=0,
        artifact_dispositions={"deep_scan": 2},
        artifact_reachability={"direct": 1, "none": 1},
        capabilities=[
            "artifact_inventory",
            "finding_deduplication",
            "reachability",
        ],
    )
    if sample_id == "tuning-artifact-native":
        label = "coverage_control"
        fired = ["extrace.s3.embedded_native_binary"] if not candidate else []
        observed = StaticGateDecision.WARN if not candidate else expected
    elif sample_id == "tuning-network-runtime":
        label = "malicious_behavior"
        expected = observed = StaticGateDecision.WARN
        fired = ["extrace.s5.suspicious_network_endpoint"]
    elif sample_id == "tuning-doc-url":
        fired = [] if candidate else ["extrace.s5.suspicious_network_endpoint"]
        observed = expected if candidate else StaticGateDecision.WARN
    elif sample_id in {
        "tuning-obfuscation",
        "tuning-credential-flow",
        "holdout-download-exec",
        "holdout-workspace-process",
    }:
        label = "malicious_behavior"
        expected = observed = StaticGateDecision.WARN
        fired = [f"extrace.test.{sample_id}"]
    elif sample_id == "tuning-manifest-malformed":
        label = "coverage_control"
        expected = observed = StaticGateDecision.INCONCLUSIVE
        coverage.coverage_reasons = ["manifest_malformed"]
    elif sample_id == "tuning-transitive-loader":
        label = "malicious_behavior"
        expected = StaticGateDecision.WARN
        observed = expected if candidate else StaticGateDecision.ALLOW
        fired = ["extrace.sg.eval"] if candidate else []
        summary = summary.model_copy(
            update={
                "retained_finding_count": int(candidate),
                "artifact_dispositions": {"deep_scan": 4},
                "artifact_reachability": {"direct": 1, "transitive": 3},
            }
        )
    elif sample_id == "tuning-echo-deduplication":
        label = "coverage_control"
        expected = observed = StaticGateDecision.WARN
        fired = ["extrace.sg.eval"]
        summary = summary.model_copy(
            update={
                "retained_finding_count": 1,
                "suppressed_findings_by_reason": (
                    {"vendor_echo": 1} if candidate else {}
                ),
            }
        )
    return SampleEvaluation(
        sample_id=sample_id,
        split=split,
        label=label,
        observed_gate=observed,
        expected_gate=expected,
        fired_rule_ids=fired,
        missing_rule_ids=(
            ["extrace.sg.eval"]
            if sample_id == "tuning-transitive-loader" and not candidate
            else []
        ),
        artifact_summary=summary,
        coverage=coverage,
        duration_ms=100,
        tool_duration_ms={"inhouse": 5, "semgrep": 90},
        passed=candidate or observed is expected,
        errors=(
            ["missing:extrace.sg.eval", "gate:allow!=expected:warn"]
            if sample_id == "tuning-transitive-loader" and not candidate
            else [f"gate:{observed.value}!=expected:{expected.value}"]
            if observed is not expected
            else []
        ),
    )


def _result(split: str, *, candidate: bool, run: int) -> EvaluationResult:
    ids = (
        _TUNING_IDS
        if split == "tuning"
        else _HOLDOUT_IDS
        if split == "holdout"
        else [*_TUNING_IDS, *_HOLDOUT_IDS]
    )
    samples = [_sample(sample_id, candidate=candidate) for sample_id in ids]
    errors = [
        f"{sample.sample_id}:{error}" for sample in samples for error in sample.errors
    ]
    return EvaluationResult(
        evaluation_id=f"{'candidate' if candidate else 'baseline'}-{split}-{run}",
        rules_bundle_fingerprint=("b" if candidate else "a") * 64,
        corpus_manifest_sha256="c" * 64,
        sample_results=samples,
        sample_metric=(
            _metric(tp=6, fp=0, fn=0, tn=5)
            if candidate
            else _metric(tp=5, fp=1, fn=1, tn=4)
        ),
        coverage_summary=StaticScanCoverage(
            files_discovered=len(samples) * 2,
            files_scanned=len(samples) * 2,
            files_parsed=len(samples) * 2,
            coverage_reasons=(
                ["manifest_malformed"] if "tuning-manifest-malformed" in ids else []
            ),
        ),
        runtime_summary={
            "sample_count": len(samples),
            "p50_ms": 100 + run,
            "p95_ms": 120 + run,
            "total_ms": (100 + run) * len(samples),
        },
        errors=errors,
    )


def _write_result(path: Path, result: EvaluationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.model_dump_json(), encoding="utf-8")


def _write_run_set(directory: Path, *, candidate: bool) -> None:
    _write_result(
        directory / "tuning.json", _result("tuning", candidate=candidate, run=0)
    )
    _write_result(
        directory / "holdout.json", _result("holdout", candidate=candidate, run=0)
    )
    for run in range(1, 4):
        _write_result(
            directory / f"all-{run}.json",
            _result("all", candidate=candidate, run=run),
        )


def test_legacy_sample_defaults_artifact_measurement_capabilities() -> None:
    payload = _sample("tuning-clean", candidate=True).model_dump(mode="json")
    payload.pop("artifact_summary")
    parsed = SampleEvaluation.model_validate(payload)
    assert parsed.artifact_summary.retained_finding_count == 0
    assert parsed.artifact_summary.capabilities == []


def test_integer_delta_rejects_inconsistent_value() -> None:
    with pytest.raises(ValidationError, match="candidate minus baseline"):
        IntegerDelta(baseline=1, candidate=3, delta=1)


def test_delta_compares_three_deterministic_runs_and_acceptance(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run_set(baseline, candidate=False)
    _write_run_set(candidate, candidate=True)

    result = build_delta(
        baseline_dir=baseline,
        candidate_dir=candidate,
        baseline_ref="7b8b4b2",
        candidate_ref="sap6",
    )

    assert result.passed is True
    assert all(result.acceptance_checks.values())
    assert list(result.acceptance_checks) == sorted(result.acceptance_checks)
    all_delta = next(item for item in result.splits if item.split == "all")
    assert [item.sample_id for item in all_delta.sample_deltas] == sorted(
        item.sample_id for item in all_delta.sample_deltas
    )
    assert all_delta.suppression_counts["vendor_echo"].delta == 1
    assert all_delta.runtime["p95_ms"].baseline_median_ms == 122
    assert all_delta.runtime["p95_ms"].candidate_median_ms == 122
    transitive = next(
        item
        for item in all_delta.sample_deltas
        if item.sample_id == "tuning-transitive-loader"
    )
    assert transitive.added_rule_ids == ["extrace.sg.eval"]


def test_delta_rejects_sample_identity_mismatch(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run_set(baseline, candidate=False)
    _write_run_set(candidate, candidate=True)
    document = json.loads((candidate / "tuning.json").read_text(encoding="utf-8"))
    document["sample_results"].pop()
    (candidate / "tuning.json").write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="sample ids differ"):
        build_delta(
            baseline_dir=baseline,
            candidate_dir=candidate,
            baseline_ref="7b8b4b2",
            candidate_ref="sap6",
        )


def test_delta_rejects_split_mismatch(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run_set(baseline, candidate=False)
    _write_run_set(candidate, candidate=True)
    document = json.loads((candidate / "tuning.json").read_text(encoding="utf-8"))
    document["sample_results"][0]["split"] = "holdout"
    (candidate / "tuning.json").write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="split mismatch"):
        build_delta(
            baseline_dir=baseline,
            candidate_dir=candidate,
            baseline_ref="7b8b4b2",
            candidate_ref="sap6",
        )


def test_delta_rejects_broken_fingerprint(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run_set(baseline, candidate=False)
    _write_run_set(candidate, candidate=True)
    document = json.loads((candidate / "holdout.json").read_text(encoding="utf-8"))
    document["rules_bundle_fingerprint"] = "broken"
    (candidate / "holdout.json").write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValidationError, match="lowercase SHA-256"):
        build_delta(
            baseline_dir=baseline,
            candidate_dir=candidate,
            baseline_ref="7b8b4b2",
            candidate_ref="sap6",
        )


def test_delta_paths_stay_under_ignored_results_root(tmp_path: Path) -> None:
    root = tmp_path / "output"
    validate_paths(
        baseline_dir=root / "baseline",
        candidate_dir=root / "candidate",
        output_json=root / "delta.json",
        output_markdown=root / "delta.md",
        results_root=root,
    )
    with pytest.raises(ValueError, match="baseline path"):
        validate_paths(
            baseline_dir=tmp_path / "outside",
            candidate_dir=root / "candidate",
            output_json=root / "delta.json",
            output_markdown=root / "delta.md",
            results_root=root,
        )
    with pytest.raises(ValueError, match=r"must use \.json and \.md suffixes"):
        validate_paths(
            baseline_dir=root / "baseline",
            candidate_dir=root / "candidate",
            output_json=root / "delta.txt",
            output_markdown=root / "delta.md",
            results_root=root,
        )
