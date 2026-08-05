"""S3 static rules: file-tree heuristics (ES-3a, ADR 0016).

Two production rules over the decompressed file tree:

* ``extrace.s3.embedded_native_binary`` — native modules (.node/.so/.dylib/...)
  or content-sniffed binary blobs disguised under another name.
* ``extrace.s3.unusual_file_signature`` — text/source files that are
  unexpectedly large (a common shape for packed/obfuscated payloads).

Each rule emits at most one finding carrying up to ``_MAX_EVIDENCE`` evidence
refs; when more files match, the count is reported in the description rather
than silently truncated.
"""

from __future__ import annotations

from pathlib import Path

from packages.analysis_contracts.detection.enums import (
    AdversaryClass,
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.static_detection import (
    StaticDetectionFinding,
    StaticEvidenceRef,
)
from static_runtime.artifacts import classify_artifact
from static_runtime.context import StaticAnalysisContext
from static_runtime.rules._common import file_evidence
from static_runtime.rules.registry import register

_TEXT_SUFFIXES = frozenset(
    {
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".json",
        ".md",
        ".txt",
        ".html",
        ".css",
        # Stylesheet preprocessor sources are known-text; listing them skips the
        # NUL-byte content sniff for the nextsecurity/vsix-zoo ``.less`` corpus.
        ".less",
        ".scss",
        ".sass",
        ".map",
    }
)
_LARGE_TEXT_THRESHOLD = 2 * 1024 * 1024  # 2 MB
_MAX_EVIDENCE = 25


def _suffix(relative_path: str) -> str:
    return Path(relative_path).suffix.lower()


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


class EmbeddedNativeBinaryRule:
    rule_id = "extrace.s3.embedded_native_binary"
    rule_version = "1.2.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    # Presence is inventory, not malice. S13 owns suspicious native-loader
    # conjunctions; an ordinary signed/verified helper must not warn by itself.
    severity = Severity.INFO
    description = (
        "Extension ships native binaries or content-sniffed binary blobs, which "
        "can execute outside the JS sandbox and resist static review."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        evidence: list[StaticEvidenceRef] = []
        total = 0
        for relative_path, absolute_path in context.iter_files():
            classification = classify_artifact(relative_path, absolute_path)
            if not classification.is_native_executable:
                continue
            total += 1
            if len(evidence) < _MAX_EVIDENCE:
                evidence.append(
                    file_evidence(
                        relative_path,
                        "binary_file",
                        snippet=f"{classification.format} native artifact, "
                        f"{classification.suffix or 'no-suffix'}, "
                        f"{_file_size(absolute_path)} bytes",
                    )
                )
        if total == 0:
            return []
        shown = min(total, _MAX_EVIDENCE)
        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1105", "extrace.ext.native_binary"],
                severity=self.severity,
                confidence=Confidence.HIGH,
                title="Extension ships embedded native or binary files",
                description=(
                    f"{total} native executable/module artifact(s) found in the "
                    f"extension tree (showing {shown}). Native modules execute "
                    "outside the JS sandbox and are opaque to source review."
                ),
                evidence=evidence,
                mitigation_hint=(
                    "Verify each binary's provenance; embedded native code is a "
                    "common vehicle for sandbox-escaping payloads."
                ),
            )
        ]


class UnusualFileSignatureRule:
    rule_id = "extrace.s3.unusual_file_signature"
    rule_version = "1.1.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    # Modern webpack/esbuild bundles commonly exceed 2 MiB. Keep the visibility
    # but do not turn bundle size alone into a security warning.
    severity = Severity.INFO
    description = (
        "Extension contains text/source files that are unexpectedly large, a "
        "common shape for packed or obfuscated payloads."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        evidence: list[StaticEvidenceRef] = []
        total = 0
        for relative_path, absolute_path in context.iter_files():
            if _suffix(relative_path) not in _TEXT_SUFFIXES:
                continue
            size = _file_size(absolute_path)
            if size <= _LARGE_TEXT_THRESHOLD:
                continue
            total += 1
            if len(evidence) < _MAX_EVIDENCE:
                evidence.append(
                    file_evidence(
                        relative_path,
                        "source_file",
                        snippet=f"{size} bytes (> {_LARGE_TEXT_THRESHOLD})",
                    )
                )
        if total == 0:
            return []
        shown = min(total, _MAX_EVIDENCE)
        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1027", "extrace.ext.unusual_file"],
                severity=self.severity,
                confidence=Confidence.LOW,
                title="Extension contains unusually large text/source files",
                description=(
                    f"{total} text/source file(s) exceed {_LARGE_TEXT_THRESHOLD} "
                    f"bytes (showing {shown}). Oversized source is a common shape "
                    "for packed or obfuscated payloads."
                ),
                evidence=evidence,
                mitigation_hint=(
                    "Inspect the oversized files; minified/packed bundles can "
                    "hide behaviour from static review."
                ),
            )
        ]


register(EmbeddedNativeBinaryRule())
register(UnusualFileSignatureRule())

__all__ = ["EmbeddedNativeBinaryRule", "UnusualFileSignatureRule"]
