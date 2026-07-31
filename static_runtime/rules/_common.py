"""Shared helpers for in-house static rules (ES-3a, ADR 0016).

Mirrors ``packages.analysis_engine.rules._common``: small evidence/parse helpers
shared across the s1/s2/s3 rule modules. Snippets quoted from the untrusted
manifest/source are routed through ``redact_secrets`` (the dynamic
``ContentSample`` pattern) before they reach the report JSON / UI / logs
(AGENTS rule 11) and clamped to the ``StaticEvidenceRef.snippet`` length bound.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from packages.analysis_contracts.evidence import (
    redact_multiline_secrets,
    redact_secrets,
)
from packages.analysis_contracts.static_detection import StaticEvidenceRef
from packages.analysis_contracts.static_detection.finding import StaticEvidenceType
from static_runtime.context import StaticAnalysisContext

# Text/source suffixes the content-scanning rules (s4-s7) inspect. A superset of
# the s3 file-tree set: domain / secret / obfuscation indicators hide in config
# and markup too, not only executable JS.
TEXT_SUFFIXES: frozenset[str] = frozenset(
    {
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".cjs",
        ".mjs",
        ".json",
        ".jsonc",
        ".md",
        ".txt",
        ".html",
        ".htm",
        ".css",
        # Stylesheet + CSS-preprocessor sources. ``.less``/``.scss``/``.sass``
        # are added so the content scanners (and the stylesheet-borne s19 family)
        # actually see them: the nextsecurity / vsix-zoo corpus ships its entire
        # CSS/LESS TTP set as ``.less`` files, which were previously skipped by
        # ``is_text_document`` and so never scanned for remote endpoints (s4/s5),
        # secrets (s7), webhooks (s8), crypto addresses (s9), or stylesheet
        # inline-JS / exfil (s19). See
        # ``documents/detection-design/nextsecurity-stylesheet-spec.md``.
        ".less",
        ".scss",
        ".sass",
        ".map",
        ".yml",
        ".yaml",
        ".xml",
        ".sh",
        ".env",
    }
)
# Per-file read cap for the content scanners (parity with the context's ES-4
# adversarial-input bounds). Modern VS Code extensions commonly ship multi-MiB
# webpack/esbuild entrypoint bundles (the local production set reaches 20.6
# MiB), so the old 1 MiB cap produced a blind spot on otherwise normal
# artifacts. Thirty-two MiB covers that production shape while preserving a hard
# per-file bound inside the 1 GiB, networkless analyzer container.
_MAX_TEXT_BYTES = 32 * 1024 * 1024
MAX_TEXT_BYTES = _MAX_TEXT_BYTES

# Mirror of StaticEvidenceRef.snippet's max_length=400 contract bound.
_SNIPPET_MAX = 400
# Clamp the raw input to this before redacting (see ``safe_snippet``). The 2x
# window keeps a secret straddling the final 400-char boundary catchable while
# bounding the redaction regexes' input.
_SNIPPET_INPUT_MAX = 2 * _SNIPPET_MAX


def safe_snippet(value: str) -> str:
    """Redact secrets from a quoted snippet and clamp to the contract bound.

    The raw input is clamped *before* redaction (not after), so an adversarial
    multi-MB snippet — e.g. a Semgrep match spanning a huge minified line —
    cannot drive the redaction regexes over an unbounded string (ReDoS). The
    bounded multiline pre-pass collapses PEM blocks (the only cross-line secret
    class) before the single-line passes run; then we clamp to the contract bound.
    """
    clamped = redact_multiline_secrets(value[:_SNIPPET_INPUT_MAX])
    return redact_secrets(clamped)[:_SNIPPET_MAX]


def manifest_string(manifest: dict[str, Any], key: str) -> str:
    """Return ``manifest[key]`` as a stripped string, '' for non-string/missing."""
    value = manifest.get(key)
    return value.strip() if isinstance(value, str) else ""


def manifest_evidence(
    context: StaticAnalysisContext,
    snippet: str,
    *,
    rule_match_id: str | None = None,
) -> StaticEvidenceRef:
    """Build a ``manifest`` evidence ref pointing at the parsed package.json."""
    return StaticEvidenceRef(
        type="manifest",
        relative_path=context.manifest_relative_path or "package.json",
        snippet=safe_snippet(snippet),
        tool="inhouse",
        rule_match_id=rule_match_id,
    )


def file_evidence(
    relative_path: str,
    evidence_type: StaticEvidenceType,
    snippet: str | None = None,
    *,
    tool: str = "inhouse",
    line_number: int | None = None,
    rule_match_id: str | None = None,
) -> StaticEvidenceRef:
    """Build a file evidence ref; ``relative_path`` is validated by the contract.

    ``tool`` defaults to ``"inhouse"`` so the s1/s2/s3 rule call sites are
    unchanged; the Semgrep mapper passes ``tool="semgrep"`` with a ``line_number``
    and ``rule_match_id`` to reuse this single redact+clamp evidence builder.
    """
    return StaticEvidenceRef(
        type=evidence_type,
        relative_path=relative_path,
        line_number=line_number,
        snippet=safe_snippet(snippet) if snippet else None,
        tool=tool,
        rule_match_id=rule_match_id,
    )


def is_text_document(relative_path: str) -> bool:
    """True when ``relative_path``'s suffix is one the content scanners inspect."""
    return Path(relative_path).suffix.lower() in TEXT_SUFFIXES


