"""Framework-agnostic blacklist host/domain indicators (blacklist_domains feature).

Pure-stdlib helpers shared by two call sites that must NOT share a heavier
dependency, mirroring ``typosquat_match.py``:

* the dynamic detection rule
  ``packages.analysis_engine.rules.a7_blacklisted_domain`` (host-side, full
  engine), which checks each observed outbound network ``event.host``; and
* the in-house static rule ``static_runtime.rules.s4_blacklisted_domain`` (runs
  inside the hardened ``automation_static_analyzer`` image, which copies only
  ``packages/analysis_contracts/`` + ``static_runtime/`` and deliberately NOT
  ``packages/analysis_engine/``).

The effective denylist is the shipped seed file
(``data/blacklist_domains.txt``) UNION an optional in-process *operator override*.
The override is the editable ``blacklist_domains`` field: the host/dynamic process
(``automation_api``) loads the operator's DB rows at startup and on every edit and
calls ``set_operator_blacklist`` — so the dynamic ``a7`` rule sees edits live. The
hardened static container NEVER calls the setter, so the override stays empty
there and the static ``s4`` rule keeps its seed-only, DB-free behaviour. Imports
are confined to the standard library so importing this leaf never drags the
dynamic engine into the hardened static image.

Matching is host-suffix aware (``c2.evil.example`` matches ``evil.example``) but
registrable-boundary safe (``notevil.example`` / ``evil.example.org`` do NOT
match ``evil.example``). Exact IP host literals are also allowed for known
direct-IP C2/stagers. These semantics mirror the allowlist's
``packages.analysis_engine.rules._common.is_benign_domain``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

# The curated seed denylist lives here (not under packages/analysis_engine/) so
# the hardened static image can read it; the dynamic engine reads the same file
# via this module (one curated copy, mirroring popular_extensions.txt).
_BLACKLIST_DOMAIN_PATH = (
    Path(__file__).resolve().parent / "data" / "blacklist_domains.txt"
)

# Adversarial-input bound (parity with the static context's ES-4 caps): clamp the
# per-document text the source scanner inspects so a multi-MB minified bundle
# cannot drive the alternation regex over an unbounded string.
_MAX_SCAN_CHARS = 512 * 1024

# A DNS label is [a-z0-9-]; we also admit '_'. The lookarounds reject a hit that
# is part of a larger label (``notevil.example``) or a longer registrable domain
# (``evil.example.org``); the optional ``(?:<label>+\.)*`` prefix admits arbitrary
# subdomains.
_LABEL = r"[a-z0-9_-]"

# In-process operator additions (the editable list). EMPTY inside the hardened
# static-analyzer container — it never calls ``set_operator_blacklist`` — so the
# static rule stays seed-only and DB-free. Replaced atomically (assign a new
# frozenset) so a concurrent reader never sees a half-built set.
_operator_domains: frozenset[str] = frozenset()


def _normalize(domain: str) -> str:
    return domain.strip().lower().rstrip(".")


@lru_cache(maxsize=1)
def _seed_domains() -> frozenset[str]:
    """The shipped baseline denylist from the curated file (cached)."""
    try:
        lines = _BLACKLIST_DOMAIN_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return frozenset()
    return frozenset(
        _normalize(line)
        for line in lines
        if (stripped := line.strip()) and not stripped.startswith("#")
    )


def seed_domains() -> frozenset[str]:
    """The shipped baseline denylist (read-only file). Not operator-editable."""
    return _seed_domains()


def operator_domains() -> frozenset[str]:
    """The in-process operator additions (empty in the static container)."""
    return _operator_domains


def set_operator_blacklist(domains: Iterable[str]) -> None:
    """Replace the in-process operator additions (host/dynamic side only).

    Called by the API process at startup and on every edit so the dynamic ``a7``
    rule's matcher reflects the operator's DB-backed list live. A no-op for the
    static container, which never calls it.
    """
    global _operator_domains
    _operator_domains = frozenset(
        normalized for domain in domains if (normalized := _normalize(domain))
    )


def clear_operator_blacklist() -> None:
    """Drop all in-process operator additions (back to seed-only)."""
    global _operator_domains
    _operator_domains = frozenset()


def blacklisted_domains() -> frozenset[str]:
    """Effective denylist = shipped seed UNION the operator additions."""
    return _seed_domains() | _operator_domains


@lru_cache(maxsize=8)
def _compile_pattern(domains: frozenset[str]) -> re.Pattern[str] | None:
    """Compile a single anchored alternation over ``domains`` (cached per set)."""
    if not domains:
        return None
    # Longest domain first so the alternation prefers the most specific match.
    alternation = "|".join(
        re.escape(domain) for domain in sorted(domains, key=len, reverse=True)
    )
    return re.compile(
        rf"(?<![a-z0-9_.-])(?:{_LABEL}+\.)*({alternation})(?![a-z0-9_.-])"
    )


def match_host(host: str) -> str | None:
    """Return the blacklisted domain ``host`` belongs to, or ``None``.

    Exact match or subdomain (``host`` ends with ``.<domain>``). Used by the
    dynamic rule over observed ``event.host`` values; sees operator edits live.
    """
    normalized = _normalize(host)
    if not normalized:
        return None
    for domain in blacklisted_domains():
        if normalized == domain or normalized.endswith(f".{domain}"):
            return domain
    return None


def find_in_text(text: str) -> list[str]:
    """Return the sorted unique blacklisted domains referenced in ``text``.

    For the static source/manifest scanner: finds any host token (with optional
    subdomain prefix) whose registrable domain is on the effective denylist. The
    input is clamped and lowercased before the bounded alternation regex runs.
    """
    pattern = _compile_pattern(blacklisted_domains())
    if pattern is None or not text:
        return []
    clamped = text[:_MAX_SCAN_CHARS].lower()
    return sorted({match.group(1) for match in pattern.finditer(clamped)})


__all__ = [
    "blacklisted_domains",
    "clear_operator_blacklist",
    "find_in_text",
    "match_host",
    "operator_domains",
    "seed_domains",
    "set_operator_blacklist",
]
