"""Shared helpers for in-house static rules (ES-3a, ADR 0016).

Mirrors ``packages.analysis_engine.rules._common``: small evidence/parse helpers
shared across the s1/s2/s3 rule modules. Snippets quoted from the untrusted
manifest/source are routed through ``redact_secrets`` (the dynamic
``ContentSample`` pattern) before they reach the report JSON / UI / logs
(AGENTS rule 11) and clamped to the ``StaticEvidenceRef.snippet`` length bound.
"""

from __future__ import annotations

from typing import Any

from packages.analysis_contracts.evidence import redact_secrets
from packages.analysis_contracts.static_detection import StaticEvidenceRef
from packages.analysis_contracts.static_detection.finding import StaticEvidenceType
from static_runtime.context import StaticAnalysisContext

# Mirror of StaticEvidenceRef.snippet's max_length=400 contract bound.
_SNIPPET_MAX = 400


def safe_snippet(value: str) -> str:
    """Redact secrets from a quoted snippet and clamp to the contract bound."""
    return redact_secrets(value)[:_SNIPPET_MAX]


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
) -> StaticEvidenceRef:
    """Build a file evidence ref; ``relative_path`` is validated by the contract."""
    return StaticEvidenceRef(
        type=evidence_type,
        relative_path=relative_path,
        snippet=safe_snippet(snippet) if snippet else None,
        tool="inhouse",
    )


__all__ = ["file_evidence", "manifest_evidence", "manifest_string", "safe_snippet"]
