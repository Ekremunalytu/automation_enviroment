"""W8-7 architecture regression: enforce ADR 0007 loopback defaults.

Three independent surfaces are pinned here:

1. Pydantic settings — `APISettings.HOST` and the CORS defaults must
   resolve to loopback / explicit allow-list when `EXTRACE_ALLOW_LAN` is
   unset.
2. `EXTRACE_ALLOW_LAN` opt-in — truthy values restore the wildcard
   binding (`0.0.0.0` + `*`); falsy / unset values keep loopback.
3. `docker-compose.yml` — every default-profile `ports:` mapping must
   begin with `127.0.0.1:`; the CDP port (9222) lives behind the
   non-default `debug` profile via the `executor-cdp` sidecar.

The test fails if a future change re-introduces a `0.0.0.0` default,
publishes a wildcard CORS origin, drops a host-IP prefix from compose,
or surfaces CDP on the default profile.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parents[2]
COMPOSE_PATH = REPO_ROOT / "docker-compose.yml"

_ENV_PREFIXES_TO_SCRUB = ("API_", "EXTRACE_", "POSTGRES_")


@pytest.fixture(autouse=True)
def _scrub_extrace_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip env vars that would otherwise override the in-test defaults."""
    for key in [k for k in os.environ if k.startswith(_ENV_PREFIXES_TO_SCRUB)]:
        monkeypatch.delenv(key, raising=False)


def _fresh_api_settings():
    """Build a fresh APISettings instance without consulting the on-disk
    `.env` file — the operator's local `.env` may carry overrides that
    would mask the regression we are pinning."""
    from appcore.api import config as cfg

    return cfg.APISettings(_env_file=None)


def test_api_host_default_is_loopback() -> None:
    settings = _fresh_api_settings()
    assert settings.HOST == "127.0.0.1"


def test_cors_origins_default_is_not_wildcard() -> None:
    settings = _fresh_api_settings()
    assert settings.cors_allow_origins == ["http://localhost:3000"]
    assert "*" not in settings.cors_allow_origins


def test_cors_credentials_default_is_false() -> None:
    settings = _fresh_api_settings()
    assert settings.CORS_ALLOW_CREDENTIALS is False


@pytest.mark.parametrize("truthy", ["1", "true", "yes", "ON"])
def test_extrace_allow_lan_truthy_restores_wildcard(
    truthy: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EXTRACE_ALLOW_LAN", truthy)
    settings = _fresh_api_settings()
    assert settings.HOST == "0.0.0.0"
    assert settings.cors_allow_origins == ["*"]


@pytest.mark.parametrize("falsy", ["0", "false", "no", "off", ""])
def test_extrace_allow_lan_falsy_keeps_loopback(
    falsy: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EXTRACE_ALLOW_LAN", falsy)
    settings = _fresh_api_settings()
    assert settings.HOST == "127.0.0.1"
    assert settings.cors_allow_origins == ["http://localhost:3000"]


def _compose_services() -> dict:
    return yaml.safe_load(COMPOSE_PATH.read_text()).get("services", {}) or {}


def test_compose_default_profile_ports_are_loopback() -> None:
    """Every default-profile service `ports:` entry must carry the
    explicit `127.0.0.1:` prefix. A service that opts into a non-empty
    `profiles:` list is exempt — it is only started when the operator
    requests that profile (e.g. `docker compose --profile debug up`)."""
    violations: list[str] = []
    for svc_name, svc in _compose_services().items():
        if svc.get("profiles"):  # opt-in profile, exempt from default gate
            continue
        for port in svc.get("ports") or []:
            spec = port if isinstance(port, str) else str(port)
            if not spec.startswith("127.0.0.1:"):
                violations.append(f"{svc_name}: {spec}")
    assert not violations, (
        "compose default-profile services must bind loopback:\n" + "\n".join(violations)
    )


def test_compose_cdp_port_is_debug_gated() -> None:
    """Port 9222 must only appear under a non-default profile. ADR 0007 §4
    routes CDP through the `executor-cdp` sidecar that activates with the
    `debug` profile."""
    cdp_in_default: list[str] = []
    cdp_in_debug = False
    for svc_name, svc in _compose_services().items():
        profiles = svc.get("profiles") or []
        for port in svc.get("ports") or []:
            spec = port if isinstance(port, str) else str(port)
            if "9222" not in spec:
                continue
            if not profiles:
                cdp_in_default.append(f"{svc_name}: {spec}")
            elif "debug" in profiles:
                cdp_in_debug = True
    assert not cdp_in_default, (
        "CDP port 9222 must not be exposed in the default profile:\n"
        + "\n".join(cdp_in_default)
    )
    assert cdp_in_debug, (
        "CDP port 9222 must remain reachable under the `debug` profile "
        "(executor-cdp socat sidecar)."
    )


def test_explicit_host_override_wins_over_lan_substitution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ADR 0007: explicit env overrides win — `model_post_init` only swaps
    in `0.0.0.0` when `HOST` still holds the loopback default. An operator
    who pins a specific bind address must keep it even with the LAN flag on."""
    monkeypatch.setenv("EXTRACE_ALLOW_LAN", "1")
    monkeypatch.setenv("API_HOST", "192.168.1.10")
    settings = _fresh_api_settings()
    assert settings.HOST == "192.168.1.10"


def test_explicit_cors_origins_override_wins_over_lan_substitution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit `API_CORS_ALLOW_ORIGINS` allow-list survives the LAN-mode
    wildcard substitution. The runbook §Pre-Flight item 3 mandates an
    explicit list; this test pins that the substitution does not silently
    overwrite it."""
    monkeypatch.setenv("EXTRACE_ALLOW_LAN", "1")
    monkeypatch.setenv(
        "API_CORS_ALLOW_ORIGINS",
        "https://extrace.lab.local,https://analyst.lab.local",
    )
    settings = _fresh_api_settings()
    assert settings.cors_allow_origins == [
        "https://extrace.lab.local",
        "https://analyst.lab.local",
    ]
    assert "*" not in settings.cors_allow_origins


def test_cors_methods_default_is_explicit_allow_list() -> None:
    settings = _fresh_api_settings()
    assert settings.cors_allow_methods == [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
        "OPTIONS",
    ]
    assert "*" not in settings.cors_allow_methods


def test_cors_headers_default_is_explicit_allow_list() -> None:
    settings = _fresh_api_settings()
    assert settings.cors_allow_headers == ["Content-Type", "Authorization"]
    assert "*" not in settings.cors_allow_headers


def test_cors_credentials_remains_false_under_lan_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Even when `EXTRACE_ALLOW_LAN=1` widens origins to `*`, credentials
    must stay False — the browser CORS spec rejects `*` paired with
    credentials=true (runbook §Pre-Flight item 3)."""
    monkeypatch.setenv("EXTRACE_ALLOW_LAN", "1")
    settings = _fresh_api_settings()
    assert settings.cors_allow_origins == ["*"]
    assert settings.CORS_ALLOW_CREDENTIALS is False


@pytest.mark.parametrize("padded", [" 1 ", "TRUE\n", "  yes", "On\t"])
def test_extrace_allow_lan_strips_and_lowercases(
    padded: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_allow_lan()` applies `.strip().lower()` before the truthy
    comparison; whitespace and case must not gate the opt-in."""
    monkeypatch.setenv("EXTRACE_ALLOW_LAN", padded)
    settings = _fresh_api_settings()
    assert settings.HOST == "0.0.0.0"
