"""Shared helpers for in-house static rules (ES-3a, ADR 0016).

Mirrors ``packages.analysis_engine.rules._common``: small evidence/parse helpers
shared across the s1/s2/s3 rule modules. Snippets quoted from the untrusted
manifest/source are routed through ``redact_secrets`` (the dynamic
``ContentSample`` pattern) before they reach the report JSON / UI / logs
(AGENTS rule 11) and clamped to the ``StaticEvidenceRef.snippet`` length bound.
"""

from __future__ import annotations

from typing import Any

from packages.analysis_contracts.evidence import (
    redact_multiline_secrets,
    redact_secrets,
)
from packages.analysis_contracts.static_detection import StaticEvidenceRef
from packages.analysis_contracts.static_detection.finding import StaticEvidenceType
from static_runtime.context import StaticAnalysisContext

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


__all__ = ["file_evidence", "manifest_evidence", "manifest_string", "safe_snippet"]
