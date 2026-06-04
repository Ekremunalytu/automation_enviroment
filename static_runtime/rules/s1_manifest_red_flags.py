"""S1 static rules: VSIX manifest (package.json) red flags (ES-3a, ADR 0016).

Three production rules over the parsed manifest:

* ``extrace.s1.activation_wildcard`` — ``activationEvents: ["*"]`` eager
  activation (the extension runs on every event, before any user intent).
* ``extrace.s1.suspicious_capabilities`` — install-time lifecycle scripts and/or
  a declared right to run in untrusted workspaces.
* ``extrace.s1.generic_publisher`` — missing or placeholder ``publisher``.

All three require a parseable manifest; an absent package.json yields no S1
findings (the file-tree rules in s3 still run).
"""

from __future__ import annotations

from packages.analysis_contracts.detection.enums import (
    AdversaryClass,
    Confidence,
    RuleLifecycle,
    Severity,
)
from packages.analysis_contracts.static_detection import StaticDetectionFinding
from static_runtime.context import StaticAnalysisContext
from static_runtime.rules._common import manifest_evidence, manifest_string
from static_runtime.rules.registry import register

# package.json `scripts` keys that execute code at install time — a VS Code
# extension almost never needs these, so their presence is a supply-chain smell.
_INSTALL_SCRIPT_KEYS = ("preinstall", "install", "postinstall")

# publisher values that indicate a scaffold/placeholder rather than a real
# marketplace identity.
_GENERIC_PUBLISHERS = frozenset(
    {
        "",
        "publisher",
        "your-publisher-name",
        "your-name",
        "name",
        "example",
        "undefined",
        "null",
        "test",
        "vscode",
    }
)

# Reserved / first-party brand publisher namespaces. A side-loaded VSIX that
# *claims* one of these is asserting a trusted vendor identity — the nf3xn
# reverse-shell PoC ships ``publisher: "ms-vscode"`` to borrow Microsoft's trust
# (signal MN, the nf3xn spec §4b). This is a curated, owner-extendable set of the
# highest-value impersonation targets, matched EXACTLY (not an ``ms-*`` prefix —
# that would flag every legitimate ``ms-python`` / ``ms-toolsai`` / ... extension).
_RESERVED_PUBLISHERS = frozenset(
    {
        "microsoft",
        "ms-vscode",
        "vscode",
        "github",
        "visualstudio",
        "google",
    }
)


class ActivationWildcardRule:
    rule_id = "extrace.s1.activation_wildcard"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    # HIGH (warns, never blocks): a '*' activation is an always-on, no-user-intent
    # foothold that amplifies every other capability — too load-bearing to bury at
    # LOW. Deliberately NOT a promoted blocker (some legitimate extensions still
    # declare '*'), so it surfaces prominently without rejecting before the sandbox.
    severity = Severity.HIGH
    description = (
        "Extension declares a '*' activation event, so it activates on every "
        "VS Code event regardless of user intent."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        if context.manifest_relative_path is None:
            return []
        events = context.manifest.get("activationEvents")
        if not isinstance(events, list) or "*" not in events:
            return []
        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1546", "extrace.ext.activation_wildcard"],
                severity=self.severity,
                confidence=Confidence.HIGH,
                title="Extension activates on the '*' wildcard event",
                description=self.description,
                evidence=[manifest_evidence(context, '"activationEvents": ["*"]')],
                mitigation_hint=(
                    "Confirm the extension genuinely needs to run on every event; "
                    "wildcard activation maximises the window for malicious "
                    "startup behaviour."
                ),
            )
        ]


class SuspiciousCapabilitiesRule:
    rule_id = "extrace.s1.suspicious_capabilities"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    severity = Severity.MEDIUM
    description = (
        "Extension manifest requests elevated capabilities (install-time "
        "lifecycle scripts and/or unrestricted execution in untrusted "
        "workspaces)."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        if context.manifest_relative_path is None:
            return []

        reasons: list[str] = []

        scripts = context.manifest.get("scripts")
        if isinstance(scripts, dict):
            present = [key for key in _INSTALL_SCRIPT_KEYS if key in scripts]
            if present:
                reasons.append(
                    "install-time lifecycle script(s): " + ", ".join(present)
                )

        capabilities = context.manifest.get("capabilities")
        if isinstance(capabilities, dict):
            untrusted = capabilities.get("untrustedWorkspaces")
            if isinstance(untrusted, dict) and untrusted.get("supported") is True:
                reasons.append("runs unrestricted in untrusted workspaces")

        if not reasons:
            return []

        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1059", "extrace.ext.suspicious_capabilities"],
                severity=self.severity,
                confidence=Confidence.MEDIUM,
                title="Extension manifest requests elevated capabilities",
                description=self.description + " Signals: " + "; ".join(reasons) + ".",
                evidence=[manifest_evidence(context, "; ".join(reasons))],
                mitigation_hint=(
                    "Review why the extension needs these capabilities; "
                    "install-time scripts in particular are a supply-chain "
                    "execution vector."
                ),
            )
        ]


