"""Regression guard for the stylesheet content-scanner coverage fix.

The `nextsecurity` / vsix-zoo corpus ships its entire CSS/LESS TTP set as
stylesheet files. Before the fix, ``.less`` / ``.scss`` / ``.sass`` were absent
from ``_common.TEXT_SUFFIXES``, so ``is_text_document`` skipped them and the
content-scanning rules (s4 domains, s5 endpoints, s7 secrets, s8 webhooks,
s9 crypto, s12 invisible-unicode) — *and* the stylesheet-borne s19 family, which
filters ``iter_text_documents`` — never saw a single byte of a stylesheet.

The s19 unit tests use ``.less`` fixtures and so transitively pin ``.less``, but
nothing pins ``.scss`` / ``.sass`` and nothing pins that a *content* scanner
(not s19) actually reaches a stylesheet. This file closes that gap: drop any
stylesheet suffix from ``TEXT_SUFFIXES`` and one of these assertions goes red.

See ``documents/detection-design/nextsecurity-stylesheet-spec.md``.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules._common import TEXT_SUFFIXES, is_text_document
from static_runtime.rules.s8_exfil_webhook import ExfiltrationWebhookRule
from static_runtime.rules.s9_crypto_address_scan import CryptoAddressScanRule

MakeContext = Callable[..., StaticAnalysisContext]

# Suffixes the coverage fix added (``.css`` was always present).
_STYLESHEET_SUFFIXES = (".css", ".less", ".scss", ".sass")
_NEW_STYLESHEET_SUFFIXES = (".less", ".scss", ".sass")

# Synthetic Discord webhook literal (token shape preserved, value fabricated) —
# the same exfil-channel shape the s8 unit test fires on, embedded here in a
# CSS ``::after`` content beacon so it lives inside a stylesheet, not JS.
_WEBHOOK = (
    "https://discord.com/api/webhooks/1332511931541491802/"
    "5Hnr5TXbOi_O9REwjkk4MPLBaImsrsfkZPkJ115lAQD35e2hHNtR_h0M62VLACH-qEZ2"
)


@pytest.mark.parametrize("suffix", _STYLESHEET_SUFFIXES)
def test_is_text_document_recognizes_stylesheet_suffixes(suffix: str) -> None:
    assert suffix in TEXT_SUFFIXES
    assert is_text_document(f"styles/theme{suffix}")
    # Case-insensitive, mirroring is_text_document's ``.lower()``.
    assert is_text_document(f"styles/theme{suffix.upper()}")


@pytest.mark.parametrize("suffix", _NEW_STYLESHEET_SUFFIXES)
def test_webhook_scanner_reaches_each_stylesheet_suffix(
    make_context: MakeContext, suffix: str
) -> None:
    """s8 must fire on an exfil webhook hidden inside a stylesheet file.

    This is the data-plane half of the fix: a CSS-native exfil beacon
    (``::after { content: url(<webhook>) }``) is a stylesheet, not JS, and
    must still be scanned for the webhook ingestion endpoint.
    """
    ctx = make_context(
        files={f"theme{suffix}": f'body::after {{ content: url("{_WEBHOOK}"); }}'}
    )
    findings = ExfiltrationWebhookRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.s8.exfil_webhook"
    assert "Discord" in findings[0].description


def test_second_content_scanner_also_reaches_a_stylesheet(
    make_context: MakeContext,
) -> None:
    """A different content rule (s9 crypto) also sees stylesheet bytes.

    Guards against a half-fix where only one scanner's suffix list grew.
    """
    ctx = make_context(files={"vars.scss": "$eth: /0x[a-fA-F0-9]{40}/;"})
    findings = CryptoAddressScanRule().evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "extrace.s9.crypto_address_scan"


def test_unrelated_suffix_stays_unscanned(make_context: MakeContext) -> None:
    """Control: a non-text binary-ish suffix is still skipped, so the assertions
    above are about the suffix list, not about scanning literally everything."""
    assert ".woff" not in TEXT_SUFFIXES
    ctx = make_context(files={"font.woff": f'url("{_WEBHOOK}")'})
    assert ExfiltrationWebhookRule().evaluate(ctx) == []
