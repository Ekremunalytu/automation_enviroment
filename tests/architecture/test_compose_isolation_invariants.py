"""W21-4 container isolation baseline invariants (ADR 0013).

Pins the hardening posture established in
`documents/adrs/0013-container-isolation-baseline.md` so a future
edit cannot silently regress it.

What's pinned:

1. Three runtime services (`executor`, `api`, `ui`) carry
   `cap_drop: [ALL]` so Docker's permissive default keepset is
   removed.
2. The same three services carry `security_opt:
   ["no-new-privileges:true"]` so the residual set-uid privilege
   escalation path is closed.
3. The `executor` service preserves `cap_add: [NET_RAW, SYS_PTRACE]`
   — the harness monitoring tools (tcpdump/tshark/strace) need both
   capabilities; dropping them would silently kill malware
   observability without the test catching it.
4. The ADR 0013 file itself exists at the expected path so a future
   edit that removes the ADR (or moves it) trips this gate.

What's intentionally NOT pinned (deferred per ADR 0013 §Deferred):

- `read_only: true` — write-surface restructuring required first.
- Custom `docker/seccomp.json` profile — Docker default seccomp is
  active until a ratchet-down audit lands.
- `postgres` / `postgres_test` cap state — image needs CAP_CHOWN
  for the data-directory bootstrap; W22+ scope.
- `executor-cdp` (debug profile) — opt-in, not part of the default
  attack surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = REPO_ROOT / "docker-compose.yml"
ADR_PATH = REPO_ROOT / "documents" / "adrs" / "0013-container-isolation-baseline.md"


def _load_compose() -> dict[str, Any]:
    raw = COMPOSE_PATH.read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict), "docker-compose.yml must parse as a mapping"
    services = parsed.get("services")
    assert isinstance(services, dict), (
        "docker-compose.yml must declare a `services:` mapping"
    )
    return services


_HARDENED_SERVICES = ("executor", "api", "ui")


@pytest.mark.parametrize("service_name", _HARDENED_SERVICES)
def test_runtime_service_drops_all_capabilities(service_name: str) -> None:
    """ADR 0013: each runtime service must drop the Docker-default
    capability keepset via `cap_drop: [ALL]`.

    Dropping `ALL` removes CAP_CHOWN, CAP_DAC_OVERRIDE, CAP_FOWNER,
    CAP_FSETID, CAP_KILL, CAP_MKNOD, CAP_NET_BIND_SERVICE,
    CAP_NET_RAW, CAP_SETFCAP, CAP_SETGID, CAP_SETPCAP, CAP_SETUID,
    CAP_SYS_CHROOT, CAP_AUDIT_WRITE. A future edit that re-adds the
    keepset (or replaces ALL with a partial drop list) must update
    this test alongside ADR 0013.
    """
    services = _load_compose()
    assert service_name in services, (
        f"service `{service_name}` must exist in docker-compose.yml"
    )
    cap_drop = services[service_name].get("cap_drop")
    assert cap_drop == ["ALL"], (
        f"ADR 0013 requires `cap_drop: [ALL]` on the `{service_name}` "
        f"service. Got: {cap_drop!r}. If you intentionally restored the "
        f"Docker keepset, update ADR 0013 + this test together."
    )


@pytest.mark.parametrize("service_name", _HARDENED_SERVICES)
def test_runtime_service_refuses_new_privileges(service_name: str) -> None:
    """ADR 0013: each runtime service must carry
    `security_opt: ["no-new-privileges:true"]` so set-uid binaries
    inside the image cannot grant new caps at exec time.
    """
    services = _load_compose()
    security_opt = services[service_name].get("security_opt") or []
    assert "no-new-privileges:true" in security_opt, (
        f'ADR 0013 requires `security_opt: ["no-new-privileges:true"]` '
        f"on the `{service_name}` service. Got: {security_opt!r}."
    )


def test_executor_keeps_audited_capabilities() -> None:
    """ADR 0013: the `executor` service drops ALL caps but explicitly
    re-adds NET_RAW + SYS_PTRACE because the harness monitoring tools
    (tcpdump/tshark/strace per executor/container/Dockerfile L30-L33)
    need them. Removing either would silently break malware
    observability without surfacing as a test failure elsewhere —
    pin both here.
    """
    services = _load_compose()
    cap_add = services["executor"].get("cap_add") or []
    assert "NET_RAW" in cap_add, (
        "executor must keep CAP_NET_RAW (tcpdump/tshark — "
        "executor/container/Dockerfile L30-L31). ADR 0013 §Decision."
    )
    assert "SYS_PTRACE" in cap_add, (
        "executor must keep CAP_SYS_PTRACE (strace — "
        "executor/container/Dockerfile L33). ADR 0013 §Decision."
    )
    # Surface a regression if anything else creeps in — those would
    # need their own ADR justification.
    extra = sorted(set(cap_add) - {"NET_RAW", "SYS_PTRACE"})
    assert not extra, (
        f"executor cap_add must contain exactly NET_RAW + SYS_PTRACE. "
        f"Extra capabilities found: {extra}. Audit + update ADR 0013."
    )


def test_postgres_services_remain_unhardened_until_w22() -> None:
    """ADR 0013 §Decision: postgres + postgres_test keep their default
    cap keepset because the postgres image's first-run schema setup
    needs CAP_CHOWN to chown the data dir. Pin the deferral so an
    accidental cap_drop:[ALL] on either service surfaces here, and
    the operator either updates ADR 0013 (because the upstream image
    finally works without CAP_CHOWN) or reverts.
    """
    services = _load_compose()
    for name in ("postgres", "postgres_test"):
        cap_drop = services[name].get("cap_drop")
        assert cap_drop is None, (
            f"`{name}` cap_drop must remain unset (deferred to W22 per "
            f"ADR 0013 §Deferred). Got: {cap_drop!r}. If the upstream "
            f"image no longer needs CAP_CHOWN, update ADR 0013 first."
        )


def test_adr_0013_exists() -> None:
    """ADR 0013 file must remain at the expected path so the
    compose-level invariants above have a documented source-of-truth.
    """
    assert ADR_PATH.exists(), (
        f"ADR 0013 not found at {ADR_PATH.relative_to(REPO_ROOT)}. "
        "The compose-level cap_drop / security_opt invariants in this "
        "module reference this ADR — restore it before re-running."
    )


def test_adr_0013_documents_deferred_items() -> None:
    """ADR 0013 must explicitly carry the deferred-to-W22 items
    (`read_only`, custom seccomp profile, tmpfs mounts) so a future
    ratchet-down iter inherits the audit trail without re-litigating
    why those items are not in the baseline.
    """
    text = ADR_PATH.read_text(encoding="utf-8")
    for token in (
        "read_only",
        "tmpfs",
        "seccomp",
        "W22",
    ):
        assert token in text, (
            f"ADR 0013 must mention {token!r} in its Deferred / next-steps "
            "section so the ratchet-down lane has the carry-over signal."
        )
