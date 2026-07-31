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
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

from packages.analysis_contracts.static_detection import (
    StaticCoverageReason,
    StaticManifestStatus,
    StaticScanCoverage,
)

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
_MAX_PATH_DETAILS = 20
_ENTRYPOINT_SUFFIXES = (".js", ".cjs", ".mjs", ".json", ".node")


def _normalized_entrypoint(value: object) -> str | None:
    """Return one safe manifest entrypoint without masking traversal."""

    if not isinstance(value, str):
        return None
    normalized = value.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if (
        not normalized
        or normalized.startswith("/")
        or ".." in normalized.split("/")
        or any(ord(char) < 32 for char in normalized)
    ):
        return None
    return normalized


def _resolve_entrypoint(
    declared: str,
    *,
    manifest_relative_path: str | None,
    available: set[str],
) -> str:
    """Resolve Node-style extensionless manifest entrypoints deterministically."""

    manifest_parent = (
        PurePosixPath(manifest_relative_path).parent
        if manifest_relative_path is not None
        else PurePosixPath()
    )
    rooted = (manifest_parent / PurePosixPath(declared)).as_posix()
    candidates = [rooted]
    if not PurePosixPath(rooted).suffix:
        candidates.extend(f"{rooted}{suffix}" for suffix in _ENTRYPOINT_SUFFIXES)
        candidates.extend(f"{rooted}/index{suffix}" for suffix in _ENTRYPOINT_SUFFIXES)
    return next(
        (candidate for candidate in candidates if candidate in available),
        rooted,
    )


