"""SAP-4 artifact inventory and bounded deep-target selection tests."""

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
    StaticDetectionFinding,
    StaticEvidenceRef,
)
from static_runtime import artifact_inventory
from static_runtime.artifact_inventory import build_artifact_inventory
from static_runtime.context import StaticAnalysisContext


def _finding(path: str) -> StaticDetectionFinding:
    return StaticDetectionFinding(
        rule_id="extrace.test.signal",
        rule_version="1.0.0",
        rule_lifecycle=RuleLifecycle.PRODUCTION,
        categories=["extrace.ext.dynamic_code_exec"],
        severity=Severity.MEDIUM,
        confidence=Confidence.MEDIUM,
        title="signal",
        description="signal",
        evidence=[
            StaticEvidenceRef(
                type="source_file",
                relative_path=path,
                tool="inhouse",
            )
        ],
    )


def test_inventory_classifies_and_selects_direct_and_evidenced_targets(
    tmp_path: Path,
) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"publisher": "trusted", "main": "dist/main"}),
        encoding="utf-8",
    )
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/main.js").write_text("activate()", encoding="utf-8")
    dependency = tmp_path / "node_modules/@scope/pkg/index.js"
    dependency.parent.mkdir(parents=True)
    dependency.write_text("eval(payload)", encoding="utf-8")
    ordinary = tmp_path / "node_modules/plain/index.js"
    ordinary.parent.mkdir(parents=True)
    ordinary.write_text("module.exports = {}", encoding="utf-8")
    minified = tmp_path / "dist/vendor.min.js"
    minified.write_text("function x(){}", encoding="utf-8")
    (tmp_path / "README.md").write_text("docs", encoding="utf-8")

    result = build_artifact_inventory(
        StaticAnalysisContext.from_vsix_dir(tmp_path),
        findings=[_finding("node_modules/@scope/pkg/index.js")],
        max_target_bytes=1024,
    )
    by_path = {entry.relative_path: entry for entry in result.entries}

    assert by_path["dist/main.js"].entrypoint_reachability == "direct"
    assert by_path["dist/main.js"].disposition == "deep_scan"
    assert by_path["node_modules/@scope/pkg/index.js"].dependency_owner == "@scope/pkg"
    assert by_path["node_modules/@scope/pkg/index.js"].disposition == "deep_scan"
    assert by_path["node_modules/plain/index.js"].disposition == "inventory_only"
    assert by_path["README.md"].disposition == "inventory_only"
    assert by_path["dist/vendor.min.js"].is_minified is True
    assert by_path["dist/vendor.min.js"].disposition == "inventory_only"
    assert {
        Path(path).relative_to(tmp_path).as_posix()
        for path in result.extra_deep_scan_targets
    } == {
        "node_modules/@scope/pkg/index.js",
    }


def test_direct_minified_entrypoint_is_selected_without_inhouse_evidence(
    tmp_path: Path,
) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"publisher": "trusted", "main": "dist/entry.min"}),
        encoding="utf-8",
    )
    entrypoint = tmp_path / "dist/entry.min.js"
    entrypoint.parent.mkdir()
    entrypoint.write_text("module.exports = {};", encoding="utf-8")

    result = build_artifact_inventory(
        StaticAnalysisContext.from_vsix_dir(tmp_path),
        findings=[],
        max_target_bytes=1024,
    )
    entry = next(
        item for item in result.entries if item.relative_path == "dist/entry.min.js"
    )

    assert entry.entrypoint_reachability == "direct"
    assert entry.disposition == "deep_scan"
    assert entry.disposition_reasons == ["direct_manifest_entrypoint"]
    assert [
        Path(path).relative_to(tmp_path).as_posix()
        for path in result.extra_deep_scan_targets
    ] == ["dist/entry.min.js"]


def test_dependency_format_mismatch_is_selected_for_deep_scan(tmp_path: Path) -> None:
    disguised = tmp_path / "node_modules/pkg/payload.js"
    disguised.parent.mkdir(parents=True)
    disguised.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 32)

    result = build_artifact_inventory(
        StaticAnalysisContext.from_vsix_dir(tmp_path),
        findings=[],
        max_target_bytes=1024,
    )
    entry = next(
        item for item in result.entries if item.relative_path.endswith("payload.js")
    )

    assert entry.extension_header_match is False
    assert entry.disposition == "deep_scan"
    assert entry.disposition_reasons == ["format_extension_mismatch"]
    assert len(result.extra_deep_scan_targets) == 1


