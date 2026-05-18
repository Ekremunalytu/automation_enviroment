"""W15-7 architecture gate: every ``apiClient`` method routes through ``/api/*``.

This gate prevents the W15-5 I2 regression class: a bare ``fetch("/health")``
or any other ``apiClient`` method whose path bypasses nginx's ``/api/*``
reverse-proxy block. The W15-5 I2 fix migrated ``getHealth()`` from
``/health`` to ``/api/health`` (new ``appcore/api/health_router.py`` mounted
with ``prefix="/api"``); the W15-5 close-out evidence noted no existing
extendable gate, so the new gate is deferred to W15-7 close-out hygiene.
This file lands that gate.

The invariant: ``ui/src/lib/api/client.ts`` exposes the ``apiClient`` object
whose methods all delegate to ``requestJson<T>(...)`` from
``ui/src/lib/api/http``. The first argument to every ``requestJson(...)``
call site is the URL path. Every path must start with ``/api/`` so the
nginx ``location /api/`` block proxies it to the API container; any path
starting with anything else either bypasses the proxy (production
breakage) or hits a non-existent SPA route (silent failure).

Modeled on the W14-2 / W14-5 AST gate pattern, adapted to TypeScript via
regex scanning (no TypeScript AST parsing available in the Python test
environment; regex over the literal source is the right granularity for
a string-prefix invariant on a small surface).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLIENT_PATH = REPO_ROOT / "ui" / "src" / "lib" / "api" / "client.ts"

REQUIRED_PREFIX = "/api/"

# Match ``requestJson<...>( "..." `` or ``requestJson<...>( `...` `` —
# capturing the leading character of the literal so we can determine
# whether the URL is a plain string, a template literal, or a single-quoted
# string. We capture the first 5 chars of the URL body to validate the
# ``/api/`` prefix without needing to balance closing quotes / interpolations.
_REQUEST_JSON_CALL = re.compile(
    r"""requestJson<[^>]*>\(           # requestJson<T>(
        \s*                             # optional whitespace before the URL arg
        (?P<quote>["`'])                # opening quote / backtick / apostrophe
        (?P<path_head>[^"`'$]{0,5})     # first up-to-5 chars of the URL path
    """,
    re.VERBOSE,
)

# Allowlist for absolute URLs to external services. Currently empty —
# ``apiClient`` does not call any external service. If a future entry
# legitimately needs an external URL (e.g., a third-party telemetry
# endpoint), add it here with a comment justifying the exemption and
# the ADR or runbook that authorises it.
_ABSOLUTE_URL_ALLOWLIST: tuple[str, ...] = ()


def _scan_request_json_calls() -> list[tuple[int, str]]:
    """Return (line_number, path_head) for every ``requestJson(...)`` call.

    Line numbers are 1-based for human-readable failure messages.
    """
    source = CLIENT_PATH.read_text(encoding="utf-8")
    calls: list[tuple[int, str]] = []
    for match in _REQUEST_JSON_CALL.finditer(source):
        line_no = source.count("\n", 0, match.start()) + 1
        calls.append((line_no, match.group("path_head")))
    return calls


def test_api_client_request_json_paths_start_with_api_prefix() -> None:
    """Every ``requestJson<T>(...)`` call in ``apiClient`` must use ``/api/``.

    Drift class: the W15-5 I2 regression — ``getHealth()`` issued a bare
    ``fetch("/health")`` that bypassed nginx's ``/api/*`` proxy block and
    fell through to the SPA fallback in production. This gate walks every
    ``requestJson(...)`` call site and asserts the first five characters
    of the URL path start with ``/api/``.

    Absolute URLs to external services are not currently expected; if one
    is added later, extend ``_ABSOLUTE_URL_ALLOWLIST`` with a comment
    citing the ADR or runbook that authorises the exemption.
    """
    assert CLIENT_PATH.exists(), (
        f"{CLIENT_PATH.relative_to(REPO_ROOT)} not found; if the apiClient "
        f"file moved, update CLIENT_PATH in this gate."
    )

    calls = _scan_request_json_calls()

    assert calls, (
        f"No ``requestJson<T>(...)`` calls found in "
        f"{CLIENT_PATH.relative_to(REPO_ROOT)}. Either the file no longer "
        f"hosts the apiClient surface or the regex stopped matching the "
        f"call shape — update _REQUEST_JSON_CALL."
    )

    violations: list[str] = []
    for line_no, path_head in calls:
        if path_head.startswith(REQUIRED_PREFIX):
            continue
        if any(path_head.startswith(prefix) for prefix in _ABSOLUTE_URL_ALLOWLIST):
            continue
        violations.append(
            f"  line {line_no}: requestJson(...) path starts with "
            f"{path_head!r} (expected to start with {REQUIRED_PREFIX!r})"
        )

    assert not violations, (
        "apiClient methods must route through the ``/api/*`` nginx proxy "
        "block. The W15-5 I2 regression was a bare ``fetch('/health')`` "
        "that bypassed the proxy; the W15-5 fix migrated it to ``/api/"
        "health``. This gate prevents the regression class.\n"
        + "\n".join(violations)
        + "\n\nIf an external absolute URL is genuinely required, extend "
        "_ABSOLUTE_URL_ALLOWLIST with a justifying comment."
    )


def test_api_client_at_least_health_endpoint_present() -> None:
    """Sanity: the W15-5 I2 ``/api/health`` endpoint stays callable.

    Drift class: a future refactor that drops ``getHealth()`` from the
    apiClient (or moves it to a different URL family) silently breaks
    the SystemPage health probe. This gate asserts the canonical
    ``/api/health`` call site stays present at ``ui/src/lib/api/client.ts``;
    a removal would fail and force an explicit decision (UI feature drop
    or alternative wiring) rather than silent loss.
    """
    source = CLIENT_PATH.read_text(encoding="utf-8")
    assert '"/api/health"' in source or "'/api/health'" in source, (
        f"Canonical ``/api/health`` call site missing from "
        f"{CLIENT_PATH.relative_to(REPO_ROOT)}. The W15-5 I2 fix landed "
        f"this route as the proxy-friendly health probe. Removing it "
        f"reintroduces the I2 regression class — add a deprecation ADR "
        f"before deleting the call site."
    )
