"""S17 static rule: a sensitive credential file is read *and* a network egress
sink is present in the same module — credential exfiltration (ecm3401 CRED-X).

The ecm3401 "Educational Attack Suite" ships ``func_steal_ssh``: it reads
``~/.ssh/id_rsa`` (path built at runtime as ``/Users/${user}/.ssh/id_rsa``) and
POSTs the contents to an attacker receiver. That is the canonical **confidentiality
breach** shape — a high-value secret read, then shipped off-host. See
``documents/detection-design/ecm3401-malicious-suite-spec.md`` (signals CRED1 /
CRED-X).

This rule approximates the spec's CRED-X *taint* (source = sensitive-file read,
sink = network) with a **file-level conjunction**: in one source file all of

  (1) a reference to a sensitive credential path (``.ssh`` / ``id_rsa`` /
      ``id_ed25519`` / ``.aws/credentials`` / ``.gnupg`` / ``.netrc`` /
      ``.kube/config`` / ``.npmrc`` / ``.docker/config.json`` / gcloud creds),
  (2) a filesystem *read* primitive (``fs.readFile`` / ``readFileSync`` /
      ``createReadStream``), and
  (3) an outbound network egress sink (``fetch`` / ``http(s).request`` /
      ``http(s).get`` / ``axios`` / ``node-fetch`` / ``XMLHttpRequest``)

co-occur. The credential-path token is matched **anywhere in the file**, not only
inside the read call, on purpose: ecm3401 concatenates the path at runtime
(``/Users/${u}/.ssh/id_rsa``), so a ``metavariable``-style literal-in-the-read
match would miss it — the durable signal is that the file *names* a credential
path, *reads* a file, and *talks to the network*.

The conjunction is load-bearing because each part alone is wildly benign. Many
extensions read files (1)+(2); many make HTTP calls (3); plenty reference a
credential path in a comment or a settings key. It is the three together — read a
credential store **and** hold an egress channel — that signals exfiltration.

Severity is **HIGH / WARN, not CRITICAL / BLOCK** (mirrors ``s8``). Unlike the
``s10``/``s11``/``s16`` finished-primitive rules, this is a file-level
*co-occurrence*, not proven dataflow: a legitimate cloud/SSH extension can read
``.aws/credentials`` *and* call its provider's API in the same file without
exfiltrating anything (it never wires the secret into the request body). So the
finding **surfaces a credential-exfiltration capability for review**, it does not
convict before the sandbox. ``adversary_class`` stays ``None`` per the static-IOC
convention; the runtime read->egress correlation is the dynamic
``extrace.a1.credential_read_then_network`` / ``extrace.a4.workspace_exfil`` rules'
job. The known FN (spec §7): an obfuscated path (``["id","_rsa"].join("")``) or a
base64-encoded credential name slips the literal token match and is left to the
dynamic plane.
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

# (1) A sensitive credential path. Matched anywhere in the file (not only inside
# the read call) so a runtime-concatenated path (``/Users/${u}/.ssh/id_rsa``) is
# still caught. Each token is a specific credential-store path, not a bare word —
# ``credentials`` alone is too common, so only ``.aws/credentials`` qualifies.
_SENSITIVE_PATH_RE = re.compile(
    r"\.ssh[\\/]"
    r"|\bid_(?:rsa|ed25519|ecdsa|dsa)\b"
    r"|\.aws[\\/]+credentials"
    r"|\.gnupg\b"
    r"|\.netrc\b"
    r"|\.kube[\\/]+config"
    r"|\.npmrc\b"
    r"|\.docker[\\/]+config\.json"
    r"|\.config[\\/]+gcloud",
    re.IGNORECASE,
)

# (2) A filesystem read primitive (fs-qualified or the bare/destructured forms).
_FS_READ_RE = re.compile(
    r"\b(?:fs\s*\.\s*)?(?:readFileSync|readFile|createReadStream)\s*\("
)

# (3) An outbound network egress sink — the exfil channel. ``net.connect`` is
# excluded (that is the reverse-shell surface owned by s10); this rule keys on
# HTTP-style egress where a body is POSTed.
_NETWORK_SINK_RE = re.compile(
    r"\bfetch\s*\("
    r"|\bhttps?\s*\.\s*(?:request|get)\s*\("
    r"|require\(\s*['\"](?:node-fetch|axios|got|undici|superagent)['\"]\s*\)"
    r"|\baxios\s*(?:\.\s*(?:post|get|put|patch|request)\s*)?\("
    r"|\bXMLHttpRequest\b"
)


class CredentialExfilRule:
    rule_id = "extrace.s17.credential_exfil"
    rule_version = "1.0.0"
    lifecycle = RuleLifecycle.PRODUCTION
    adversary_class: AdversaryClass | None = None
    # HIGH / WARN, not CRITICAL / BLOCK: a file-level co-occurrence (read a
    # credential store + hold an egress channel), not proven dataflow. A
    # legitimate cloud/SSH extension can do both without exfiltrating, so this
    # surfaces the capability for review rather than rejecting before the sandbox.
    severity = Severity.HIGH
    description = (
        "Extension source reads a sensitive credential file (.ssh/id_rsa, "
        ".aws/credentials, etc.) and holds an outbound network egress sink in the "
        "same module — a credential-exfiltration capability."
    )

    def evaluate(self, context: StaticAnalysisContext) -> list[StaticDetectionFinding]:
        for relative_path, text in iter_text_documents(context):
            sensitive = _SENSITIVE_PATH_RE.search(text)
            if sensitive is None:
                continue
            if _FS_READ_RE.search(text) is None:
                continue
            if _NETWORK_SINK_RE.search(text) is None:
                continue
            return [self._finding(context, relative_path, text)]
        return []

    def _finding(
        self,
        context: StaticAnalysisContext,
        relative_path: str,
        text: str,
    ) -> StaticDetectionFinding:
        evidence: list[StaticEvidenceRef] = []
        # The credential-path token first (the load-bearing evidence), then the
        # read primitive, then the egress sink.
        for pattern in (_SENSITIVE_PATH_RE, _FS_READ_RE, _NETWORK_SINK_RE):
            self._add_first_match(evidence, context, relative_path, text, pattern)

        return StaticDetectionFinding(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            rule_lifecycle=self.lifecycle,
            categories=[
                "attack.T1552.004",
                "attack.T1041",
                "extrace.ext.credential_exfil",
            ],
            severity=self.severity,
            confidence=Confidence.MEDIUM,
            title="Extension reads a credential file and has a network egress sink",
            description=(
                "The extension source references a sensitive credential path "
                "(SSH private key, cloud credentials, gnupg, netrc, kube/npm/docker "
                "config), reads a file, and holds an outbound HTTP egress sink in "
                "the same module. Together these are the credential-exfiltration "
                "shape: read a high-value secret and ship it off-host. The match "
                "requires the credential-path reference, a read primitive, and a "
                "network sink together, so each individually benign part does not "
                "fire. This surfaces an exfiltration capability for review; it is "
                "not proof the secret reaches the wire (a legitimate cloud/SSH "
                "extension may read credentials and call its provider API)."
            ),
            evidence=evidence,
            mitigation_hint=(
                "Confirm what the extension does with the credential file contents "
                "and where the network sink sends them. Reading an SSH private key "
                "or cloud credentials and POSTing data off-host is credential "
                "theft; block the extension and the destination."
            ),
        )

    @staticmethod
    def _add_first_match(
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
                snippet=line_at(text, line_number) or "credential exfil",
                line_number=line_number,
            )
        )


register(CredentialExfilRule())

__all__ = ["CredentialExfilRule"]
