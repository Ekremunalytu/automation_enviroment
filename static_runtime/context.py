"""Static analysis input context (ES-3a, ADR 0016).

Parses the decompressed VSIX tree into the read-only surface the in-house rules
evaluate against. Lives inside the hardened ``automation_static_analyzer`` image,
so imports are confined to the standard library — the manifest is parsed with
``json`` directly rather than reusing
``workflows.extension_catalog.manifest_reader`` (which imports ``appcore`` and
would both break the ``packages``/``static_runtime`` boundary and drag api
config into the minimal image).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# VS Code packages the manifest at the extraction root for installed-extension
# layouts and under ``extension/`` for raw .vsix archives. Probe both so the
# rules work regardless of how ES-3b stages the tree.
_MANIFEST_CANDIDATES = ("package.json", "extension/package.json")

# Adversarial-input bounds (ES-4): a real manifest fits well under the byte cap
# and a real extension well under the file-count cap. Larger inputs are padding
# and are bounded here so an oversized "package.json" or a file-count bomb cannot
# drive an unbounded read / unbounded memory inside the hardened container.
_MAX_MANIFEST_BYTES = 1024 * 1024
_MAX_FILES = 50_000


@dataclass(slots=True)
class StaticAnalysisContext:
    """Read-only view of a decompressed extension tree for the static rules."""

    vsix_dir: Path
    manifest: dict[str, Any]
    # Path of the parsed manifest relative to ``vsix_dir`` (for evidence refs);
    # None when no parseable package.json was found.
    manifest_relative_path: str | None

    @classmethod
    def from_vsix_dir(cls, vsix_dir: str | Path) -> StaticAnalysisContext:
        """Build a context by locating + parsing the extension manifest.

        A missing, unreadable, or non-object manifest yields an empty dict (and
        ``manifest_relative_path`` still records where it was found, if any) so
        rules can decide whether to evaluate without raising.
        """
        root = Path(vsix_dir)
        manifest: dict[str, Any] = {}
        manifest_relative_path: str | None = None
        for candidate in _MANIFEST_CANDIDATES:
            path = root / candidate
            if not path.is_file():
                continue
            manifest_relative_path = candidate
            try:
                with path.open("rb") as handle:
                    raw = handle.read(_MAX_MANIFEST_BYTES)
                parsed = json.loads(raw.decode("utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                parsed = None
            if isinstance(parsed, dict):
                manifest = parsed
            break
        return cls(
            vsix_dir=root,
            manifest=manifest,
            manifest_relative_path=manifest_relative_path,
        )

    def iter_files(self) -> Iterator[tuple[str, Path]]:
        """Yield ``(relative_posix_path, absolute_path)`` for each regular file.

        Symlinks are skipped: the tree is extension-controlled and untrusted, so
        a symlink must never let a rule read (and quote into evidence) a file
        outside the extraction root. At most ``_MAX_FILES`` regular files are
        collected (then sorted for deterministic evidence order): the cap bounds
        memory against a file-count bomb without materialising the whole tree the
        way ``sorted(rglob(...))`` would.
        """
        if not self.vsix_dir.is_dir():
            return
        collected: list[Path] = []
        for path in self.vsix_dir.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            collected.append(path)
            if len(collected) >= _MAX_FILES:
                break
        for path in sorted(collected):
            yield path.relative_to(self.vsix_dir).as_posix(), path


__all__ = ["StaticAnalysisContext"]