def read_text_head(path: Path, *, max_bytes: int = _MAX_TEXT_BYTES) -> str:
    """Read up to ``max_bytes`` of ``path`` as utf-8 (undecodable bytes dropped).

    Returns '' on any OSError so a single unreadable file degrades to "no text"
    rather than raising out of a rule pass.
    """
    try:
        with path.open("rb") as handle:
            raw = handle.read(max_bytes)
    except OSError:
        return ""
    return raw.decode("utf-8", "ignore")


def iter_text_documents(context: StaticAnalysisContext) -> Iterator[tuple[str, str]]:
    """Yield ``(relative_path, text)`` for each text/source file (bounded read).

    The manifest (package.json) is itself a text document, so the content
    scanners (s4 domains, s5 endpoints, s6 obfuscation, s7 secrets) see it
    without special-casing. Symlinks are already filtered by ``iter_files``.
    """
    for relative_path, absolute_path in context.iter_files():
        if not is_text_document(relative_path):
            continue
        text = read_text_head(absolute_path)
        if text:
            yield relative_path, text


def line_number_at(text: str, index: int) -> int:
    """1-based line number of character offset ``index`` within ``text``."""
    return text.count("\n", 0, max(index, 0)) + 1


def line_at(text: str, line_number: int) -> str:
    """Return the (stripped) content of 1-based ``line_number``, '' if out of range."""
    if line_number < 1:
        return ""
    lines = text.splitlines()
    if line_number > len(lines):
        return ""
    return lines[line_number - 1].strip()


def snippet_at(text: str, index: int, *, radius: int = 180) -> str:
    """Return a bounded snippet centred on ``index``.

    ``line_at`` is useful for ordinary source, but a minified bundle can place
    several MiB on one line. Returning that line and clamping its first 400
    characters points at unrelated code. This helper keeps the actual match in
    view before the normal evidence redaction/clamp is applied.
    """

    if not text:
        return ""
    bounded_index = min(max(index, 0), len(text))
    line_start = text.rfind("\n", 0, bounded_index) + 1
    line_end = text.find("\n", bounded_index)
    if line_end < 0:
        line_end = len(text)
    if line_end - line_start <= (radius * 2):
        return text[line_start:line_end].strip()
    start = max(line_start, bounded_index - radius)
    end = min(line_end, bounded_index + radius)
    prefix = "..." if start > line_start else ""
    suffix = "..." if end < line_end else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


def find_local_pattern_cluster(
    text: str,
    patterns: tuple[re.Pattern[str], ...],
    *,
    max_span: int,
) -> tuple[re.Match[str], ...] | None:
    """Find one match per pattern inside a bounded lexical region.

    Large bundled JavaScript files contain many unrelated libraries. File-wide
    co-occurrence therefore is not evidence that several APIs form one attack
    chain. The smallest covering window is used so callers can require lexical
    locality without adding a parser dependency to the hardened image.
    """

    if not patterns or max_span < 0:
        return None
    matches_by_pattern: list[list[re.Match[str]]] = []
    for pattern in patterns:
        matches = list(pattern.finditer(text))
        if not matches:
            # Most production bundles do not contain the first, most-specific
            # conjunct. Stop there instead of scanning the same multi-MiB file
            # once for every remaining pattern.
            return None
        matches_by_pattern.append(matches)

    events = sorted(
        (match.start(), pattern_index)
        for pattern_index, matches in enumerate(matches_by_pattern)
        for match in matches
    )
    counts = [0] * len(patterns)
    covered = 0
    left = 0
    best: tuple[int, int, int] | None = None
    for right_start, right_pattern in events:
        if counts[right_pattern] == 0:
            covered += 1
        counts[right_pattern] += 1
        while covered == len(patterns):
            left_start, left_pattern = events[left]
            candidate = (right_start - left_start, left_start, right_start)
            if best is None or candidate < best:
                best = candidate
            counts[left_pattern] -= 1
            if counts[left_pattern] == 0:
                covered -= 1
            left += 1

    if best is None or best[0] > max_span:
        return None
    _, window_start, window_end = best
    return tuple(
        min(
            (match for match in matches if window_start <= match.start() <= window_end),
            key=lambda match: match.start(),
        )
        for matches in matches_by_pattern
    )


def evidence_type_for(
    context: StaticAnalysisContext, relative_path: str
) -> StaticEvidenceType:
    """``manifest`` for the parsed package.json, ``source_file`` otherwise."""
    if relative_path == context.manifest_relative_path:
        return "manifest"
    return "source_file"


__all__ = [
    "MAX_TEXT_BYTES",
    "TEXT_SUFFIXES",
    "evidence_type_for",
    "file_evidence",
    "find_local_pattern_cluster",
    "is_text_document",
    "iter_text_documents",
    "line_at",
    "line_number_at",
    "manifest_evidence",
    "manifest_string",
    "read_text_head",
    "safe_snippet",
    "snippet_at",
]
