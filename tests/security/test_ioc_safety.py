"""Safety guards: blocklisted malicious IOC hosts can never reach the dev host.

The ``blacklist_domains`` denylist must contain REAL malicious hosts (un-defanged)
to work as exact match targets for ``s4``/``a7`` — but those strings must never be
*contacted*. Three independent properties keep the developer environment safe, and
this module pins each so a future edit cannot silently regress them:

1. **The denylist loader is inert.** ``domain_indicators`` only reads the file and
   string-matches it; it imports no network module and never resolves (DNS) or
   fetches (HTTP) a host. Listing a real C2 here cannot make anything reach it.
2. **The only live-request tool skips every real IOC.** ``markdown-link-check``
   (the lone toolchain step that issues HTTP requests, over Markdown docs) is
   configured via ``.mlc_config.json`` ``ignorePatterns`` to ignore every real IOC
   host, so it can never fetch one even if a URL form appeared.
3. **No doc carries a live malicious URL.** IOCs in docs are defanged (``hxxp`` /
   ``[.]``) and fenced, reference-only — so no tracked Markdown file contains a
   real IOC host in a live ``scheme://`` URL the link checker could resolve.

When a new real IOC host joins ``blacklist_domains.txt``, add its fragment to
``REAL_IOC_HOSTS`` below and a matching ``.mlc_config.json`` ignorePattern; these
tests then enforce the rest.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

# Real, observed malicious C2 / relay host fragments that appear (un-defanged) in
# the shipped denylist (kagema/snowshono + related BYOSC campaigns). Each MUST be
# skipped by markdown-link-check and MUST NOT appear as a live URL in any doc.
REAL_IOC_HOSTS = (
    "niggboo",
    "year000001",
    "undefined21",
    "bulletmailer",
    "dof-connect",
    "144.172.103.247",
)

# Network-capable imports/calls that must never appear in the denylist loader.
_NETWORK_TOKENS = (
    "import socket",
    "socket.socket",
    "urllib",
    "requests",
    "httpx",
    "aiohttp",
    "http.client",
    "getaddrinfo",
    "urlopen",
)


def _mlc_ignore_patterns() -> list[str]:
    cfg = json.loads((_REPO / ".mlc_config.json").read_text(encoding="utf-8"))
    return [entry["pattern"] for entry in cfg.get("ignorePatterns", [])]


def test_denylist_loader_is_network_free() -> None:
    """The loader must stay pure file-read + string-match — never resolve/fetch."""
    src = (_REPO / "packages/analysis_contracts/domain_indicators.py").read_text(
        encoding="utf-8"
    )
    offenders = [token for token in _NETWORK_TOKENS if token in src]
    assert not offenders, (
        "the blacklist_domains loader must never gain a network capability "
        f"(found {offenders}); a denylisted host is data, never a fetch target"
    )


def test_every_real_ioc_is_ignored_by_link_checker() -> None:
    """markdown-link-check (the only live-request tool) must skip every real IOC."""
    patterns = _mlc_ignore_patterns()
    for host in REAL_IOC_HOSTS:
        assert any(host in pattern for pattern in patterns), (
            f"{host!r} is a real IOC on the denylist but has no markdown-link-check "
            "ignorePattern in .mlc_config.json — the link checker could try to "
            "fetch it. Add a {'pattern': '<host>'} entry."
        )


def test_no_live_ioc_url_in_tracked_markdown() -> None:
    """No Markdown doc may carry a real IOC host in a live scheme:// URL."""
    url_re = re.compile(
        r"https?://[^\s)\"'<>`]*(?:"
        + "|".join(re.escape(h) for h in REAL_IOC_HOSTS)
        + ")",
        re.IGNORECASE,
    )
    offenders: list[str] = []
    for md in (_REPO / "documents").rglob("*.md"):
        if url_re.search(md.read_text(encoding="utf-8", errors="ignore")):
            offenders.append(str(md.relative_to(_REPO)))
    assert not offenders, (
        "defang discipline broken — a live malicious IOC URL appears in: "
        f"{offenders}. IOCs in docs must be defanged (hxxp / [.]) and reference-only."
    )
