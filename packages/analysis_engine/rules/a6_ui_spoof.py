"""A6 detection rule: startup-time credential prompt style UI."""

from __future__ import annotations

import re

from packages.analysis_contracts import ActivationReport
from packages.analysis_contracts.detection import (
    AdversaryClass,
    Confidence,
    DetectionFinding,
    RuleLifecycle,
    Severity,
)
from packages.analysis_engine.rules._common import (
    activation_time,
    event_message,
    make_evidence_ref,
    rel_time,
)
from packages.analysis_engine.rules.registry import register

_PROMPT_PATTERN = re.compile(
    r"(showquickpick|showinputbox|showinformationmessage|showwarningmessage|"
    r"showerrormessage|quick pick|input box|notification)",
    re.IGNORECASE,
)


class StartupUiPromptRule:
    rule_id = "extrace.a6.startup_ui_prompt"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = AdversaryClass.A6
    severity = Severity.MEDIUM
    description = "Suspicious startup-time UI prompt behavior."

    def evaluate(self, report: ActivationReport) -> list[DetectionFinding]:
        activated_at = activation_time(report)
        if activated_at is None:
            return []

        prompt_events = [
            event
            for event in report.evidence_events
            if event.kind in {"extension_host", "log"}
            and _PROMPT_PATTERN.search(event_message(event))
        ]
        for prompt_event in prompt_events:
            prompt_time = rel_time(prompt_event)
            if prompt_time < activated_at or prompt_time - activated_at <= 2:
                return [
                    DetectionFinding(
                        rule_id=self.rule_id,
                        rule_version=self.rule_version,
                        rule_lifecycle=self.lifecycle,
                        categories=["extrace.ext.startup_ui_prompt"],
                        severity=self.severity,
                        confidence=Confidence.MEDIUM,
                        title="Startup-time UI prompt before normal activation",
                        description=(
                            "The extension showed prompt-like UI at startup "
                            "before activation settled, which matches known "
                            "post-install social-engineering patterns."
                        ),
                        evidence=[make_evidence_ref(prompt_event)],
                        adversary_class=self.adversary_class,
                        mitigation_hint=(
                            "Review activation-time UI flows and block prompts "
                            "that solicit secrets before user intent is clear."
                        ),
                    )
                ]
        return []


RULE = StartupUiPromptRule()
register(RULE)

__all__ = ["RULE", "StartupUiPromptRule"]
