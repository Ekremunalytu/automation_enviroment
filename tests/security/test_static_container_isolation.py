"""ES-2 security: hardened static-analyzer container isolation.

ADR 0016 §Decision 2 + ADR 0013. Pins the static-specific envelope of the
``static_analyzer`` compose service that the shared parametrized invariants in
``tests/architecture/test_compose_isolation_invariants.py`` (``cap_drop: [ALL]``
+ ``no-new-privileges``, applied to every hardened service) do NOT cover:

- ``network_mode: none`` — the analyzer parses untrusted VSIX content and must
  never have egress.
- no ``cap_add`` — it starts as the non-root ``static`` user, so unlike api/ui
  it needs no SETUID/SETGID for a runtime privilege drop.
- ``mem_limit`` 1g / ``cpus`` 1.0 resource bounds.
- extensions input mounted read-only; results mounted read-write.
- no Docker socket; no published host ports.

Enrolled into the explicit ``make test-security`` file list (no auto-discovery).
No marker — also runs in the default lane / ``make check-all`` (compose-parse
only, no live container).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = REPO_ROOT / "docker-compose.yml"
_SERVICE = "static_analyzer"


def _service() -> dict[str, Any]:
    parsed = yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8"))
    services = parsed["services"]
    assert _SERVICE in services, (
        f"`{_SERVICE}` service missing from docker-compose.yml (ES-2, ADR 0016)."
    )
    return services[_SERVICE]


def test_static_analyzer_has_no_network() -> None:
    """ADR 0016 §Decision 2: the analyzer never needs egress -> network_mode none."""
    assert _service().get("network_mode") == "none", (
        "static_analyzer must run with `network_mode: none` — it parses "
        "untrusted VSIX content and must have no network access."
    )


def test_static_analyzer_drops_all_caps_and_adds_none() -> None:
    """``cap_drop: [ALL]`` and NO ``cap_add`` (non-root start, no privilege drop)."""
    svc = _service()
    assert svc.get("cap_drop") == ["ALL"], (
        f"static_analyzer must drop all caps. Got: {svc.get('cap_drop')!r}."
    )
    assert not svc.get("cap_add"), (
        "static_analyzer must not re-add any capability: it starts as the "
        "non-root `static` user and performs no runtime privilege drop "
        f"(unlike api/ui). Got cap_add={svc.get('cap_add')!r}."
    )


def test_static_analyzer_refuses_new_privileges() -> None:
    """ADR 0013: set-uid binaries cannot grant new caps at exec time."""
    security_opt = _service().get("security_opt") or []
    assert "no-new-privileges:true" in security_opt, (
        f"static_analyzer must carry no-new-privileges. Got: {security_opt!r}."
    )


def test_static_analyzer_pins_resource_limits() -> None:
    """``mem_limit`` defaults to 1g and ``cpus`` to 1.0 (ADR 0016 §Decision 2).

    ``yaml.safe_load`` does not expand docker-compose ``${VAR:-default}``
    substitution, so the parsed value is the literal expression — assert the
    1g / 1.0 default rides inside it.
    """
    svc = _service()
    assert "1g" in str(svc.get("mem_limit", "")), (
        f"static_analyzer mem_limit must default to 1g. Got: {svc.get('mem_limit')!r}."
    )
    assert "1.0" in str(svc.get("cpus", "")), (
        f"static_analyzer cpus must default to 1.0. Got: {svc.get('cpus')!r}."
    )


def test_static_analyzer_mounts_input_ro_and_results_rw() -> None:
    """Extensions input is read-only; the results dir is writable."""
    volumes = [str(v) for v in (_service().get("volumes") or [])]
    ro_input = [v for v in volumes if "/extensions-input" in v and v.endswith(":ro")]
    assert ro_input, (
        "static_analyzer must mount the extensions input read-only (:ro). "
        f"Got volumes: {volumes!r}."
    )
    results = [v for v in volumes if "/results" in v]
    assert results, f"static_analyzer must mount the results dir. Got: {volumes!r}."
    assert all(not v.endswith(":ro") for v in results), (
        f"static_analyzer results mount must be writable (rw). Got: {results!r}."
    )


def test_static_analyzer_has_no_docker_socket() -> None:
    """The analyzer must never reach the Docker socket."""
    volumes = [str(v) for v in (_service().get("volumes") or [])]
    assert all("docker.sock" not in v for v in volumes), (
        f"static_analyzer must NOT mount the Docker socket. Got: {volumes!r}."
    )


def test_static_analyzer_publishes_no_ports() -> None:
    """No host ports (it has no network)."""
    assert not _service().get("ports"), (
        f"static_analyzer must not publish host ports. Got: {_service().get('ports')!r}."
    )
