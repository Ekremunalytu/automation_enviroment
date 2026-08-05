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


def test_index_nested_package_browser_entry_and_loader_edges(tmp_path: Path) -> None:
    source = tmp_path / "src"
    (source / "feature").mkdir(parents=True)
    (source / "main.js").write_text(
        "import './feature'; require.resolve('outer');",
        encoding="utf-8",
    )
    (source / "feature/index.ts").write_text("export {};", encoding="utf-8")

    outer = tmp_path / "node_modules/outer"
    inner = outer / "node_modules/inner"
    (inner / "lib").mkdir(parents=True)
    (outer / "package.json").write_text(
        json.dumps({"main": "server.js", "browser": "browser.js"}),
        encoding="utf-8",
    )
    (outer / "server.js").write_text(
        "throw new Error('wrong entry');", encoding="utf-8"
    )
    (outer / "browser.js").write_text(
        "require('inner');\n//# sourceMappingURL=browser.js.map",
        encoding="utf-8",
    )
    (outer / "browser.js.map").write_text("{}", encoding="utf-8")
    (inner / "package.json").write_text(
        json.dumps({"main": "lib/index"}), encoding="utf-8"
    )
    (inner / "lib/index.js").write_text("module.exports = {};", encoding="utf-8")

    result = build_reachability_graph(
        _context(tmp_path, {"main": "src/main.js"}), max_file_bytes=1024 * 1024
    )

    assert "src/feature/index.ts" in result.provenance
    assert "node_modules/outer/server.js" not in result.provenance
    assert (
        result.provenance["node_modules/outer/browser.js"].edge_kind
        == "require_resolve"
    )
    assert (
        result.provenance["node_modules/outer/node_modules/inner/lib/index.js"].parent
        == "node_modules/outer/browser.js"
    )
    assert (
        result.provenance["node_modules/outer/browser.js.map"].edge_kind == "source_map"
    )


def test_package_browser_object_is_not_inferred_over_string_main(
    tmp_path: Path,
) -> None:
    (tmp_path / "main.js").write_text("require('pkg');", encoding="utf-8")
    package = tmp_path / "node_modules/pkg"
    package.mkdir(parents=True)
    (package / "package.json").write_text(
        json.dumps({"browser": {"./server.js": "./browser.js"}, "main": "server.js"}),
        encoding="utf-8",
    )
    (package / "server.js").write_text("module.exports = {};", encoding="utf-8")
    (package / "browser.js").write_text("module.exports = {};", encoding="utf-8")

    result = build_reachability_graph(
        _context(tmp_path, {"main": "main.js"}), max_file_bytes=1024 * 1024
    )

    assert "node_modules/pkg/server.js" in result.provenance
    assert "node_modules/pkg/browser.js" not in result.provenance


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


def test_traversal_absolute_and_missing_modules_are_diagnostic_but_builtins_are_not(
    tmp_path: Path,
) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src/main.js").write_text(
        "\n".join(
            [
                "require('../../escape');",
                "require('/absolute/path');",
                "require('missing-package');",
                "require('node:fs');",
                "require('vscode');",
            ]
        ),
        encoding="utf-8",
    )

    result = build_reachability_graph(
        _context(tmp_path, {"main": "src/main.js"}), max_file_bytes=1024 * 1024
    )

    assert result.summary.unresolved_count == 3
    assert [item.expression for item in result.summary.unresolved_references] == [
        "'../../escape'",
        "'/absolute/path'",
        "'missing-package'",
    ]
    assert set(result.provenance) == {"src/main.js"}


def test_unresolved_reference_details_are_capped_without_losing_total(
    tmp_path: Path,
) -> None:
    (tmp_path / "main.js").write_text(
        "\n".join(f"require(target{index});" for index in range(25)),
        encoding="utf-8",
    )

    result = build_reachability_graph(
        _context(tmp_path, {"main": "main.js"}), max_file_bytes=1024 * 1024
    )

    assert result.summary.unresolved_count == 25
    assert len(result.summary.unresolved_references) == 20
    assert result.summary.unresolved_references[0].expression == "target0"
    assert result.summary.unresolved_references[-1].expression == "target19"
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


def test_per_file_bound_is_an_explicit_parse_coverage_loss(tmp_path: Path) -> None:
    (tmp_path / "main.js").write_text("import './next';", encoding="utf-8")
    (tmp_path / "next.js").write_text("export {};", encoding="utf-8")

    result = build_reachability_graph(
        _context(tmp_path, {"main": "main.js"}), max_file_bytes=4
    )

    assert result.summary.nodes_reached == 1
    assert result.summary.edges_resolved == 0
    assert "reachability_parse_error" in result.coverage_reasons
