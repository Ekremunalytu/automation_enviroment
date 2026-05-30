"""Tests for StaticAnalysisContext manifest parsing + file iteration (ES-3a)."""

from __future__ import annotations

import json
from pathlib import Path

from static_runtime.context import StaticAnalysisContext


def test_manifest_parsed_from_root(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"publisher": "acme", "name": "x"}), encoding="utf-8"
    )
    ctx = StaticAnalysisContext.from_vsix_dir(tmp_path)
    assert ctx.manifest_relative_path == "package.json"
    assert ctx.manifest["publisher"] == "acme"


def test_manifest_parsed_from_extension_subdir(tmp_path: Path) -> None:
    # Raw .vsix layout: the manifest lives under extension/.
    nested = tmp_path / "extension"
    nested.mkdir()
    (nested / "package.json").write_text(
        json.dumps({"publisher": "acme"}), encoding="utf-8"
    )
    ctx = StaticAnalysisContext.from_vsix_dir(tmp_path)
    assert ctx.manifest_relative_path == "extension/package.json"
    assert ctx.manifest["publisher"] == "acme"


def test_missing_manifest_yields_none_path(tmp_path: Path) -> None:
    (tmp_path / "extension.js").write_text("x", encoding="utf-8")
    ctx = StaticAnalysisContext.from_vsix_dir(tmp_path)
    assert ctx.manifest_relative_path is None
    assert ctx.manifest == {}


def test_malformed_manifest_records_path_but_empty_dict(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{not valid json", encoding="utf-8")
    ctx = StaticAnalysisContext.from_vsix_dir(tmp_path)
    # Path is recorded (it was found), but the unparseable body degrades to {}.
    assert ctx.manifest_relative_path == "package.json"
    assert ctx.manifest == {}


def test_non_object_manifest_degrades_to_empty_dict(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(json.dumps(["a", "b"]), encoding="utf-8")
    ctx = StaticAnalysisContext.from_vsix_dir(tmp_path)
    assert ctx.manifest == {}


def test_iter_files_yields_nested_posix_paths(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b.js").write_text("x", encoding="utf-8")
    (tmp_path / "top.txt").write_text("y", encoding="utf-8")
    ctx = StaticAnalysisContext.from_vsix_dir(tmp_path)
    rels = {rel for rel, _ in ctx.iter_files()}
    assert rels == {"a/b.js", "top.txt"}


def test_iter_files_skips_symlinks(tmp_path: Path) -> None:
    """A symlink (esp. one escaping the tree) must never be read as evidence."""
    outside = tmp_path / "secret.txt"
    outside.write_text("host secret", encoding="utf-8")
    scan = tmp_path / "scan"
    scan.mkdir()
    (scan / "ok.js").write_text("x", encoding="utf-8")
    (scan / "escape.txt").symlink_to(outside)

    ctx = StaticAnalysisContext.from_vsix_dir(scan)
    rels = {rel for rel, _ in ctx.iter_files()}
    assert rels == {"ok.js"}
    assert "escape.txt" not in rels


def test_iter_files_empty_for_missing_dir(tmp_path: Path) -> None:
    ctx = StaticAnalysisContext.from_vsix_dir(tmp_path / "does-not-exist")
    assert list(ctx.iter_files()) == []