class GenericPublisherRule:
    rule_id = "extrace.s1.generic_publisher"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    severity = Severity.LOW
    description = (
        "Extension manifest has a missing or placeholder publisher, so it lacks "
        "a verifiable marketplace identity."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        if context.manifest_relative_path is None:
            return []
        publisher = manifest_string(context.manifest, "publisher")
        normalized = publisher.lower()
        is_generic = normalized in _GENERIC_PUBLISHERS or "example" in normalized
        if not is_generic:
            return []
        shown = publisher or "<missing>"
        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1036", "extrace.ext.generic_publisher"],
                severity=self.severity,
                confidence=Confidence.MEDIUM,
                title="Extension has a missing or placeholder publisher",
                description=(
                    f"Extension publisher is {shown!r}, a placeholder or empty "
                    "value rather than a verifiable marketplace identity."
                ),
                evidence=[manifest_evidence(context, f'"publisher": "{shown}"')],
                mitigation_hint=(
                    "Treat unattributed extensions with caution; a real "
                    "marketplace publisher is a baseline trust signal."
                ),
            )
        ]


class ReservedPublisherSpoofRule:
    """Manifest claims a reserved / first-party brand publisher namespace.

    nf3xn (a reverse-shell PoC, ``documents/detection-design/nf3xn-reverse-shell-
    spec.md``) labels itself ``publisher: "ms-vscode"`` to impersonate Microsoft's
    official namespace and borrow its trust (signal MN). This rule flags a VSIX
    that *claims* a curated reserved/first-party brand identity
    (``_RESERVED_PUBLISHERS``).

    **Honest FP boundary — MEDIUM / WARN, never a blocker.** Genuine first-party
    extensions legitimately carry these same publishers (``ms-vscode.cpptools``,
    ``GitHub.copilot``), so name-only matching cannot, on its own, distinguish a
    spoof from the real thing — the durable disambiguator is the marketplace
    *verified-publisher* signal, which is **out of static scope**. The value here
    is in ExTrace's threat model of arbitrary / side-loaded VSIXs: a package
    asserting a trusted-vendor identity warrants a provenance check, and the
    signal is a strong escalator when it co-occurs with a malicious capability
    (e.g. the nf3xn reverse shell that ``s10`` convicts). It therefore surfaces
    for review and never rejects before the sandbox. Distinct from
    ``generic_publisher`` (missing/placeholder identity); this is *claimed-trusted*
    identity. ``adversary_class`` stays ``None`` per the static-IOC convention.
    """

    rule_id = "extrace.s1.reserved_publisher_spoof"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    severity = Severity.MEDIUM
    description = (
        "Extension manifest claims a reserved / first-party brand publisher "
        "namespace (microsoft / ms-vscode / vscode / github / ...), the trust-"
        "borrowing impersonation pattern used by malicious side-loaded VSIXs."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        if context.manifest_relative_path is None:
            return []
        publisher = manifest_string(context.manifest, "publisher")
        if publisher.lower() not in _RESERVED_PUBLISHERS:
            return []
        return [
            StaticDetectionFinding(
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                rule_lifecycle=self.lifecycle,
                categories=["attack.T1036", "extrace.ext.publisher_impersonation"],
                severity=self.severity,
                confidence=Confidence.MEDIUM,
                title="Extension claims a reserved first-party publisher namespace",
                description=(
                    f"Extension publisher is {publisher!r}, a reserved / first-party "
                    "brand namespace. A side-loaded extension that claims a trusted "
                    "vendor identity is impersonating that vendor to borrow its "
                    "trust. Name-only matching cannot by itself separate a spoof "
                    "from a genuine first-party extension (the marketplace "
                    "verified-publisher signal, out of static scope, is the durable "
                    "disambiguator), so this is a provenance-review signal and a "
                    "strong escalator when it co-occurs with a malicious capability."
                ),
                evidence=[manifest_evidence(context, f'"publisher": "{publisher}"')],
                mitigation_hint=(
                    "Verify the extension's provenance against the claimed vendor "
                    "(marketplace verified-publisher / signature). Treat a "
                    "first-party identity claim paired with any malicious "
                    "capability as confirmed impersonation."
                ),
            )
        ]


register(ActivationWildcardRule())
register(SuspiciousCapabilitiesRule())
register(GenericPublisherRule())
register(ReservedPublisherSpoofRule())

__all__ = [
    "ActivationWildcardRule",
    "GenericPublisherRule",
    "ReservedPublisherSpoofRule",
    "SuspiciousCapabilitiesRule",
]
