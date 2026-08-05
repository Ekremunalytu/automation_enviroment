"""Compare deterministic static-evaluation baseline and candidate artifacts."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from packages.analysis_contracts.static_evaluation import (
    EvaluationCapability,
    EvaluationDeltaResult,
    EvaluationResult,
    IntegerDelta,
    RuntimeDelta,
    SampleEvaluation,
    SampleEvaluationDelta,
    SplitEvaluationDelta,
)

_SPLITS = ("tuning", "holdout", "all")
_ALLOWED_CANDIDATE_COVERAGE_REASONS = frozenset({"manifest_malformed"})
_EXPECTED_SAMPLE_GATES = {
    "tuning-artifact-native": "allow",
    "tuning-doc-url": "allow",
    "tuning-network-runtime": "warn",
    "tuning-transitive-loader": "warn",
}


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _load_result(path: Path) -> EvaluationResult:
    return EvaluationResult.model_validate_json(path.read_bytes())


def _load_split_runs(directory: Path, split: str) -> list[EvaluationResult]:
    if split == "all":
        paths = sorted(directory.glob("all*.json"))
    else:
        paths = [directory / f"{split}.json"]
    if not paths or any(not path.is_file() for path in paths):
        raise ValueError(f"missing {split} evaluation JSON in {directory}")
    if len(paths) > 10:
        raise ValueError(f"too many {split} evaluation runs in {directory}")
    return [_load_result(path) for path in paths]


def _normalized_runs_match(runs: list[EvaluationResult]) -> bool:
    first = runs[0].normalized_payload()
    return all(run.normalized_payload() == first for run in runs[1:])


def _samples_by_id(result: EvaluationResult) -> dict[str, SampleEvaluation]:
    samples = {sample.sample_id: sample for sample in result.sample_results}
    if len(samples) != len(result.sample_results):
        raise ValueError("evaluation result contains duplicate sample ids")
    return samples


def _stable_sample_payload(sample: SampleEvaluation) -> dict[str, object]:
    payload = sample.model_dump(mode="json")
    payload.pop("duration_ms", None)
    payload.pop("tool_duration_ms", None)
    return payload


def _validate_revision_runs(
    runs: dict[str, list[EvaluationResult]], *, label: str
) -> None:
    results = [run for split_runs in runs.values() for run in split_runs]
    if len({run.corpus_manifest_sha256 for run in results}) != 1:
        raise ValueError(f"{label} corpus fingerprint differs across splits")
    if len({run.rules_bundle_fingerprint for run in results}) != 1:
        raise ValueError(f"{label} rules fingerprint differs across splits")

    all_samples = _samples_by_id(runs["all"][0])
    for split in ("tuning", "holdout"):
        split_samples = _samples_by_id(runs[split][0])
        if any(sample.split != split for sample in split_samples.values()):
            raise ValueError(f"{label} {split} result contains a split mismatch")
        expected = {
            sample_id: sample
            for sample_id, sample in all_samples.items()
            if sample.split == split
        }
        if split_samples.keys() != expected.keys():
            raise ValueError(f"{label} {split} sample ids differ from all")
        for sample_id in split_samples:
            if _stable_sample_payload(split_samples[sample_id]) != (
                _stable_sample_payload(expected[sample_id])
            ):
                raise ValueError(f"{label} {split} sample {sample_id} differs from all")


def _capabilities(samples: Iterable[SampleEvaluation]) -> list[EvaluationCapability]:
    return sorted(
        {
            capability
            for sample in samples
            for capability in sample.artifact_summary.capabilities
        }
    )


def _integer_delta(baseline: int, candidate: int) -> IntegerDelta:
    return IntegerDelta(
        baseline=baseline,
        candidate=candidate,
        delta=candidate - baseline,
    )


def _runtime_delta(baseline: Iterable[int], candidate: Iterable[int]) -> RuntimeDelta:
    baseline_median = int(statistics.median(list(baseline)))
    candidate_median = int(statistics.median(list(candidate)))
    return RuntimeDelta(
        baseline_median_ms=baseline_median,
        candidate_median_ms=candidate_median,
        delta_ms=candidate_median - baseline_median,
    )


def _sum_map(samples: Iterable[SampleEvaluation], attribute: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for sample in samples:
        counts.update(getattr(sample.artifact_summary, attribute))
    return dict(sorted(counts.items()))


def _map_deltas(
    baseline: dict[str, int], candidate: dict[str, int]
) -> dict[str, IntegerDelta]:
    return {
        key: _integer_delta(baseline.get(key, 0), candidate.get(key, 0))
        for key in sorted(set(baseline) | set(candidate))
    }


def _sample_delta(
    baseline: SampleEvaluation, candidate: SampleEvaluation
) -> SampleEvaluationDelta:
    baseline_rules = set(baseline.fired_rule_ids)
    candidate_rules = set(candidate.fired_rule_ids)
    return SampleEvaluationDelta(
        sample_id=candidate.sample_id,
        split=candidate.split,
        baseline_label=baseline.label,
        candidate_label=candidate.label,
        baseline_expected_gate=baseline.expected_gate,
        candidate_expected_gate=candidate.expected_gate,
        baseline_observed_gate=baseline.observed_gate,
        candidate_observed_gate=candidate.observed_gate,
        added_rule_ids=sorted(candidate_rules - baseline_rules),
        removed_rule_ids=sorted(baseline_rules - candidate_rules),
        retained_findings=_integer_delta(
            baseline.artifact_summary.retained_finding_count,
            candidate.artifact_summary.retained_finding_count,
        ),
        suppressed_findings=_integer_delta(
            sum(baseline.artifact_summary.suppressed_findings_by_reason.values()),
            sum(candidate.artifact_summary.suppressed_findings_by_reason.values()),
        ),
        candidate_passed=candidate.passed,
    )


def _build_split_delta(
    split: str,
    baseline_runs: list[EvaluationResult],
    candidate_runs: list[EvaluationResult],
) -> SplitEvaluationDelta:
    baseline = baseline_runs[0]
    candidate = candidate_runs[0]
    baseline_samples = _samples_by_id(baseline)
    candidate_samples = _samples_by_id(candidate)
    if baseline_samples.keys() != candidate_samples.keys():
        raise ValueError(f"{split} sample ids differ between baseline and candidate")
    for sample_id in baseline_samples:
        if baseline_samples[sample_id].split != candidate_samples[sample_id].split:
            raise ValueError(f"{split} split differs for sample {sample_id}")

    coverage_fields = (
        "files_discovered",
        "files_scanned",
        "files_parsed",
        "bytes_considered",
        "bytes_read",
    )
    runtime_keys = sorted(
        set().union(
            *(run.runtime_summary.keys() for run in baseline_runs),
            *(run.runtime_summary.keys() for run in candidate_runs),
        )
    )
    numeric_runtime_keys = [
        key
        for key in runtime_keys
        if key != "sample_count"
        if all(
            isinstance(run.runtime_summary.get(key), int)
            for run in (*baseline_runs, *candidate_runs)
        )
    ]
    return SplitEvaluationDelta(
        split=split,
        sample_count=len(candidate_samples),
        baseline_sample_metric=baseline.sample_metric,
        candidate_sample_metric=candidate.sample_metric,
        coverage_counts={
            field: _integer_delta(
                int(getattr(baseline.coverage_summary, field)),
                int(getattr(candidate.coverage_summary, field)),
            )
            for field in coverage_fields
        },
        artifact_dispositions=_map_deltas(
            _sum_map(baseline_samples.values(), "artifact_dispositions"),
            _sum_map(candidate_samples.values(), "artifact_dispositions"),
        ),
        artifact_reachability=_map_deltas(
            _sum_map(baseline_samples.values(), "artifact_reachability"),
            _sum_map(candidate_samples.values(), "artifact_reachability"),
        ),
        suppression_counts=_map_deltas(
            _sum_map(baseline_samples.values(), "suppressed_findings_by_reason"),
            _sum_map(candidate_samples.values(), "suppressed_findings_by_reason"),
        ),
        runtime={
            key: _runtime_delta(
                [int(run.runtime_summary[key]) for run in baseline_runs],
                [int(run.runtime_summary[key]) for run in candidate_runs],
            )
            for key in numeric_runtime_keys
        },
        sample_deltas=[
            _sample_delta(baseline_samples[sample_id], candidate_samples[sample_id])
            for sample_id in sorted(candidate_samples)
        ],
    )


def _numeric_metric(value: float | str) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _allowed_baseline_error(error: str) -> bool:
    detail = error.split(":", 1)[1] if ":" in error else error
    return detail.startswith(("missing:", "unexpected:", "gate:"))


def build_delta(
    *,
    baseline_dir: Path,
    candidate_dir: Path,
    baseline_ref: str,
    candidate_ref: str,
) -> EvaluationDeltaResult:
    baseline_runs = {split: _load_split_runs(baseline_dir, split) for split in _SPLITS}
    candidate_runs = {
        split: _load_split_runs(candidate_dir, split) for split in _SPLITS
    }
    _validate_revision_runs(baseline_runs, label="baseline")
    _validate_revision_runs(candidate_runs, label="candidate")
    baseline_all = baseline_runs["all"]
    candidate_all = candidate_runs["all"]
    baseline = baseline_all[0]
    candidate = candidate_all[0]
    baseline_samples = _samples_by_id(baseline)
    candidate_samples = _samples_by_id(candidate)

    structural_errors: list[str] = []
    if baseline_samples.keys() != candidate_samples.keys():
        structural_errors.append("all:sample_ids_differ")
    if any(not _allowed_baseline_error(error) for error in baseline.errors):
        structural_errors.append("baseline:non_expectation_error")

    baseline_recall = _numeric_metric(baseline.sample_metric.recall)
    candidate_recall = _numeric_metric(candidate.sample_metric.recall)
    baseline_fpr = _numeric_metric(baseline.sample_metric.false_positive_rate)
    candidate_fpr = _numeric_metric(candidate.sample_metric.false_positive_rate)
    baseline_noise = _numeric_metric(baseline.sample_metric.noise)
    candidate_noise = _numeric_metric(candidate.sample_metric.noise)
    candidate_coverage_reasons = {
        reason
        for sample in candidate.sample_results
        for reason in sample.coverage.coverage_reasons
    }

    sample_gate_checks = {
        sample_id: (
            sample_id in candidate_samples
            and candidate_samples[sample_id].observed_gate.value == expected_gate
        )
        for sample_id, expected_gate in _EXPECTED_SAMPLE_GATES.items()
    }
    transitive = candidate_samples.get("tuning-transitive-loader")
    dedupe = candidate_samples.get("tuning-echo-deduplication")
    all_candidate_samples = list(candidate_samples.values())
    candidate_runtime_values = [
        value
        for run in candidate_all
        for sample in run.sample_results
        for value in (sample.duration_ms, *sample.tool_duration_ms.values())
    ]
    checks = {
        "baseline_three_run_determinism": len(baseline_all) == 3
        and _normalized_runs_match(baseline_all),
        "candidate_three_run_determinism": len(candidate_all) == 3
        and _normalized_runs_match(candidate_all),
        "candidate_expectations_pass": not candidate.errors
        and all(sample.passed for sample in all_candidate_samples),
        "candidate_sample_count_14": len(candidate_samples) == 14,
        "candidate_tuning_count_10": len(candidate_runs["tuning"][0].sample_results)
        == 10,
        "candidate_holdout_count_4": len(candidate_runs["holdout"][0].sample_results)
        == 4,
        "same_final_corpus": baseline.corpus_manifest_sha256
        == candidate.corpus_manifest_sha256,
        "recall_not_regressed": baseline_recall is not None
        and candidate_recall is not None
        and candidate_recall >= baseline_recall,
        "false_positive_rate_not_higher": baseline_fpr is not None
        and candidate_fpr is not None
        and candidate_fpr <= baseline_fpr,
        "noise_not_higher": baseline_noise is not None
        and candidate_noise is not None
        and candidate_noise <= baseline_noise,
        "holdout_preserved": all(
            sample.passed for sample in candidate_runs["holdout"][0].sample_results
        ),
        "coverage_reasons_expected": candidate_coverage_reasons
        <= _ALLOWED_CANDIDATE_COVERAGE_REASONS,
        "runtime_inside_600s": bool(candidate_runtime_values)
        and max(candidate_runtime_values) <= 600_000,
        "native_marker_allow": sample_gate_checks["tuning-artifact-native"],
        "documentation_url_allow": sample_gate_checks["tuning-doc-url"],
        "runtime_endpoint_warn": sample_gate_checks["tuning-network-runtime"],
        "transitive_loader_warn": sample_gate_checks["tuning-transitive-loader"],
        "transitive_loader_selected": transitive is not None
        and "extrace.sg.eval" in transitive.fired_rule_ids
        and transitive.artifact_summary.artifact_reachability.get("transitive", 0) > 0
        and transitive.artifact_summary.artifact_dispositions.get("deep_scan", 0) > 0,
        "exact_echo_suppressed": dedupe is not None
        and dedupe.artifact_summary.suppressed_findings_by_reason.get("vendor_echo", 0)
        > 0,
    }
    errors = [
        *structural_errors,
        *(key for key, passed in checks.items() if not passed),
    ]
    return EvaluationDeltaResult(
        baseline_ref=baseline_ref,
        candidate_ref=candidate_ref,
        baseline_rules_bundle_fingerprint=baseline.rules_bundle_fingerprint,
        candidate_rules_bundle_fingerprint=candidate.rules_bundle_fingerprint,
        baseline_corpus_manifest_sha256=baseline.corpus_manifest_sha256,
        candidate_corpus_manifest_sha256=candidate.corpus_manifest_sha256,
        baseline_capabilities=_capabilities(baseline_samples.values()),
        candidate_capabilities=_capabilities(candidate_samples.values()),
        splits=[
            _build_split_delta(
                split,
                baseline_runs[split],
                candidate_runs[split],
            )
            for split in _SPLITS
        ],
        acceptance_checks=checks,
        errors=errors,
        passed=not errors and all(checks.values()),
    )


def render_markdown(result: EvaluationDeltaResult) -> str:
    lines = [
        "# Static Evaluation Delta",
        "",
        f"- Baseline: `{result.baseline_ref}`",
        f"- Candidate: `{result.candidate_ref}`",
        f"- Result: {'PASS' if result.passed else 'FAIL'}",
        "- Baseline measurement capabilities: "
        + (", ".join(result.baseline_capabilities) or "legacy/unavailable"),
        "- Candidate measurement capabilities: "
        + (", ".join(result.candidate_capabilities) or "none"),
        "",
        "## Acceptance",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    lines.extend(
        f"| `{key}` | {'pass' if passed else 'fail'} |"
        for key, passed in result.acceptance_checks.items()
    )
    lines.extend(
        [
            "",
            "## Sample changes",
            "",
            "| Sample | Split | Gate before | Gate after | Added rules | Removed rules |",
            "|---|---|---|---|---|---|",
        ]
    )
    all_delta = next(item for item in result.splits if item.split == "all")
    for sample in all_delta.sample_deltas:
        lines.append(
            f"| `{sample.sample_id}` | {sample.split} | "
            f"{sample.baseline_observed_gate.value} | "
            f"{sample.candidate_observed_gate.value} | "
            f"{', '.join(sample.added_rule_ids) or '-'} | "
            f"{', '.join(sample.removed_rule_ids) or '-'} |"
        )
    if result.errors:
        lines.extend(["", "## Errors", "", *[f"- `{item}`" for item in result.errors]])
    return "\n".join(lines) + "\n"


def validate_paths(
    *,
    baseline_dir: Path,
    candidate_dir: Path,
    output_json: Path,
    output_markdown: Path,
    results_root: Path,
) -> None:
    root = results_root.resolve()
    for label, path in (
        ("baseline", baseline_dir),
        ("candidate", candidate_dir),
        ("JSON output", output_json),
        ("Markdown output", output_markdown),
    ):
        if not path.resolve().is_relative_to(root):
            raise ValueError(f"{label} path must stay within {root}")
    if output_json.suffix != ".json" or output_markdown.suffix != ".md":
        raise ValueError("delta outputs must use .json and .md suffixes")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="static-eval-delta")
    parser.add_argument("--baseline-dir", required=True)
    parser.add_argument("--candidate-dir", required=True)
    parser.add_argument("--baseline-ref", default="7b8b4b2")
    parser.add_argument("--candidate-ref", default="SAP-6-candidate")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    args = parser.parse_args(argv)
    baseline_dir = Path(args.baseline_dir)
    candidate_dir = Path(args.candidate_dir)
    output_json = Path(args.output_json)
    output_markdown = Path(args.output_markdown)
    validate_paths(
        baseline_dir=baseline_dir,
        candidate_dir=candidate_dir,
        output_json=output_json,
        output_markdown=output_markdown,
        results_root=Path("output/static-evaluation"),
    )
    result = build_delta(
        baseline_dir=baseline_dir,
        candidate_dir=candidate_dir,
        baseline_ref=args.baseline_ref,
        candidate_ref=args.candidate_ref,
    )
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_bytes(_canonical_json(result.model_dump(mode="json")))
    output_markdown.write_text(render_markdown(result), encoding="utf-8")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_delta", "main", "render_markdown", "validate_paths"]
