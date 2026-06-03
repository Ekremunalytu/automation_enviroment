"""Fire / silent unit tests for the S9 crypto-address-awareness rule."""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s9_crypto_address_scan import CryptoAddressScanRule

MakeContext = Callable[..., StaticAnalysisContext]


def test_fires_on_btc_base58_regex_high_confidence(make_context: MakeContext) -> None:
    ctx = make_context(
        files={"extension.js": "const btc = /[13][a-km-zA-HJ-NP-Z1-9]{25,34}/g;"}
    )
    findings = CryptoAddressScanRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s9.crypto_address_scan"
    assert finding.severity.value == "medium"
    # Base58 char-class is near-unique to crypto -> HIGH confidence.
    assert finding.confidence.value == "high"
    assert "attack.T1565" in finding.categories
    assert "Bitcoin" in finding.description


def test_fires_on_eth_address_regex(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": "const eth = /0x[a-fA-F0-9]{40}/g;"})
    findings = CryptoAddressScanRule().evaluate(ctx)
    assert len(findings) == 1
    # No Base58 fragment -> the broader hex pattern stays MEDIUM confidence.
    assert findings[0].confidence.value == "medium"
    assert "Ethereum" in findings[0].description


def test_fires_on_bech32_regex(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": "const w = /bc1[a-z0-9]{25,90}/;"})
    findings = CryptoAddressScanRule().evaluate(ctx)
    assert len(findings) == 1
    assert "Bech32" in findings[0].description


def test_aggregates_btc_and_eth_into_one_finding(make_context: MakeContext) -> None:
    ctx = make_context(
        files={
            "a.js": "const btc = /[a-km-zA-HJ-NP-Z1-9]{25,34}/;",
            "b.js": "const eth = /0x[a-fA-F0-9]{40}/;",
        }
    )
    findings = CryptoAddressScanRule().evaluate(ctx)
    assert len(findings) == 1
    assert "Bitcoin" in findings[0].description
    assert "Ethereum" in findings[0].description
    assert findings[0].confidence.value == "high"  # Base58 present


def test_silent_for_sha1_hex_regex_without_0x_prefix(make_context: MakeContext) -> None:
    # A 40-char hex regex is SHA-1, NOT an ETH address — must not false-positive.
    ctx = make_context(files={"extension.js": "const sha1 = /[a-f0-9]{40}/;"})
    assert CryptoAddressScanRule().evaluate(ctx) == []


def test_silent_for_clean_source(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": "const id = /[A-Za-z0-9_]{8}/;"})
    assert CryptoAddressScanRule().evaluate(ctx) == []
