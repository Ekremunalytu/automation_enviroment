"""Shared helpers for in-house static rules (ES-3a, ADR 0016).

Mirrors ``packages.analysis_engine.rules._common``: small evidence/parse helpers
shared across the s1/s2/s3 rule modules. Snippets quoted from the untrusted
manifest/source are routed through ``redact_secrets`` (the dynamic
``ContentSample`` pattern) before they reach the report JSON / UI / logs
(AGENTS rule 11) and clamped to the ``StaticEvidenceRef.snippet`` length bound.
"""

from __future__ import annotations

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
        ".map",
        ".yml",
        ".yaml",
        ".xml",
        ".sh",
        ".env",
    }
)
# Per-file read cap for the content scanners (parity with the context's ES-4
# adversarial-input bounds): a real source file fits well under this; a larger
# file is scanned only up to the cap so the rules cannot be driven into an
# unbounded read inside the hardened container.
_MAX_TEXT_BYTES = 1024 * 1024

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


def evidence_type_for(
    context: StaticAnalysisContext, relative_path: str
) -> StaticEvidenceType:
    """``manifest`` for the parsed package.json, ``source_file`` otherwise."""
    if relative_path == context.manifest_relative_path:
        return "manifest"
    return "source_file"


__all__ = [
    "TEXT_SUFFIXES",
    "evidence_type_for",
    "file_evidence",
    "is_text_document",
    "iter_text_documents",
    "line_at",
    "line_number_at",
    "manifest_evidence",
    "manifest_string",
    "read_text_head",
    "safe_snippet",
]
