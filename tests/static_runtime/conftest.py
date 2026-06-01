"""Shared fixtures for the in-house static-rule tests (ES-3a, ADR 0016)."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import pytest

from static_runtime.context import StaticAnalysisContext


@pytest.fixture
def make_context(
    tmp_path: Path,
) -> Callable[..., StaticAnalysisContext]:
    """Factory: write a manifest + files into a temp tree, return its context.

    ``manifest`` (when given) is JSON-dumped to ``package.json``; ``files`` maps
    relative paths to ``str`` (text) or ``bytes`` content.
    """

    def _make(
        manifest: Mapping[str, Any] | None = None,
        files: Mapping[str, str | bytes] | None = None,
    ) -> StaticAnalysisContext:
        if manifest is not None:
            (tmp_path / "package.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
        for relative_path, content in (files or {}).items():
            target = tmp_path / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                target.write_bytes(content)
            else:
                target.write_text(content, encoding="utf-8")
        return StaticAnalysisContext.from_vsix_dir(tmp_path)

    return _make
