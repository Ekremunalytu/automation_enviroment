"""S13 static rule: bundled .node native loader with platform dispatch.

Native addons are dual-use, so the rule is deliberately conjunctive. A plain
``require("./addon.node")`` is a warning. The GlassWorm-strength shape is a
relative/bundled .node load plus platform dispatch plus host-context arguments
such as ``process.execPath`` or ``__dirname`` being passed into the native module.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

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
from static_runtime.context import StaticAnalysisContext
from static_runtime.rules._common import (
    evidence_type_for,
    file_evidence,
    iter_text_documents,
    line_at,
    line_number_at,
    manifest_string,
)
from static_runtime.rules.registry import register

_MAX_EVIDENCE = 25

_REQUIRE_NODE_RE = re.compile(
    r"\brequire\s*\(\s*(['\"`])(?P<path>[^'\"`]*\.node)\1\s*\)",
    re.IGNORECASE,
)
_DECLARED_REQUIRE_NODE_RE = re.compile(
    r"\b(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*=\s*"
    r"require\s*\(\s*(['\"`])(?P<path>[^'\"`]*\.node)\2\s*\)",
    re.IGNORECASE,
)
_ASSIGNED_REQUIRE_NODE_RE = re.compile(
    r"\b(?P<name>[A-Za-z_$][\w$]*)\s*=\s*"
    r"require\s*\(\s*(['\"`])(?P<path>[^'\"`]*\.node)\2\s*\)",
    re.IGNORECASE,
)
_DLOPEN_NODE_RE = re.compile(
    r"\bprocess\s*\.\s*dlopen\s*\([^)]*?\.node[^)]*?\)",
    re.IGNORECASE | re.DOTALL,
)
_PLATFORM_API_RE = re.compile(
    r"\b(?:os\s*\.\s*platform\s*\(\s*\)|process\s*\.\s*platform)"
)
_PLATFORM_TOKEN_RE = re.compile(r"['\"](?P<platform>win32|darwin|linux)['\"]")
_PLATFORM_GENERIC_NODE_RE = re.compile(
    r"(?:^|[/\\])(?:os|darwin|win32|windows|macos|linux)\.node$", re.IGNORECASE
)
_HOST_CONTEXT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("process.execPath", re.compile(r"\bprocess\s*\.\s*execPath\b")),
    ("__dirname", re.compile(r"\b__dirname\b")),
    ("process.cwd()", re.compile(r"\bprocess\s*\.\s*cwd\s*\(")),
    ("process.env", re.compile(r"\bprocess\s*\.\s*env\b")),
    ("context.extensionPath", re.compile(r"\bcontext\s*\.\s*extensionPath\b")),
    (
        "context.globalStorageUri",
        re.compile(r"\bcontext\s*\.\s*globalStorageUri\b"),
    ),
    ("context.storageUri", re.compile(r"\bcontext\s*\.\s*storageUri\b")),
)
_DIRECT_REQUIRE_INVOKE_RE = re.compile(
    r"require\s*\([^)]*?\.node[^)]*?\)\s*(?:\.\s*[A-Za-z_$][\w$]*)?\s*"
    r"\([^)]*(?:process\s*\.\s*execPath|__dirname|process\s*\.\s*cwd\s*\(|"
    r"process\s*\.\s*env|context\s*\.\s*(?:extensionPath|globalStorageUri|storageUri))",
    re.IGNORECASE | re.DOTALL,
)
_THEME_KEYWORDS = ("theme", "icon", "color", "snippet", "formatter")


def _matched_platforms(text: str) -> set[str]:
    if not _PLATFORM_API_RE.search(text):
        return set()
    return {match.group("platform") for match in _PLATFORM_TOKEN_RE.finditer(text)}


def _host_context_labels(text: str) -> list[str]:
    return [label for label, pattern in _HOST_CONTEXT_PATTERNS if pattern.search(text)]


def _assigned_native_names(text: str) -> set[str]:
    return {
        match.group("name")
        for pattern in (_DECLARED_REQUIRE_NODE_RE, _ASSIGNED_REQUIRE_NODE_RE)
        for match in pattern.finditer(text)
    }


def _has_host_context_native_invoke(text: str, names: Iterable[str]) -> bool:
    if _DIRECT_REQUIRE_INVOKE_RE.search(text):
        return True
    host_context = (
        r"process\s*\.\s*execPath|__dirname|process\s*\.\s*cwd\s*\(|"
        r"process\s*\.\s*env|context\s*\.\s*(?:extensionPath|globalStorageUri|storageUri)"
    )
    for name in names:
        pattern = re.compile(
            rf"\b{re.escape(name)}\b\s*(?:\.\s*[A-Za-z_$][\w$]*)?\s*"
            rf"\([^)]*(?:{host_context})",
            re.IGNORECASE | re.DOTALL,
        )
        if pattern.search(text):
            return True
    return False


def _is_suspicious_package_context(context: StaticAnalysisContext) -> bool:
    searchable: list[str] = [
        manifest_string(context.manifest, "name"),
        manifest_string(context.manifest, "displayName"),
        manifest_string(context.manifest, "description"),
    ]
    categories = context.manifest.get("categories")
    if isinstance(categories, list):
        searchable.extend(item for item in categories if isinstance(item, str))
    contributes = context.manifest.get("contributes")
    if isinstance(contributes, dict):
        if isinstance(contributes.get("themes"), list):
            searchable.append("theme")
        if isinstance(contributes.get("iconThemes"), list):
            searchable.append("icon theme")
        if isinstance(contributes.get("snippets"), list):
            searchable.append("snippet")
    haystack = " ".join(searchable).lower()
    return any(keyword in haystack for keyword in _THEME_KEYWORDS)


class NativeNodeLoaderRule:
    rule_id = "extrace.s13.native_node_loader"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    severity = Severity.HIGH
    description = (
        "Extension source loads a bundled .node native addon, with escalation for "
        "platform dispatch and host-context arguments passed to the native module."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        evidence: list[StaticEvidenceRef] = []
        files_with_loads = 0
        total_loads = 0
        platforms: set[str] = set()
        host_contexts: set[str] = set()
        platform_generic_native = False
        host_context_invoke = False

        for relative_path, text in iter_text_documents(context):
            require_matches = list(_REQUIRE_NODE_RE.finditer(text))
            dlopen_matches = list(_DLOPEN_NODE_RE.finditer(text))
            if not require_matches and not dlopen_matches:
                continue

            files_with_loads += 1
            total_loads += len(require_matches) + len(dlopen_matches)
            platforms.update(_matched_platforms(text))
            host_contexts.update(_host_context_labels(text))
            assigned_names = _assigned_native_names(text)
            host_context_invoke = (
                host_context_invoke
                or _has_host_context_native_invoke(text, assigned_names)
            )
            platform_generic_native = platform_generic_native or any(
                _PLATFORM_GENERIC_NODE_RE.search(match.group("path"))
                for match in require_matches
            )

            for match in [*require_matches, *dlopen_matches]:
                if len(evidence) >= _MAX_EVIDENCE:
                    break
                line_number = line_number_at(text, match.start())
                evidence.append(
                    file_evidence(
                        relative_path,
                        evidence_type_for(context, relative_path),
                        snippet=line_at(text, line_number) or ".node native load",
                        line_number=line_number,
                    )
                )

        if total_loads == 0:
            return []

        has_platform_dispatch = bool(platforms)
        non_linux_payload = (
            bool({"win32", "darwin"} & platforms) and "linux" not in platforms
        )
        suspicious_package = _is_suspicious_package_context(context)

        severity = Severity.MEDIUM
        confidence = Confidence.MEDIUM
        reasons = [".node native addon load"]
        if has_platform_dispatch:
            severity = Severity.HIGH
            confidence = Confidence.HIGH
            reasons.append("platform dispatch")
        if host_context_invoke:
            severity = Severity.HIGH
            confidence = Confidence.HIGH
            reasons.append(
                "native invocation receives host context: "
                + ", ".join(sorted(host_contexts))
            )
        if non_linux_payload:
            reasons.append("win32/darwin payload path with no linux branch")
        if suspicious_package:
            reasons.append("package context is theme/icon/snippet/formatter-like")
        if platform_generic_native:
            reasons.append("platform-generic native filename")

        if (
            has_platform_dispatch
            and host_context_invoke
            and (suspicious_package or platform_generic_native or non_linux_payload)
        ):
            severity = Severity.CRITICAL
            confidence = Confidence.HIGH

        categories = ["attack.T1059", "extrace.ext.native_loader"]
        if non_linux_payload:
            categories.append("extrace.host.platform_gate")

        blindspot = (
            " Linux-only dynamic sandboxes cannot detonate the non-linux native "
            "payload branch, so quiet runtime behavior must not lower static "
            "confidence."
            if non_linux_payload
            else ""
        )

        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=categories,
                severity=severity,
                confidence=confidence,
                title="Extension source loads a bundled native .node module",
                description=(
                    f"{total_loads} native .node load(s) found across "
                    f"{files_with_loads} source file(s). Signals: "
                    f"{'; '.join(reasons)}.{blindspot}"
                ),
                evidence=evidence,
                mitigation_hint=(
                    "Review the native module provenance and arguments. A theme "
                    "or simple UI extension that dispatches os.node/darwin.node "
                    "and passes process.execPath or __dirname into native code "
                    "should be treated as malicious pending reverse engineering."
                ),
            )
        ]


register(NativeNodeLoaderRule())

__all__ = ["NativeNodeLoaderRule"]
