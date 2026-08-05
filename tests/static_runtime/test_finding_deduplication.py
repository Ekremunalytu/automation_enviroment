"""SAP-5 exact vendor/source-map finding deduplication tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.analysis_contracts.detection.enums import (
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.static_detection import (
    StaticArtifactInventoryEntry,
    StaticDetectionFinding,
    StaticEvidenceRef,
)
from static_runtime.context import StaticAnalysisContext
from static_runtime.finding_deduplication import deduplicate_findings


def _finding(
    path: str,
    *,
    snippet: str = "eval(payload)",
    line: int = 1,
    rule_id: str = "extrace.test.echo",
    extra_evidence: list[StaticEvidenceRef] | None = None,
) -> StaticDetectionFinding:
    evidence = [
        StaticEvidenceRef(
            type="source_file",
            relative_path=path,
            line_number=line,
            snippet=snippet,
            tool="inhouse",
            rule_match_id="echo-1",
        )
    ]
    evidence.extend(extra_evidence or [])
    return StaticDetectionFinding(
        rule_id=rule_id,
        rule_version="1.0.0",
        rule_lifecycle=RuleLifecycle.PRODUCTION,
        categories=["extrace.ext.dynamic_code_exec"],
        severity=Severity.MEDIUM,
        confidence=Confidence.MEDIUM,
        title="Exact echo",
        description="Exact echo",
        evidence=evidence,
    )


def _entry(
    path: str,
    *,
    role: str = "first_party_runtime",
    vendor: bool = False,
    minified: bool = False,
    reachability: str = "none",
    confidence: str | None = None,
) -> StaticArtifactInventoryEntry:
    return StaticArtifactInventoryEntry(
        relative_path=path,
        role=role,
        format="text",
        size_bytes=16,
        is_vendor=vendor,
        is_minified=minified,
        entrypoint_reachability=reachability,
        reachability_parent="main.js" if reachability == "transitive" else None,
        reachability_edge_kind="require" if reachability == "transitive" else None,
        reachability_confidence=confidence,
        disposition="deep_scan",
        disposition_reasons=["first_party_runtime"],
    )


def _dedupe(
    tmp_path: Path,
    findings: list[StaticDetectionFinding],
    entries: list[StaticArtifactInventoryEntry],
    *,
    max_file_bytes: int = 1024 * 1024,
):
    return deduplicate_findings(
        StaticAnalysisContext.from_vsix_dir(tmp_path),
        findings=findings,
        artifact_inventory=tuple(entries),
        max_file_bytes=max_file_bytes,
    )


def test_exact_vendor_copy_is_suppressed_with_deterministic_provenance(
    tmp_path: Path,
) -> None:
    content = "eval(payload)\n"
    (tmp_path / "src").mkdir()
    (tmp_path / "vendor").mkdir()
    (tmp_path / "src/main.js").write_text(content, encoding="utf-8")
    (tmp_path / "vendor/main.js").write_text(content, encoding="utf-8")
    canonical = _finding("src/main.js")
    duplicate = _finding("vendor/main.js")

    result = _dedupe(
        tmp_path,
        [duplicate, canonical],
        [
            _entry("src/main.js", reachability="direct"),
            _entry("vendor/main.js", vendor=True),
        ],
    )

    assert [item.evidence[0].relative_path for item in result.findings] == [
        "src/main.js"
    ]
    assert len(result.records) == 1
    assert result.records[0].reason == "vendor_echo"
    assert result.records[0].canonical_path == "src/main.js"
    assert result.records[0].duplicate_path == "vendor/main.js"

    reversed_result = _dedupe(
        tmp_path,
        [canonical, duplicate],
        [
            _entry("src/main.js", reachability="direct", confidence="literal"),
            _entry("vendor/main.js", vendor=True),
        ],
    )
    assert reversed_result.records == result.records


def test_exact_minified_copy_is_suppressed(tmp_path: Path) -> None:
    content = "eval(payload)\n"
    (tmp_path / "src").mkdir()
    (tmp_path / "dist").mkdir()
    (tmp_path / "src/main.js").write_text(content, encoding="utf-8")
    (tmp_path / "dist/main.min.js").write_text(content, encoding="utf-8")

    result = _dedupe(
        tmp_path,
        [_finding("dist/main.min.js"), _finding("src/main.js")],
        [
            _entry("src/main.js", reachability="direct", confidence="literal"),
            _entry("dist/main.min.js", minified=True),
        ],
    )

    assert len(result.findings) == 1
    assert result.records[0].reason == "vendor_echo"


@pytest.mark.parametrize(
    (
        "first_reachability",
        "first_confidence",
        "second_reachability",
        "second_confidence",
    ),
    [
        ("direct", "literal", "transitive", "literal"),
        ("transitive", "literal", "transitive", "heuristic"),
        ("transitive", "heuristic", "none", None),
    ],
)
def test_canonical_reachability_priority_is_stable(
    tmp_path: Path,
    first_reachability: str,
    first_confidence: str | None,
    second_reachability: str,
    second_confidence: str | None,
) -> None:
    content = "eval(payload)\n"
    for directory in ("preferred", "secondary", "vendor"):
        (tmp_path / directory).mkdir()
        (tmp_path / directory / "main.js").write_text(content, encoding="utf-8")
    findings = [
        _finding("vendor/main.js"),
        _finding("secondary/main.js"),
        _finding("preferred/main.js"),
    ]
    entries = [
        _entry(
            "preferred/main.js",
            reachability=first_reachability,
            confidence=first_confidence,
        ),
        _entry(
            "secondary/main.js",
            reachability=second_reachability,
            confidence=second_confidence,
        ),
        _entry("vendor/main.js", vendor=True),
    ]

    result = _dedupe(tmp_path, findings, entries)

    assert result.records[0].canonical_path == "preferred/main.js"
    assert result.records[0].duplicate_path == "vendor/main.js"


def test_first_party_is_canonical_over_vendor_when_reachability_is_equal(
    tmp_path: Path,
) -> None:
    content = "eval(payload)\n"
    (tmp_path / "src").mkdir()
    (tmp_path / "vendor").mkdir()
    (tmp_path / "src/main.js").write_text(content, encoding="utf-8")
    (tmp_path / "vendor/main.js").write_text(content, encoding="utf-8")

    result = _dedupe(
        tmp_path,
        [_finding("vendor/main.js"), _finding("src/main.js")],
        [_entry("src/main.js"), _entry("vendor/main.js", vendor=True)],
    )

    assert result.records[0].canonical_path == "src/main.js"


def test_source_map_sources_content_echo_is_suppressed(tmp_path: Path) -> None:
    source = "eval(payload)\n"
    (tmp_path / "src").mkdir()
    (tmp_path / "dist").mkdir()
    (tmp_path / "src/main.js").write_text(source, encoding="utf-8")
    (tmp_path / "dist/main.js.map").write_text(
        json.dumps({"sources": ["../src/main.js"], "sourcesContent": [source]}),
        encoding="utf-8",
    )
    canonical = _finding("src/main.js")
    duplicate = _finding("dist/main.js.map", snippet="eval(payload)", line=1)

    result = _dedupe(
        tmp_path,
        [duplicate, canonical],
        [
            _entry("src/main.js", reachability="direct"),
            _entry("dist/main.js.map", role="source_map"),
        ],
    )

    assert len(result.findings) == 1
    assert result.records[0].reason == "source_map_echo"


def test_different_rule_snippet_or_line_preserves_unique_vendor_evidence(
    tmp_path: Path,
) -> None:
    content = "eval(payload)\nother()\n"
    (tmp_path / "src").mkdir()
    (tmp_path / "vendor").mkdir()
    (tmp_path / "src/main.js").write_text(content, encoding="utf-8")
    (tmp_path / "vendor/main.js").write_text(content, encoding="utf-8")
    entries = [
        _entry("src/main.js", reachability="direct"),
        _entry("vendor/main.js", vendor=True),
    ]

    result = _dedupe(
        tmp_path,
        [
            _finding("src/main.js"),
            _finding("vendor/main.js", rule_id="extrace.test.other"),
            _finding("vendor/main.js", snippet="other()", line=2),
        ],
        entries,
    )

    assert len(result.findings) == 3
    assert result.records == ()


def test_version_severity_and_confidence_changes_preserve_unique_evidence(
    tmp_path: Path,
) -> None:
    content = "eval(payload)\n"
    (tmp_path / "src").mkdir()
    (tmp_path / "vendor").mkdir()
    (tmp_path / "src/main.js").write_text(content, encoding="utf-8")
    (tmp_path / "vendor/main.js").write_text(content, encoding="utf-8")
    base = _finding("src/main.js")
    duplicate = _finding("vendor/main.js")

    variants = [
        duplicate.model_copy(update={"rule_version": "2.0.0"}),
        duplicate.model_copy(update={"severity": Severity.HIGH}),
        duplicate.model_copy(update={"confidence": Confidence.HIGH}),
    ]
    result = _dedupe(
        tmp_path,
        [base, *variants],
        [
            _entry("src/main.js", reachability="direct"),
            _entry("vendor/main.js", vendor=True),
        ],
    )

    assert len(result.findings) == 4
    assert result.records == ()


def test_partial_multi_evidence_match_is_never_suppressed(tmp_path: Path) -> None:
    for directory in ("src", "vendor"):
        (tmp_path / directory).mkdir()
        (tmp_path / directory / "main.js").write_text(
            "eval(payload)\n", encoding="utf-8"
        )
    (tmp_path / "src/unique.js").write_text("one()", encoding="utf-8")
    (tmp_path / "vendor/unique.js").write_text("two()", encoding="utf-8")
    canonical_extra = StaticEvidenceRef(
        type="source_file",
        relative_path="src/unique.js",
        line_number=1,
        snippet="one()",
        tool="inhouse",
    )
    duplicate_extra = canonical_extra.model_copy(
        update={"relative_path": "vendor/unique.js"}
    )

    result = _dedupe(
        tmp_path,
        [
            _finding("src/main.js", extra_evidence=[canonical_extra]),
            _finding("vendor/main.js", extra_evidence=[duplicate_extra]),
        ],
        [
            _entry("src/main.js", reachability="direct"),
            _entry("src/unique.js"),
            _entry("vendor/main.js", vendor=True),
            _entry("vendor/unique.js", vendor=True),
        ],
    )

    assert len(result.findings) == 2


def test_malformed_oversized_or_unique_source_map_is_preserved(tmp_path: Path) -> None:
    source = "eval(payload)\n"
    (tmp_path / "src").mkdir()
    (tmp_path / "dist").mkdir()
    (tmp_path / "src/main.js").write_text(source, encoding="utf-8")
    (tmp_path / "dist/bad.js.map").write_text("{bad", encoding="utf-8")
    (tmp_path / "dist/unique.js.map").write_text(
        json.dumps({"sourcesContent": ["different()"]}), encoding="utf-8"
    )
    entries = [
        _entry("src/main.js", reachability="direct"),
        _entry("dist/bad.js.map", role="source_map"),
        _entry("dist/unique.js.map", role="source_map"),
    ]

    malformed = _dedupe(
        tmp_path,
        [_finding("src/main.js"), _finding("dist/bad.js.map")],
        entries,
    )
    oversized = _dedupe(
        tmp_path,
        [_finding("src/main.js"), _finding("dist/unique.js.map")],
        entries,
        max_file_bytes=4,
    )
    unique = _dedupe(
        tmp_path,
        [_finding("src/main.js"), _finding("dist/unique.js.map")],
        entries,
    )

    assert len(malformed.findings) == 2
    assert len(oversized.findings) == 2
    assert len(unique.findings) == 2
