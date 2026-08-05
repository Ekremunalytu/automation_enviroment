"""SAP-5 bounded import/loader reachability tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from static_runtime import reachability
from static_runtime.context import StaticAnalysisContext
from static_runtime.reachability import build_reachability_graph


def _context(root: Path, manifest: dict[str, object]) -> StaticAnalysisContext:
    (root / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
    return StaticAnalysisContext.from_vsix_dir(root)


def test_literal_and_constant_folded_edges_reach_local_and_dependency_targets(
    tmp_path: Path,
) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "main.js").write_text(
        """
        import './literal';
        const base = './';
        require(base + 'loader');
        import('pkg');
        """,
        encoding="utf-8",
    )
    (source / "literal.js").write_text("export const ok = true;", encoding="utf-8")
    (source / "loader.js").write_text("module.exports = {};", encoding="utf-8")
    package = tmp_path / "node_modules/pkg"
    (package / "dist").mkdir(parents=True)
    (package / "package.json").write_text(
        json.dumps({"main": "dist/index"}), encoding="utf-8"
    )
    (package / "dist/index.js").write_text("module.exports = {};", encoding="utf-8")

    result = build_reachability_graph(
        _context(tmp_path, {"main": "src/main"}), max_file_bytes=1024 * 1024
    )

    assert result.summary.roots == ["src/main.js"]
    assert set(result.provenance) == {
        "src/main.js",
        "src/literal.js",
        "src/loader.js",
        "node_modules/pkg/dist/index.js",
    }
    assert result.provenance["src/literal.js"].confidence == "literal"
    assert result.provenance["src/loader.js"].confidence == "heuristic"
    assert result.provenance["node_modules/pkg/dist/index.js"].parent == "src/main.js"


def test_path_join_native_loader_and_template_are_bounded_heuristics(
    tmp_path: Path,
) -> None:
    (tmp_path / "main.js").write_text(
        """
        const nativeName = 'addon.node';
        require(path.join(__dirname, nativeName));
        const stem = './feature';
        import(`${stem}.js`);
        """,
        encoding="utf-8",
    )
    (tmp_path / "addon.node").write_bytes(b"\x7fELF")
    (tmp_path / "feature.js").write_text("export {};", encoding="utf-8")

    result = build_reachability_graph(
        _context(tmp_path, {"main": "main.js"}), max_file_bytes=1024 * 1024
    )

    native = result.provenance["addon.node"]
    assert native.edge_kind == "native_loader"
    assert native.confidence == "heuristic"
    assert result.provenance["feature.js"].confidence == "heuristic"


def test_cycles_and_multiple_roots_choose_a_deterministic_parent(
    tmp_path: Path,
) -> None:
    (tmp_path / "a.js").write_text("import './shared';", encoding="utf-8")
    (tmp_path / "b.js").write_text("require('./shared');", encoding="utf-8")
    (tmp_path / "shared.js").write_text("import './a';", encoding="utf-8")

    result = build_reachability_graph(
        _context(tmp_path, {"main": "a.js", "browser": "b.js"}),
        max_file_bytes=1024 * 1024,
    )

    assert result.provenance["shared.js"].parent == "a.js"
    assert result.summary.nodes_reached == 3
    assert result.summary.edges_resolved == 3


def test_computed_unresolved_edge_is_visible_but_not_inconclusive(
    tmp_path: Path,
) -> None:
    (tmp_path / "main.js").write_text(
        "const target = process.env.TARGET; require(target); require('node:fs');",
        encoding="utf-8",
    )

    result = build_reachability_graph(
        _context(tmp_path, {"main": "main.js"}), max_file_bytes=1024 * 1024
    )

    assert result.summary.unresolved_count == 1
    assert result.summary.unresolved_references[0].expression == "target"
    assert result.coverage_reasons == ()


@pytest.mark.parametrize(
    ("attribute", "value", "expected"),
    [
        ("MAX_REACHABILITY_NODES", 1, "reachability_node_cap"),
        ("MAX_REACHABILITY_EDGES", 0, "reachability_edge_cap"),
        ("MAX_REACHABILITY_BYTES", 1, "reachability_byte_cap"),
        ("MAX_REACHABILITY_DEPTH", 0, "reachability_depth_cap"),
    ],
)
def test_graph_limits_are_explicit_coverage_reasons(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    attribute: str,
    value: int,
    expected: str,
) -> None:
    (tmp_path / "main.js").write_text("import './next';", encoding="utf-8")
    (tmp_path / "next.js").write_text("export {};", encoding="utf-8")
    monkeypatch.setattr(reachability, attribute, value)

    result = build_reachability_graph(
        _context(tmp_path, {"main": "main.js"}), max_file_bytes=1024 * 1024
    )

    assert expected in result.coverage_reasons


def test_read_and_parse_losses_are_inconclusive(tmp_path: Path) -> None:
    path = tmp_path / "main.js"
    path.write_text("import './next';", encoding="utf-8")
    (tmp_path / "next.js").write_text("export {};", encoding="utf-8")
    context = _context(tmp_path, {"main": "main.js"})
    list(context.iter_file_records())
    path.unlink()
    read_result = build_reachability_graph(context, max_file_bytes=1024 * 1024)
    assert "reachability_read_error" in read_result.coverage_reasons

    path.write_bytes(b"\xff\xfe")
    parse_context = StaticAnalysisContext.from_vsix_dir(tmp_path)
    parse_result = build_reachability_graph(parse_context, max_file_bytes=1024 * 1024)
    assert "reachability_parse_error" in parse_result.coverage_reasons
