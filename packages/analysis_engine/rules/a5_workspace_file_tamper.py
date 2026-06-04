"""A5 detection rule: workspace file read then rewritten (integrity / clipper)."""

from __future__ import annotations

from packages.analysis_contracts import ActivationReport, EvidenceEvent
from packages.analysis_contracts.detection import (
    AdversaryClass,
    Confidence,
    DetectionFinding,
    RuleLifecycle,
    Severity,
)
from packages.analysis_engine.rules._common import (
    make_evidence_ref,
    rel_time,
    target_file_events,
)
from packages.analysis_engine.rules.registry import register

_WORKSPACE_PREFIX = "/workspace/"


class WorkspaceFileTamperRule:
    """Integrity counterpart to A4 (which covers read -> network exfiltration).

    Fires when the target extension *rewrites* a workspace file it had read — the
    read -> modify -> save signature of a crypto-clipper / wallet-hijacker
    (``apollyon`` ``extractCryptoAddresses`` -> ``replaceCryptoAddresses`` ->
    ``applyEdit`` + ``document.save()``). This is the dynamic counterpart of the
    static ``extrace.s9.crypto_address_scan`` capability signal.

    MEDIUM, not HIGH: the runtime file layer sees "read then wrote the same file"
    but not *what* changed, and legitimate formatters / auto-fixers do exactly
    this. The finding surfaces the integrity impact for review and escalates in
    context (a target already flagged for crypto-awareness or auto-activation),
    rather than convicting on the write alone.
    """

    rule_id = "extrace.a5.workspace_file_tamper"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = AdversaryClass.A5
    severity = Severity.MEDIUM
    description = (
        "Workspace file read and then rewritten in place (integrity tampering)."
    )

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        # Earliest target read per workspace path — a later write to any path that
        # was read at or before the write time is the scan-then-rewrite signature.
        reads: dict[str, EvidenceEvent] = {}
        for event in target_file_events(report):
            if event.operation.strip().lower() == "read" and event.path.startswith(
                _WORKSPACE_PREFIX
            ):
                existing = reads.get(event.path)
                if existing is None or rel_time(event) < rel_time(existing):
                    reads[event.path] = event

        findings: list[DetectionFinding] = []
        tampered: set[str] = set()
        for event in target_file_events(report):
            if (
                event.operation.strip().lower() != "write"
                or not event.path.startswith(_WORKSPACE_PREFIX)
                or event.path in tampered
            ):
                continue
            read_event = reads.get(event.path)
            # Require the read to precede (or coincide with) the write — the
            # scan-then-rewrite ordering, not an unrelated fresh-file write.
            if read_event is None or rel_time(event) < rel_time(read_event):
                continue
            tampered.add(event.path)
            findings.append(
                DetectionFinding(
                    rule_id=self.rule_id,
                    rule_version=self.rule_version,
                    rule_lifecycle=self.lifecycle,
                    categories=["attack.T1565", "extrace.host.workspace_tamper"],
                    severity=self.severity,
                    confidence=Confidence.MEDIUM,
                    title="Workspace file read and then rewritten in place",
                    description=(
                        "The extension read a workspace file and then wrote back "
                        "to the same path — the read-modify-save signature of a "
                        "crypto-clipper / content-rewriter. Legitimate formatters "
                        "also do this, so confirm the change against the "
                        "extension's stated purpose; treat it as hostile when the "
                        "extension is otherwise flagged (crypto-awareness, "
                        "automatic activation, or unexpected file scope)."
                    ),
                    evidence=[
                        make_evidence_ref(read_event),
                        make_evidence_ref(event),
                    ],
                    adversary_class=self.adversary_class,
                    mitigation_hint=(
                        "Review what the extension changed in the workspace file "
                        "and whether in-place rewrites match its purpose; revert "
                        "and remove if the edit was unsolicited."
                    ),
                )
            )
        return findings


RULE = WorkspaceFileTamperRule()
register(RULE)

__all__ = ["RULE", "WorkspaceFileTamperRule"]
