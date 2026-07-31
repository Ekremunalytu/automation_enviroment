"""S14 static rule: VS Code globalState dormancy / throttle gate."""

from __future__ import annotations

import re

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
    find_local_pattern_cluster,
    iter_text_documents,
    line_number_at,
    snippet_at,
)
from static_runtime.rules.registry import register

_MAX_EVIDENCE = 25
_MAX_CHAIN_SPAN = 8 * 1024

_GLOBALSTATE_GET_RE = re.compile(r"\bcontext\s*\.\s*globalState\s*\.\s*get\s*\(")
_GLOBALSTATE_UPDATE_RE = re.compile(r"\bcontext\s*\.\s*globalState\s*\.\s*update\s*\(")
_TIME_MARKER_RE = re.compile(
    r"\b(?:Date\s*\.\s*now\s*\(|new\s+Date\s*\(|getTime\s*\(|"
    r"currentTime|lastActivated|lastActivation|lastRun|timestamp|activationState)\b",
    re.IGNORECASE,
)
_GATE_RE = re.compile(
    r"\bif\s*\([^)]*(?:Date\s*\.\s*now\s*\(|currentTime|now|lastActivated|"
    r"lastActivation|lastRun|timestamp|activationState)[^)]*(?:[<>]=?|={2,3}|!={1,2})",
    re.IGNORECASE | re.DOTALL,
)
_DURATION_RE = re.compile(
    r"\b(?:172800000|86400000|3600000|24\s*\*\s*60\s*\*\s*60\s*\*\s*1000|"
    r"2\s*\*\s*24\s*\*\s*60\s*\*\s*60\s*\*\s*1000|cooldown|throttle|"
    r"rearm|reArm|ttl)\b",
    re.IGNORECASE,
)
_PAYLOAD_CALL_RE = re.compile(
    r"\b(?:init|run|start|payload|native|activate)\s*\(", re.IGNORECASE
)


class GlobalStateDormancyRule:
    rule_id = "extrace.s14.globalstate_dormancy"
    rule_version = "1.1.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    severity = Severity.MEDIUM
    description = (
        "Extension source uses VS Code context.globalState with timestamp gating, "
        "which can throttle payload execution and hide behavior from repeated "
        "sandbox runs."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        evidence: list[StaticEvidenceRef] = []
        files_with_dormancy = 0
        reasons: set[str] = set()

        for relative_path, text in iter_text_documents(context):
            cluster = find_local_pattern_cluster(
                text,
                (
                    _GLOBALSTATE_GET_RE,
                    _GLOBALSTATE_UPDATE_RE,
                    _TIME_MARKER_RE,
                    _PAYLOAD_CALL_RE,
                    _GATE_RE,
                ),
                max_span=_MAX_CHAIN_SPAN,
            )
            used_duration = False
            if cluster is None:
                cluster = find_local_pattern_cluster(
                    text,
                    (
                        _GLOBALSTATE_GET_RE,
                        _GLOBALSTATE_UPDATE_RE,
                        _TIME_MARKER_RE,
                        _PAYLOAD_CALL_RE,
                        _DURATION_RE,
                    ),
                    max_span=_MAX_CHAIN_SPAN,
                )
                used_duration = cluster is not None
            if cluster is None:
                continue

            files_with_dormancy += 1
            reasons.add("context.globalState get/update")
            reasons.add("timestamp or activation-state comparison")
            if used_duration or any(
                _DURATION_RE.search(text, match.start(), match.end() + 512)
                for match in cluster
            ):
                reasons.add("cooldown/re-arm duration")
            reasons.add("gated init/payload call")

            for match in cluster[:2]:
                if len(evidence) >= _MAX_EVIDENCE:
                    break
                line_number = line_number_at(text, match.start())
                evidence.append(
                    file_evidence(
                        relative_path,
                        evidence_type_for(context, relative_path),
                        snippet=snippet_at(text, match.start())
                        or "context.globalState",
                        line_number=line_number,
                    )
                )

        if files_with_dormancy == 0:
            return []

        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1497", "extrace.ext.dormancy"],
                severity=self.severity,
                confidence=Confidence.MEDIUM,
                title="Extension uses globalState dormancy / throttle gating",
                description=(
                    f"globalState dormancy pattern found in {files_with_dormancy} "
                    f"source file(s). Signals: {'; '.join(sorted(reasons))}. "
                    "Persisted activation timestamps can cause repeated dynamic "
                    "runs to skip the payload unless the VS Code profile and "
                    "globalState are reset."
                ),
                evidence=evidence,
                mitigation_hint=(
                    "Run dynamic analysis with a fresh VS Code profile/globalState "
                    "for each attempt, and escalate when this co-occurs with native "
                    "loaders, network IOCs, or obfuscation."
                ),
            )
        ]


register(GlobalStateDormancyRule())

__all__ = ["GlobalStateDormancyRule"]
