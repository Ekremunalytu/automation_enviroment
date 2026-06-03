"""S8 static rule: hardcoded chat-service exfiltration webhooks.

Detects a hardcoded Discord / Slack / Telegram webhook (or bot) endpoint in the
extension source. A VS Code extension has almost no legitimate reason to embed a
chat-service *ingestion* endpoint: these URLs are the canonical drop point for
commodity infostealers (the ``apollyon`` PoC class — ``document.getText()`` ->
``axios.post(<discord webhook>)``). The endpoints are matched by their *exact*
ingestion-path shape (``/api/webhooks/<id>/<token>`` etc.), not a bare host
mention, so a donation / community link to ``discord.com`` in a README does not
fire — see ``documents/detection-design/apollyon-detection-spec.md`` (signal S1).

This rule reports the exfiltration *channel* (a static capability/IOC surface),
not adversary behaviour: ``adversary_class`` stays ``None`` and the runtime
read->egress correlation is owned by the dynamic ``extrace.a4.workspace_exfil``
rule. Severity is HIGH (a strong, near-zero-FP exfil-channel signal) but not
CRITICAL and not a promoted blocker, so the gate WARNs and the dynamic sandbox
still runs (ADR 0016 block-and-warn; see the architecture-reconciliation doc).
One finding aggregates every hit; the webhook token rides through the shared
secret-redaction path before it can reach the report JSON / UI / logs.
"""

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
    iter_text_documents,
    line_at,
    line_number_at,
)
from static_runtime.rules.registry import register

_MAX_EVIDENCE = 25

# Each entry is (channel-family label, compiled endpoint regex). The patterns
# match the *ingestion* path shape, not a bare host, so a non-webhook mention of
# the service (a README link, an OAuth docs URL) does not match. ``discordapp.com``
# is the legacy host alias; ``ptb.`` / ``canary.`` are the test-build subdomains.
_WEBHOOK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "Discord",
        re.compile(
            r"https?://(?:(?:ptb|canary)\.)?discord(?:app)?\.com"
            r"/api/(?:v\d+/)?webhooks/\d+/[\w-]+",
            re.IGNORECASE,
        ),
    ),
    (
        "Slack",
        re.compile(
            r"https?://hooks\.slack\.com/services/[A-Za-z0-9]+/[A-Za-z0-9]+/[A-Za-z0-9]+"
        ),
    ),
    (
        "Telegram",
        re.compile(r"https?://api\.telegram\.org/bot\d+:[\w-]+/", re.IGNORECASE),
    ),
)


class ExfiltrationWebhookRule:
    rule_id = "extrace.s8.exfil_webhook"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    severity = Severity.HIGH
    description = (
        "Extension source hardcodes a chat-service exfiltration webhook "
        "(Discord / Slack / Telegram), the canonical drop point for commodity "
        "infostealers."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        evidence: list[StaticEvidenceRef] = []
        channels: set[str] = set()
        total_hits = 0

        for relative_path, text in iter_text_documents(context):
            for channel, pattern in _WEBHOOK_PATTERNS:
                for match in pattern.finditer(text):
                    channels.add(channel)
                    total_hits += 1
                    self._add_evidence(
                        evidence, context, relative_path, text, match.start()
                    )

        if not channels:
            return []

        listed = ", ".join(sorted(channels))
        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1567", "extrace.ext.exfil_webhook"],
                severity=self.severity,
                confidence=Confidence.HIGH,
                title="Extension hardcodes a chat-service exfiltration webhook",
                description=(
                    f"{total_hits} hardcoded chat-service webhook endpoint(s) "
                    f"found in the extension source. Channel(s): {listed}. A "
                    "VS Code extension has no legitimate reason to embed a "
                    "Discord / Slack / Telegram ingestion endpoint; these are the "
                    "canonical exfiltration drop points for infostealer payloads."
                ),
                evidence=evidence,
                mitigation_hint=(
                    "Treat a hardcoded chat-service webhook as an exfiltration "
                    "channel until proven otherwise; confirm what data is POSTed "
                    "to it and block the destination."
                ),
            )
        ]

    @staticmethod
    def _add_evidence(
        evidence: list[StaticEvidenceRef],
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        index: int,
    ) -> None:
        if len(evidence) >= _MAX_EVIDENCE:
            return
        line_number = line_number_at(text, index)
        evidence.append(
            file_evidence(
                relative_path,
                evidence_type_for(context, relative_path),
                snippet=line_at(text, line_number) or "exfiltration webhook",
                line_number=line_number,
            )
        )


register(ExfiltrationWebhookRule())

__all__ = ["ExfiltrationWebhookRule"]