def test_inventory_marks_unknown_reachability_oversize_and_read_error(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.js"
    source.write_bytes(b"0123456789")
    unreadable = tmp_path / "gone.js"
    unreadable.write_text("gone", encoding="utf-8")
    context = StaticAnalysisContext.from_vsix_dir(tmp_path)
    list(context.iter_file_records())
    unreadable.unlink()

    result = build_artifact_inventory(
        context,
        findings=[],
        max_target_bytes=4,
    )
    by_path = {entry.relative_path: entry for entry in result.entries}
    assert by_path["source.js"].disposition == "skipped"
    assert by_path["source.js"].disposition_reasons == ["target_too_large"]
    assert by_path["source.js"].entrypoint_reachability == "unknown"
    assert by_path["gone.js"].disposition == "skipped"
    assert by_path["gone.js"].disposition_reasons == ["read_error"]


def test_extra_target_cap_is_deterministic_and_visible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert artifact_inventory.MAX_EXTRA_DEEP_SCAN_TARGETS == 256
    monkeypatch.setattr(artifact_inventory, "MAX_EXTRA_DEEP_SCAN_TARGETS", 1)
    (tmp_path / "package.json").write_text(
        json.dumps({"publisher": "trusted", "main": "z.min.js"}),
        encoding="utf-8",
    )
    for name in ("a.min.js", "b.min.js", "z.min.js"):
        (tmp_path / name).write_text("activate()", encoding="utf-8")

    result = build_artifact_inventory(
        StaticAnalysisContext.from_vsix_dir(tmp_path),
        findings=[_finding("a.min.js"), _finding("b.min.js")],
        max_target_bytes=1024,
    )
    by_path = {entry.relative_path: entry for entry in result.entries}
    assert result.target_cap_reached is True
    assert [Path(path).name for path in result.extra_deep_scan_targets] == ["z.min.js"]
    assert by_path["a.min.js"].disposition == "skipped"
    assert by_path["b.min.js"].disposition == "skipped"
    assert "deep_scan_target_cap" in by_path["b.min.js"].disposition_reasons


def test_vendor_and_minified_sources_need_an_explicit_deep_scan_reason(
    tmp_path: Path,
) -> None:
    (tmp_path / "vendor").mkdir()
    vendor = tmp_path / "vendor/bundle.js"
    vendor.write_text("eval(payload)", encoding="utf-8")
    minified = tmp_path / "bundle.min.js"
    minified.write_text("eval(payload)", encoding="utf-8")

    without_evidence = build_artifact_inventory(
        StaticAnalysisContext.from_vsix_dir(tmp_path),
        findings=[],
        max_target_bytes=1024,
    )
    by_path = {entry.relative_path: entry for entry in without_evidence.entries}
    assert by_path["vendor/bundle.js"].disposition_reasons == ["vendor_inventory_only"]
    assert by_path["bundle.min.js"].disposition_reasons == ["minified_inventory_only"]
    assert without_evidence.extra_deep_scan_targets == ()

    with_evidence = build_artifact_inventory(
        StaticAnalysisContext.from_vsix_dir(tmp_path),
        findings=[_finding("vendor/bundle.js"), _finding("bundle.min.js")],
        max_target_bytes=1024,
    )
    assert {
        Path(path).relative_to(tmp_path).as_posix()
        for path in with_evidence.extra_deep_scan_targets
    } == {
        "bundle.min.js",
        "vendor/bundle.js",
    }


@pytest.mark.parametrize(
    ("manifest_text", "expected"),
    [
        (json.dumps({"publisher": "trusted"}), "none"),
        ("{malformed", "unknown"),
    ],
)
def test_inventory_distinguishes_missing_and_malformed_entrypoints(
    tmp_path: Path, manifest_text: str, expected: str
) -> None:
    (tmp_path / "package.json").write_text(manifest_text, encoding="utf-8")
    (tmp_path / "extension.js").write_text("activate()", encoding="utf-8")

    result = build_artifact_inventory(
        StaticAnalysisContext.from_vsix_dir(tmp_path),
        findings=[],
        max_target_bytes=1024,
    )
    by_path = {entry.relative_path: entry for entry in result.entries}
    assert by_path["extension.js"].entrypoint_reachability == expected


def test_transitively_reachable_dependency_is_selected_with_provenance(
    tmp_path: Path,
) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"publisher": "trusted", "main": "main.js"}),
        encoding="utf-8",
    )
    (tmp_path / "main.js").write_text("require('pkg');", encoding="utf-8")
    dependency = tmp_path / "node_modules/pkg"
    dependency.mkdir(parents=True)
    (dependency / "package.json").write_text(
        json.dumps({"main": "index.js"}), encoding="utf-8"
    )
    (dependency / "index.js").write_text("module.exports = {};", encoding="utf-8")

    result = build_artifact_inventory(
        StaticAnalysisContext.from_vsix_dir(tmp_path),
        findings=[],
        max_target_bytes=1024,
    )
    entry = next(
        item
        for item in result.entries
        if item.relative_path == "node_modules/pkg/index.js"
    )

    assert entry.entrypoint_reachability == "transitive"
    assert entry.reachability_parent == "main.js"
    assert entry.reachability_edge_kind == "require"
    assert entry.reachability_confidence == "literal"
    assert entry.disposition == "deep_scan"
    assert entry.disposition_reasons == ["transitive_entrypoint_reachable"]
    assert [
        Path(path).relative_to(tmp_path).as_posix()
        for path in result.extra_deep_scan_targets
    ] == ["node_modules/pkg/index.js"]
