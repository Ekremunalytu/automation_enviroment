"""S20 static rule: an extension wires up a remote-access (RMM) client for
unattended relay access — the "bring your own ScreenConnect" (BYOSC) abuse.

Detection family for the `snowshono` / `trailofbits/vsix-zoo` campaign's **Stage 3**
(the `ScreenConnect.ClientSetup.msi` RMM-as-RAT). The campaign chains a typosquat
extension (`ShowSnowcrypto.SnowShoNo`, already convicted by `s11`'s PowerShell
download cradle — see ``kagema-detection-spec.md``) to a hidden-PowerShell
``irm | iex`` downloader, which finally drops a **legitimately code-signed
ScreenConnect (ConnectWise Control) client** configured to call back to an
attacker relay. ScreenConnect is a real, signed RMM tool; the malicious part is
not a custom binary but the *configuration* — the client is pointed at the
operator's relay for **unattended, persistent remote control**. AV/reputation sees
a signed RMM and waves it through, and every build rotates the MSI hash, so neither
a signature nor a hash blocklist holds. The durable signal is the **relay /
unattended-access configuration**, not the binary. See
``documents/detection-design/snowshono-rmm-spec.md`` for the full BYOSC threat
model, the attack chain, the as-built layer map, and the deferred work (the MSI
static config parser and the Windows dynamic node).

This rule covers the variant ExTrace's text-scanning static layer can actually
observe: an extension that **embeds the ScreenConnect relay-install reference
directly** — either an install URL
(``…/Bin/ScreenConnect.ClientSetup.msi?e=Access&y=Guest``) or a launch /
connection string (``&h=<relay>&p=<port>&s=<session>&k=<key>``). That is the shape
the sibling BYOSC campaigns (TheseVibesAreOff / ClawdBot) ship verbatim in the
extension. The `snowshono` variant that fetches the MSI indirectly through the
PowerShell cradle is already convicted by ``s11``; the two rules are complementary
(``s11`` = the indirect cradle, ``s20`` = the embedded BYOSC install).

The rule keys on the **conjunction**, never the parts — exactly the ``s11`` /
``s18`` discipline:

  (A) a remote-access (RMM) **client reference** — the ScreenConnect / ConnectWise
      Control product / installer / service-binary strings; and
  (B) an **unattended-access relay configuration** — either the ScreenConnect
      ``e=Access`` + ``y=Guest`` launch parameters (the silent, persistent-access
      marker, as opposed to attended ``e=Support``), or the relay connection
      string (``&s=<session>`` … ``&k=<key>`` / ``&h=<relay>&p=<port>``).

A bare mention of "ScreenConnect" alone is **not** convicted — a remote-support or
RMM-vendor extension can legitimately reference the product. It is the conjunction
with an *unattended-guest relay config* that has no benign extension use: a VS Code
extension has no reason to silently install an RMM client set for unattended access
to an arbitrary relay.

**Severity is HIGH / WARN, not CRITICAL / BLOCK** — the ``s18`` precedent, not the
``s10``/``s11`` one. Unlike a hidden ``powershell … | iex`` cradle (no benign
cousin), RMM abuse *has* a conceivable legitimate cousin (an official RMM-vendor or
remote-support extension), so blocking before the sandbox would risk a
trust-destroying false positive. The finding surfaces the BYOSC capability for
review. A **confidence booster** refines without gating it: when the relay
endpoint is a **bare IPv4** rather than a named ``*.screenconnect.com`` host (the
textbook BYOSC tell — legitimate ConnectWise uses a named relay, never a raw IP),
confidence is HIGH; otherwise MEDIUM.

``adversary_class`` stays ``None`` per the static-IOC convention
(architecture-reconciliation doc): in-house static rules report a capability / IOC
surface and leave adversary-class attribution to the dynamic a-rules. The
conceptual class is **A4** (remote-loader / RMM-as-RAT) — recorded in the spec
rather than on a firing rule because for this win32-gated, Windows-only-MSI family
the Linux dynamic plane never fires (the same coverage gap as ``s11`` / kagema, spec
§5). The rule logic is general (no `snowshono` / real-IOC literal — this rule is
behaviour-based; the campaign's relay hosts live in the separate ``blacklist_domains``
data file matched by ``s4``/``a7``, not in ``s20``, and the MSI/extension hashes are
reference-only in the spec appendix); the synthetic test inputs use RFC 5737 /
RFC 2606 placeholders.

Known gaps (spec §6, honest): the **MSI's embedded ``System.config`` is not parsed**
— extracting ``h/p/s/k`` from the dropped binary needs an MSI static parser (a
deferred capability; the binary is never opened in this repo); a relay reference
hidden behind string concatenation / encoding, or carried only in the dropped MSI
(never in the extension text), slips this text-layer match and is left to the
(Windows) dynamic plane.
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

_MAX_EVIDENCE = 9

# (A) Remote-access-software (RMM) client reference — the BYOSC product anchor.
# ScreenConnect / ConnectWise Control is the dominant family; the installer and
# service/client binary names are its product strings. Keying on the product is
# keying on the *behaviour class* (RMM abuse), the same way s11 keys on the
# `powershell` literal for the cradle class — not a sample signature.
_RMM_CLIENT_RE = re.compile(
    r"ScreenConnect"
    r"|ConnectWise\s*Control"
    r"|ClientSetup\.msi"
    r"|\.WindowsClient\b"
    r"|\.ClientService\b",
    re.IGNORECASE,
)

# (B1) Unattended-access launch parameters: e=Access (execution type = unattended,
# vs the attended e=Support) together with y=Guest. This is the silent,
# persistent-remote-control marker — the line that separates a BYOSC RAT install
# from a benign attended remote-support session. Matched in either order within a
# bounded same-region window so a launch URL / config blob qualifies but two
# unrelated query params far apart do not.
_UNATTENDED_LAUNCH_RE = re.compile(
    r"\be=Access\b[^\n]{0,80}\by=Guest\b|\by=Guest\b[^\n]{0,80}\be=Access\b",
    re.IGNORECASE,
)

# (B2) Relay connection string: the ScreenConnect launch parameters that carry the
# session id and the relay key (``&s=<session>`` adjacent to ``&k=<key>``), or the
# relay host + port pair (``&h=<relay>&p=<port>``). Distinctive of a ScreenConnect
# connection URL; bounded so the tokens must co-occur in one launch-parameter span.
_RELAY_CONNSTRING_RE = re.compile(
    r"[?&]s=[0-9A-Fa-f-]{6,}[^\n]{0,80}[?&]k=[A-Za-z0-9+/=]{6,}"
    r"|[?&]h=[^\s&\"']{1,253}&p=\d{1,5}\b",
    re.IGNORECASE,
)

# Booster (the "non-ConnectWise relay" tell): the relay endpoint is a bare IPv4 —
# a URL host (``://<ip>``) or the ScreenConnect ``h=`` relay value (``&h=<ip>``) —
# rather than a named ``*.screenconnect.com`` instance. Legitimate ConnectWise uses
# a named relay; a raw IP is the textbook BYOSC infrastructure marker. A confidence
# raiser, never a gate.
_BARE_IP_RELAY_RE = re.compile(
    r"(?:https?://|[?&]h=)(?:\d{1,3}\.){3}\d{1,3}\b",
    re.IGNORECASE,
)


def _relay_config_match(text: str) -> re.Match[str] | None:
    """First unattended-launch or relay-connection-string match, if any."""
    return _UNATTENDED_LAUNCH_RE.search(text) or _RELAY_CONNSTRING_RE.search(text)


class RmmRemoteAccessAbuseRule:
    rule_id = "extrace.s20.rmm_remote_access"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    # Class-less per the static-IOC convention (reconciliation doc). A4
    # (remote-loader / RMM-as-RAT) is the conceptual class, documented in the
    # snowshono spec — the win32-gated, Windows-only-MSI family leaves the Linux
    # dynamic plane that would carry A4 blind (spec §5).
    adversary_class: AdversaryClass | None = None
    # HIGH / WARN, not CRITICAL / BLOCK: RMM abuse has a conceivable legitimate
    # cousin (an official remote-support / RMM-vendor extension), so this surfaces
    # the BYOSC capability for review rather than convicting before the sandbox —
    # the s18 precedent.
    severity = Severity.HIGH
    description = (
        "Extension wires up a remote-access (RMM) client — ScreenConnect / "
        "ConnectWise Control — for unattended relay access (e=Access&y=Guest or a "
        "relay connection string): the bring-your-own-ScreenConnect (BYOSC) "
        "RMM-as-RAT deployment shape."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        for relative_path, text in iter_text_documents(context):
            if _RMM_CLIENT_RE.search(text) is None:
                continue
            relay = _relay_config_match(text)
            if relay is None:
                continue
            bare_ip = _BARE_IP_RELAY_RE.search(text)
            return [self._finding(context, relative_path, text, relay, bare_ip)]
        return []

    def _finding(
        self,
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        relay: re.Match[str],
        bare_ip: re.Match[str] | None,
    ) -> StaticDetectionFinding:
        evidence: list[StaticEvidenceRef] = []
        # Client reference, then the relay config (the load-bearing evidence), then
        # the bare-IP relay if the booster fired.
        self._add_match(evidence, context, relative_path, text, _RMM_CLIENT_RE)
        self._add_match(evidence, context, relative_path, text, relay.re)
        if bare_ip is not None:
            self._add_match(evidence, context, relative_path, text, _BARE_IP_RELAY_RE)

        confidence = Confidence.HIGH if bare_ip is not None else Confidence.MEDIUM
        relay_note = (
            " The relay endpoint is a bare IP address rather than a named "
            "*.screenconnect.com instance — the textbook BYOSC tell, since "
            "legitimate ConnectWise uses a named relay."
            if bare_ip is not None
            else ""
        )
        return StaticDetectionFinding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            rule_lifecycle=self.lifecycle,
            categories=["attack.T1219", "extrace.ext.rmm_remote_access"],
            severity=self.severity,
            confidence=confidence,
            title="Extension installs an RMM client for unattended relay (BYOSC)",
            description=(
                "The extension references a remote-access (RMM) client — "
                "ScreenConnect / ConnectWise Control — together with an "
                "unattended-access relay configuration (the e=Access&y=Guest launch "
                "parameters or a &h=/&p=/&s=/&k= relay connection string). "
                "ScreenConnect is a legitimate, code-signed remote-management tool, "
                "so the malicious element is not a custom binary but the "
                "configuration: the client is pointed at an attacker relay for "
                "silent, persistent remote control (a 'bring your own ScreenConnect' "
                "RMM-as-RAT deployment). A VS Code extension has no legitimate reason "
                "to silently install an RMM client configured for unattended guest "
                "access. The match requires the client reference and the "
                "unattended-relay configuration together, so a benign mention of the "
                "product, or an unrelated query string, does not fire." + relay_note
            ),
            evidence=evidence,
            mitigation_hint=(
                "Treat an extension that installs a remote-access client for "
                "unattended relay access as a RAT deployment — reject it. RMM-as-RAT "
                "abuse rotates the installer hash and rides a legitimate signature, "
                "so block on the relay configuration (the e=Access&y=Guest / "
                "&h=&p=&k= shape), not the binary, and isolate the relay endpoint. A "
                "legitimate remote-support integration uses attended access and the "
                "vendor's named relay, not unattended guest access to a raw IP."
            ),
        )

    @staticmethod
    def _add_match(
        evidence: list[StaticEvidenceRef],
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
        pattern: re.Pattern[str],
    ) -> None:
        if len(evidence) >= _MAX_EVIDENCE:
            return
        match = pattern.search(text)
        if match is None:
            return
        line_number = line_number_at(text, match.start())
        evidence.append(
            file_evidence(
                relative_path,
                evidence_type_for(context, relative_path),
                snippet=line_at(text, line_number) or "rmm relay config",
                line_number=line_number,
            )
        )


register(RmmRemoteAccessAbuseRule())

__all__ = ["RmmRemoteAccessAbuseRule"]
