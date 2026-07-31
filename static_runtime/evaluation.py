"""Deterministic, container-only SMF corpus evaluator."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from packages.analysis_contracts.static_detection import StaticScanCoverage
from packages.analysis_contracts.static_detection.policy import evaluate_static_gate
from packages.analysis_contracts.static_evaluation import (
    CorpusManifest,
    CorpusSample,
    EvaluationResult,
    FindingFingerprint,
    SampleEvaluation,
)
from packages.analysis_contracts.static_evaluation.metrics import build_metric
from packages.analysis_contracts.static_evaluation.models import RuleMetric
from static_runtime.rule_inventory import (
    build_rule_bundle_inventory,
    rule_inventory_payload,
)
from static_runtime.static_runner import run_static_detection_engine

_CORPUS_MOUNT = Path("/evaluation-corpus")
_RESULTS_MOUNT = Path("/results/static-evaluation")


def _positive_timeout_budget(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("timeout budget must be greater than zero")
    return parsed


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def hash_tree(root: Path) -> str:
    """Hash relative paths and exact bytes without following symlinks."""

    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def validate_runtime_paths(
    *,
    manifest_path: Path,
    corpus_root: Path,
    output_json: Path,
    output_markdown: Path,
    corpus_mount: Path = _CORPUS_MOUNT,
    results_mount: Path = _RESULTS_MOUNT,
) -> None:
    """Reject CLI paths that escape the read-only corpus or writable result roots."""

    resolved_corpus_mount = corpus_mount.resolve()
    resolved_results_mount = results_mount.resolve()
    for label, path in (
        ("manifest", manifest_path),
        ("corpus", corpus_root),
    ):
        if not path.resolve().is_relative_to(resolved_corpus_mount):
            raise ValueError(f"{label} path must stay within {resolved_corpus_mount}")
    for label, path, suffix in (
        ("JSON output", output_json, ".json"),
        ("Markdown output", output_markdown, ".md"),
    ):
        if (
            not path.resolve().is_relative_to(resolved_results_mount)
            or path.suffix != suffix
        ):
            raise ValueError(
                f"{label} path must stay within {resolved_results_mount} "
                f"and use {suffix}"
            )


def _fingerprints(report: object) -> list[FindingFingerprint]:
    findings = getattr(report, "findings", [])
    built: list[FindingFingerprint] = []
    for finding in findings:
        evidence_items = finding.evidence or [None]
        for evidence in evidence_items:
            relative_path = (
                evidence.relative_path if evidence is not None else "<report>"
            )
            evidence_type = evidence.type if evidence is not None else "none"
            snippet = evidence.snippet if evidence is not None else ""
            match_shape = hashlib.sha256((snippet or "").encode("utf-8")).hexdigest()[
                :16
            ]
            built.append(
                FindingFingerprint(
                    rule_id=finding.rule_id,
                    rule_version=finding.rule_version,
                    normalized_relative_path=relative_path,
                    evidence_type=evidence_type,
                    normalized_match_shape=match_shape,
                )
            )
    return sorted(
        built,
        key=lambda item: (
            item.rule_id,
            item.rule_version,
            item.normalized_relative_path,
            item.evidence_type,
            item.normalized_match_shape,
        ),
    )


def _evaluate_sample(
    sample: CorpusSample,
    *,
    corpus_root: Path,
    rules_version: str,
    timeout_budget_s: int,
    semgrep_enabled: bool,
) -> SampleEvaluation:
    sample_root = (corpus_root / sample.relative_path).resolve()
    if not sample_root.is_relative_to(corpus_root.resolve()):
        raise ValueError(f"sample escapes corpus root: {sample.sample_id}")
    if not sample_root.is_dir():
        raise ValueError(f"sample directory does not exist: {sample.relative_path}")
    actual_sha256 = hash_tree(sample_root)
    if actual_sha256 != sample.sha256:
        raise ValueError(
            f"sample hash mismatch for {sample.sample_id}: "
            f"expected {sample.sha256}, got {actual_sha256}"
        )

    started = time.monotonic()
    report = run_static_detection_engine(
        vsix_dir=str(sample_root),
        rules_version=rules_version,
        timeout_budget_s=timeout_budget_s,
        semgrep_enabled=semgrep_enabled,
        vsix_sha256=actual_sha256,
    )
    outcome = evaluate_static_gate(report)
    fired = sorted({finding.rule_id for finding in report.findings})
    missing = sorted(set(sample.must_fire) - set(fired))
    unexpected = sorted(set(sample.must_not_fire) & set(fired))
    reason_mismatch = sorted(
        set(sample.expected_inconclusive_reasons) - set(outcome.inconclusive_reasons)
    )
    coverage_mismatch = sorted(
        set(sample.expected_coverage) - set(report.coverage.coverage_reasons)
    )
    errors = [
        *(f"missing:{rule_id}" for rule_id in missing),
        *(f"unexpected:{rule_id}" for rule_id in unexpected),
        *(f"missing_coverage_reason:{reason}" for reason in reason_mismatch),
        *(f"missing_coverage:{reason}" for reason in coverage_mismatch),
    ]
    if outcome.decision is not sample.expected_gate:
        errors.append(
            f"gate:{outcome.decision.value}!=expected:{sample.expected_gate.value}"
        )
    return SampleEvaluation(
        sample_id=sample.sample_id,
        split=sample.split,
        label=sample.label,
        observed_gate=outcome.decision,
        expected_gate=sample.expected_gate,
        fired_rule_ids=fired,
        missing_rule_ids=missing,
        unexpected_rule_ids=unexpected,
        finding_fingerprints=_fingerprints(report),
        coverage=report.coverage,
        tool_duration_ms={
            record.tool: record.duration_ms for record in report.tool_executions
        },
        duration_ms=int((time.monotonic() - started) * 1000),
        passed=not errors,
        errors=errors,
    )


def _metric_rows(
    samples: list[CorpusSample],
    results: list[SampleEvaluation],
    *,
    known_rule_ids: set[str],
) -> tuple[RuleMetric, list[RuleMetric], list[RuleMetric]]:
    by_sample = {result.sample_id: result for result in results}
    rule_metrics: list[RuleMetric] = []
    for rule_id in sorted(known_rule_ids):
        tp = fp = fn = tn = 0
        for sample in samples:
            if rule_id not in sample.must_fire and rule_id not in sample.must_not_fire:
                continue
            fired = rule_id in by_sample[sample.sample_id].fired_rule_ids
            expected = rule_id in sample.must_fire
            tp += int(expected and fired)
            fp += int(not expected and fired)
            fn += int(expected and not fired)
            tn += int(not expected and not fired)
        rule_metrics.append(
            build_metric(
                key=rule_id,
                true_positive=tp,
                false_positive=fp,
                false_negative=fn,
                true_negative=tn,
            )
        )

    family_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    sample_counts = [0, 0, 0, 0]
    for sample in samples:
        if sample.label == "coverage_control":
            continue
        result = by_sample[sample.sample_id]
        expected_positive = sample.label in {"malicious_behavior", "vulnerable"}
        observed_positive = bool(result.fired_rule_ids)
        sample_counts[0] += int(expected_positive and observed_positive)
        sample_counts[1] += int(not expected_positive and observed_positive)
        sample_counts[2] += int(expected_positive and not observed_positive)
        sample_counts[3] += int(not expected_positive and not observed_positive)
        for family in sample.families:
            counts = family_counts[family]
            counts[0] += int(expected_positive and observed_positive)
            counts[1] += int(not expected_positive and observed_positive)
            counts[2] += int(expected_positive and not observed_positive)
            counts[3] += int(not expected_positive and not observed_positive)
    family_metrics = [
        build_metric(
            key=family,
            true_positive=counts[0],
            false_positive=counts[1],
            false_negative=counts[2],
            true_negative=counts[3],
        )
        for family, counts in sorted(family_counts.items())
    ]
    sample_metric = build_metric(
        key="samples",
        true_positive=sample_counts[0],
        false_positive=sample_counts[1],
        false_negative=sample_counts[2],
        true_negative=sample_counts[3],
    )
    return sample_metric, rule_metrics, family_metrics


def _coverage_summary(results: list[SampleEvaluation]) -> StaticScanCoverage:
    reasons = sorted(
        {reason for result in results for reason in result.coverage.coverage_reasons}
    )
    skipped: dict[str, int] = defaultdict(int)
    skipped_paths: dict[str, list[str]] = defaultdict(list)
    unsupported: dict[str, int] = defaultdict(int)
    for result in results:
        for reason, count in result.coverage.files_skipped_by_reason.items():
            skipped[reason] += count
        for reason, paths in result.coverage.skipped_paths_by_reason.items():
            skipped_paths[reason].extend(f"{result.sample_id}/{path}" for path in paths)
        for suffix, count in result.coverage.unsupported_formats.items():
            unsupported[suffix] += count
    return StaticScanCoverage(
        files_discovered=sum(item.coverage.files_discovered for item in results),
        files_selected=sum(item.coverage.files_selected for item in results),
        files_eligible=sum(item.coverage.files_eligible for item in results),
        files_scanned=sum(item.coverage.files_scanned for item in results),
        files_parsed=sum(item.coverage.files_parsed for item in results),
        files_skipped_by_reason=dict(skipped),
        skipped_paths_by_reason={
            reason: sorted(set(paths))[:20] for reason, paths in skipped_paths.items()
        },
        bytes_considered=sum(item.coverage.bytes_considered for item in results),
        bytes_read=sum(item.coverage.bytes_read for item in results),
        manifest_status="parsed",
        file_cap_reached=any(item.coverage.file_cap_reached for item in results),
        finding_cap_reached=any(item.coverage.finding_cap_reached for item in results),
        unsupported_formats=dict(unsupported),
        coverage_reasons=reasons,
    )


def _percentile(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def evaluate_corpus(
    *,
    manifest_path: Path,
    corpus_root: Path,
    split: str,
    timeout_budget_s: int = 30,
    semgrep_enabled: bool = True,
    evaluation_id: str | None = None,
) -> EvaluationResult:
    manifest_bytes = manifest_path.read_bytes()
    manifest = CorpusManifest.model_validate_json(manifest_bytes)
    inventory = build_rule_bundle_inventory()
    known_rule_ids = {entry.rule_id for entry in inventory.inhouse_rules}
    known_rule_ids.update(entry.rule_id for entry in inventory.semgrep_rules)
    manifest.validate_rule_ids(known_rule_ids)
    selected = [
        sample for sample in manifest.samples if split == "all" or sample.split == split
    ]
    if not selected:
        raise ValueError(f"corpus split contains no samples: {split}")

    started_at = datetime.now(UTC)
    sample_results = [
        _evaluate_sample(
            sample,
            corpus_root=corpus_root,
            rules_version=inventory.rules_bundle_fingerprint[:16],
            timeout_budget_s=timeout_budget_s,
            semgrep_enabled=semgrep_enabled,
        )
        for sample in selected
    ]
    known_rule_ids = {entry.rule_id for entry in inventory.inhouse_rules}
    known_rule_ids.update(entry.rule_id for entry in inventory.semgrep_rules)
    sample_metric, rule_metrics, family_metrics = _metric_rows(
        selected,
        sample_results,
        known_rule_ids=known_rule_ids,
    )
    durations = [result.duration_ms for result in sample_results]
    tool_durations: dict[str, list[int]] = defaultdict(list)
    for result in sample_results:
        for tool, duration_ms in result.tool_duration_ms.items():
            tool_durations[tool].append(duration_ms)
    errors = [
        f"{result.sample_id}:{error}"
        for result in sample_results
        for error in result.errors
    ]
    return EvaluationResult(
        evaluation_id=evaluation_id or f"static-eval-{int(started_at.timestamp())}",
        rules_bundle_fingerprint=inventory.rules_bundle_fingerprint,
        corpus_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        started_at=started_at,
        completed_at=datetime.now(UTC),
        sample_results=sample_results,
        sample_metric=sample_metric,
        rule_metrics=rule_metrics,
        family_metrics=family_metrics,
        coverage_summary=_coverage_summary(sample_results),
        runtime_summary={
            "sample_count": len(durations),
            "p50_ms": _percentile(durations, 0.50),
            "p95_ms": _percentile(durations, 0.95),
            "total_ms": sum(durations),
            **{
                f"{tool}_{percentile}_ms": _percentile(values, fraction)
                for tool, values in sorted(tool_durations.items())
                for percentile, fraction in (("p50", 0.50), ("p95", 0.95))
            },
        },
        determinism_summary={
            "normalization_schema": "1",
            "volatile_fields_excluded": True,
        },
        errors=errors,
    )


def render_markdown(result: EvaluationResult) -> str:
    lines = [
        "# Static Evaluation Baseline",
        "",
        f"- Rules bundle: `{result.rules_bundle_fingerprint}`",
        f"- Corpus manifest: `{result.corpus_manifest_sha256}`",
        f"- Samples: {len(result.sample_results)}",
        f"- Passing: {sum(item.passed for item in result.sample_results)}",
        f"- Errors: {len(result.errors)}",
        "",
        "| Sample | Split | Expected | Observed | Result |",
        "|---|---|---|---|---|",
    ]
    for sample in sorted(result.sample_results, key=lambda item: item.sample_id):
        lines.append(
            f"| `{sample.sample_id}` | {sample.split} | "
            f"{sample.expected_gate.value} | {sample.observed_gate.value} | "
            f"{'pass' if sample.passed else 'fail'} |"
        )
    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"- Files discovered: {result.coverage_summary.files_discovered}",
            f"- Files scanned: {result.coverage_summary.files_scanned}",
            "- Reasons: "
            + (
                ", ".join(result.coverage_summary.coverage_reasons)
                if result.coverage_summary.coverage_reasons
                else "none"
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="static-evaluation")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--corpus-root", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    parser.add_argument("--split", choices=("tuning", "holdout", "all"), required=True)
    parser.add_argument(
        "--timeout-budget-s",
        type=_positive_timeout_budget,
        default=30,
    )
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    corpus_root = Path(args.corpus_root)
    output_json = Path(args.output_json)
    output_markdown = Path(args.output_markdown)
    validate_runtime_paths(
        manifest_path=manifest_path,
        corpus_root=corpus_root,
        output_json=output_json,
        output_markdown=output_markdown,
    )
    result = evaluate_corpus(
        manifest_path=manifest_path,
        corpus_root=corpus_root,
        split=args.split,
        timeout_budget_s=args.timeout_budget_s,
    )
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_bytes(_canonical_json(result.model_dump(mode="json")) + b"\n")
    output_markdown.write_text(render_markdown(result), encoding="utf-8")
    inventory = build_rule_bundle_inventory()
    (output_json.parent / "rule-inventory.json").write_text(
        json.dumps(rule_inventory_payload(inventory), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "evaluate_corpus",
    "hash_tree",
    "render_markdown",
    "validate_runtime_paths",
]
