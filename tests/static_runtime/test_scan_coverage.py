"""Every enforced in-house scan bound produces visible coverage accounting."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from static_runtime import context, semgrep_runner
from static_runtime.context import StaticAnalysisContext
from static_runtime.rules._common import MAX_TEXT_BYTES, TEXT_SUFFIXES


def _coverage(root: Path):
    return StaticAnalysisContext.from_vsix_dir(root).build_coverage(
        text_suffixes=TEXT_SUFFIXES,
        max_text_bytes=MAX_TEXT_BYTES,
    )


def test_malformed_and_missing_manifests_are_visible(tmp_path: Path) -> None:
    missing = _coverage(tmp_path)
    assert missing.manifest_status == "missing"
    assert "manifest_missing" in missing.coverage_reasons

    (tmp_path / "package.json").write_text("{bad", encoding="utf-8")
    malformed = _coverage(tmp_path)
    assert malformed.manifest_status == "malformed"
    assert "manifest_malformed" in malformed.coverage_reasons


def test_file_and_text_caps_are_visible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(context, "_MAX_FILES", 2)
    (tmp_path / "package.json").write_text(
        json.dumps({"publisher": "trusted", "main": "large.js"}),
        encoding="utf-8",
    )
    (tmp_path / "large.js").write_text("x" * (MAX_TEXT_BYTES + 1), encoding="utf-8")
    (tmp_path / "extra.js").write_text("x", encoding="utf-8")
    coverage = _coverage(tmp_path)
    assert coverage.file_cap_reached is True
    assert "file_cap" in coverage.coverage_reasons

    monkeypatch.setattr(context, "_MAX_FILES", 10)
    complete_coverage = _coverage(tmp_path)
    assert complete_coverage.bytes_read <= complete_coverage.bytes_considered
    assert complete_coverage.skipped_paths_by_reason["text_truncated"] == ["large.js"]


def test_undecodable_and_missing_entrypoint_are_visible(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"publisher": "trusted", "main": "missing.js"}),
        encoding="utf-8",
    )
    (tmp_path / "invalid.js").write_bytes(b"\xff\xfe")

    coverage = _coverage(tmp_path)

    assert "undecodable" in coverage.coverage_reasons
    assert coverage.files_skipped_by_reason["undecodable"] == 1
    assert coverage.skipped_paths_by_reason["undecodable"] == ["invalid.js"]
    assert "critical_entrypoint_missing" in coverage.coverage_reasons
    assert coverage.skipped_paths_by_reason["critical_entrypoint_missing"] == [
        "missing.js"
    ]


def test_extensionless_entrypoints_resolve_to_scanned_node_files(
    tmp_path: Path,
) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "publisher": "trusted",
                "main": "./dist/extension",
                "browser": "./dist/web",
            }
        ),
        encoding="utf-8",
    )
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "extension.js").write_text("activate()", encoding="utf-8")
    (dist / "web.cjs").write_text("activateWeb()", encoding="utf-8")

    coverage = _coverage(tmp_path)

    assert "critical_entrypoint_missing" not in coverage.coverage_reasons
    assert "critical_entrypoint_unparsed" not in coverage.coverage_reasons
    assert coverage.critical_entrypoints == ["dist/extension.js", "dist/web.cjs"]
    assert coverage.critical_entrypoints_parsed == [
        "dist/extension.js",
        "dist/web.cjs",
    ]


def test_raw_vsix_entrypoint_resolves_relative_to_manifest(tmp_path: Path) -> None:
    extension = tmp_path / "extension"
    dist = extension / "dist"
    dist.mkdir(parents=True)
    (extension / "package.json").write_text(
        json.dumps({"publisher": "trusted", "main": "./dist/extension"}),
        encoding="utf-8",
    )
    (dist / "extension.js").write_text("activate()", encoding="utf-8")

    coverage = _coverage(tmp_path)

    assert coverage.critical_entrypoints == ["extension/dist/extension.js"]
    assert coverage.critical_entrypoints_parsed == ["extension/dist/extension.js"]
    assert "critical_entrypoint_missing" not in coverage.coverage_reasons


def test_adversarial_entrypoint_is_rejected_without_unsafe_path_detail(
    tmp_path: Path,
) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"publisher": "trusted", "main": "../escape.js"}),
        encoding="utf-8",
    )
    (tmp_path / "extension.js").write_text("activate()", encoding="utf-8")

    coverage = _coverage(tmp_path)

    assert coverage.critical_entrypoints == []
    assert coverage.critical_entrypoints_parsed == []
    assert coverage.files_skipped_by_reason["parser_error"] == 1
    assert "parser_error" in coverage.coverage_reasons
    assert "parser_error" not in coverage.skipped_paths_by_reason


def test_semgrep_target_byte_cap_is_visible(tmp_path: Path) -> None:
    target = tmp_path / "oversized.ts"
    target.write_text("x" * (semgrep_runner._MAX_TARGET_BYTES + 1), encoding="utf-8")

    coverage = semgrep_runner._build_semgrep_coverage(
        tmp_path,
        raw_result_count=0,
        error_count=0,
    )

    assert "target_too_large" in coverage.coverage_reasons
    assert coverage.files_skipped_by_reason["target_too_large"] == 1
    assert coverage.skipped_paths_by_reason["target_too_large"] == ["oversized.ts"]


def test_common_five_mebibyte_bundle_is_fully_covered(tmp_path: Path) -> None:
    bundle_size = 5 * 1024 * 1024
    assert MAX_TEXT_BYTES == 32 * 1024 * 1024
    assert bundle_size <= MAX_TEXT_BYTES
    assert semgrep_runner._MAX_TARGET_BYTES == MAX_TEXT_BYTES
    (tmp_path / "extension.cjs").write_bytes(b"x" * bundle_size)

    inhouse = _coverage(tmp_path)
    semgrep = semgrep_runner._build_semgrep_coverage(
        tmp_path,
        raw_result_count=0,
        error_count=0,
    )

    assert "text_truncated" not in inhouse.coverage_reasons
    assert inhouse.bytes_read == inhouse.bytes_considered
    assert "target_too_large" not in semgrep.coverage_reasons
    assert semgrep.files_scanned == 1
    assert semgrep.bytes_read == bundle_size


def test_semgrep_inventory_exclusions_are_visible_but_not_partial(
    tmp_path: Path,
) -> None:
    vendor = tmp_path / "node_modules" / "vendor"
    vendor.mkdir(parents=True)
    (vendor / "index.js").write_text("eval(payload)", encoding="utf-8")
    (tmp_path / "extension.js").write_text("activate()", encoding="utf-8")

    coverage = semgrep_runner._build_semgrep_coverage(
        tmp_path,
        raw_result_count=0,
        error_count=0,
    )

    assert coverage.files_skipped_by_reason["excluded_inventory_only"] == 1
    assert coverage.skipped_paths_by_reason["excluded_inventory_only"] == [
        "node_modules/vendor/index.js"
    ]
    assert "excluded_inventory_only" not in coverage.coverage_reasons
    assert coverage.files_scanned == 1