@dataclass(slots=True)
class StaticAnalysisContext:
    """Read-only view of a decompressed extension tree for the static rules."""

    vsix_dir: Path
    manifest: dict[str, Any]
    # Path of the parsed manifest relative to ``vsix_dir`` (for evidence refs);
    # None when no parseable package.json was found.
    manifest_relative_path: str | None
    manifest_status: StaticManifestStatus = "missing"
    _files: tuple[tuple[str, Path, int], ...] = field(default_factory=tuple, repr=False)
    _files_loaded: bool = field(default=False, repr=False)
    file_cap_reached: bool = False
    _file_cap_paths: tuple[str, ...] = field(default_factory=tuple, repr=False)

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
        manifest_status: StaticManifestStatus = "missing"
        for candidate in _MANIFEST_CANDIDATES:
            path = root / candidate
            if not path.is_file():
                continue
            manifest_relative_path = candidate
            try:
                if path.stat().st_size > _MAX_MANIFEST_BYTES:
                    manifest_status = "too_large"
                    break
                with path.open("rb") as handle:
                    raw = handle.read(_MAX_MANIFEST_BYTES + 1)
                if len(raw) > _MAX_MANIFEST_BYTES:
                    manifest_status = "too_large"
                    break
                parsed = json.loads(raw.decode("utf-8"))
            except OSError:
                manifest_status = "unreadable"
                parsed = None
            except (UnicodeDecodeError, json.JSONDecodeError):
                manifest_status = "malformed"
                parsed = None
            if isinstance(parsed, dict):
                manifest = parsed
                manifest_status = "parsed"
            elif parsed is not None:
                manifest_status = "non_object"
            break
        return cls(
            vsix_dir=root,
            manifest=manifest,
            manifest_relative_path=manifest_relative_path,
            manifest_status=manifest_status,
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
        self._load_files()
        for relative_path, path, _ in self._files:
            yield relative_path, path

    def build_coverage(
        self, *, text_suffixes: frozenset[str], max_text_bytes: int
    ) -> StaticScanCoverage:
        """Return one deterministic aggregate coverage snapshot for this tree."""

        self._load_files()
        eligible = [
            item
            for item in self._files
            if Path(item[0]).suffix.lower() in text_suffixes
        ]
        bytes_considered = sum(size for _, _, size in eligible)
        truncated = sum(1 for _, _, size in eligible if size > max_text_bytes)
        bytes_read = 0
        parsed_paths: set[str] = set()
        skipped_path_details: dict[str, list[str]] = {}
        for relative_path, path, _ in eligible:
            try:
                with path.open("rb") as handle:
                    raw = handle.read(max_text_bytes)
            except OSError:
                skipped_path_details.setdefault("parser_error", []).append(
                    relative_path
                )
                continue
            bytes_read += len(raw)
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                skipped_path_details.setdefault("undecodable", []).append(relative_path)
                continue
            parsed_paths.add(relative_path)
        for relative_path, _, size in eligible:
            if size > max_text_bytes:
                skipped_path_details.setdefault("text_truncated", []).append(
                    relative_path
                )
        unsupported: dict[str, int] = {}
        for relative_path, _, _ in self._files:
            suffix = Path(relative_path).suffix.lower() or "<none>"
            if suffix in text_suffixes:
                continue
            unsupported[suffix] = unsupported.get(suffix, 0) + 1
            skipped_path_details.setdefault("unsupported_suffix", []).append(
                relative_path
            )

        declared_entrypoints: list[str] = []
        invalid_entrypoint_count = 0
        for field_name in ("main", "browser"):
            raw_entrypoint = self.manifest.get(field_name)
            normalized = _normalized_entrypoint(raw_entrypoint)
            if normalized is not None:
                declared_entrypoints.append(normalized)
            elif isinstance(raw_entrypoint, str) and raw_entrypoint:
                invalid_entrypoint_count += 1
        available = {relative_path for relative_path, _, _ in self._files}
        entrypoints = [
            _resolve_entrypoint(
                declared,
                manifest_relative_path=self.manifest_relative_path,
                available=available,
            )
            for declared in declared_entrypoints
        ]
        parsed_entrypoints = sorted(
            path for path in entrypoints if path in parsed_paths
        )

        skipped: dict[str, int] = {}
        reasons: list[StaticCoverageReason] = []
        if self.file_cap_reached:
            skipped["file_cap"] = 1
            reasons.append("file_cap")
            skipped_path_details["file_cap"] = list(self._file_cap_paths)
        if truncated:
            skipped["text_truncated"] = truncated
            reasons.append("text_truncated")
        undecodable = len(skipped_path_details.get("undecodable", []))
        if undecodable:
            skipped["undecodable"] = undecodable
            reasons.append("undecodable")
        parser_errors = len(skipped_path_details.get("parser_error", []))
        parser_errors += invalid_entrypoint_count
        if parser_errors:
            skipped["parser_error"] = parser_errors
            reasons.append("parser_error")
        if unsupported:
            skipped["unsupported_suffix"] = sum(unsupported.values())
        manifest_reason_map: dict[StaticManifestStatus, StaticCoverageReason] = {
            "missing": "manifest_missing",
            "malformed": "manifest_malformed",
            "too_large": "manifest_too_large",
            "unreadable": "parser_error",
            "non_object": "manifest_malformed",
        }
        manifest_reason = manifest_reason_map.get(self.manifest_status)
        if manifest_reason:
            reasons.append(manifest_reason)
            if self.manifest_relative_path:
                skipped_path_details.setdefault(manifest_reason, []).append(
                    self.manifest_relative_path
                )
        missing_entrypoints = sorted(set(entrypoints) - available)
        if missing_entrypoints:
            reasons.append("critical_entrypoint_missing")
            skipped_path_details["critical_entrypoint_missing"] = missing_entrypoints
        unparsed_entrypoints = sorted(
            set(entrypoints) - set(parsed_entrypoints) - set(missing_entrypoints)
        )
        if unparsed_entrypoints:
            reasons.append("critical_entrypoint_unparsed")
            skipped_path_details["critical_entrypoint_unparsed"] = unparsed_entrypoints

        return StaticScanCoverage(
            files_discovered=len(self._files) + int(self.file_cap_reached),
            files_selected=len(self._files),
            files_eligible=len(eligible),
            files_scanned=len(self._files),
            files_parsed=len(parsed_paths),
            files_skipped_by_reason=skipped,
            skipped_paths_by_reason={
                reason: sorted(set(paths))[:_MAX_PATH_DETAILS]
                for reason, paths in skipped_path_details.items()
                if paths
            },
            bytes_considered=bytes_considered,
            bytes_read=bytes_read,
            manifest_status=self.manifest_status,
            critical_entrypoints=sorted(set(entrypoints)),
            critical_entrypoints_parsed=parsed_entrypoints,
            file_cap_reached=self.file_cap_reached,
            unsupported_formats=unsupported,
            coverage_reasons=reasons,
        )

    def _load_files(self) -> None:
        if self._files_loaded:
            return
        self._files_loaded = True
        if not self.vsix_dir.is_dir():
            return
        collected: list[tuple[str, Path, int]] = []
        for path in self.vsix_dir.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            collected.append((path.relative_to(self.vsix_dir).as_posix(), path, size))
            if len(collected) > _MAX_FILES:
                self.file_cap_reached = True
                excluded_path, _, _ = collected.pop()
                self._file_cap_paths = (excluded_path,)
                break
        self._files = tuple(sorted(collected, key=lambda item: item[0]))


__all__ = ["StaticAnalysisContext"]
