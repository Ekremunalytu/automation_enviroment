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
3. The `executor` service preserves `cap_add: [NET_RAW, SYS_PTRACE,
   SETUID, SETGID, SETPCAP]` — NET_RAW/SYS_PTRACE for the harness
   monitoring tools (tcpdump/tshark/strace), SETUID/SETGID/SETPCAP for
   the monitor_entrypoint.sh setpriv ambient-cap drop; dropping any
   silently kills malware observability (or, for the setpriv trio,
   network capture) without the test catching it. ADR 0013 §Decision.
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

import re
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
    re-adds a small audited set:

    - NET_RAW + SYS_PTRACE — the harness monitoring tools (tcpdump/
      tshark/strace per executor/container/Dockerfile L30-L33) need them.
    - SETUID + SETGID + SETPCAP — used ONCE at the start of the analyze
      monitor exec by monitor_entrypoint.sh (setpriv) to raise NET_RAW
      into the *ambient* set and drop root -> executor. Required because
      no-new-privileges:true nullifies dumpcap's cap_net_raw file
      capability; the ambient cap is the only way tshark gets NET_RAW
      effective while the workload still runs unprivileged.

    Removing any of these would silently break malware observability (or,
    for the setpriv trio, network capture specifically) without surfacing
    elsewhere — pin the exact set here. ADR 0013 §Network capture under
    no-new-privileges.
    """
    services = _load_compose()
    cap_add = services["executor"].get("cap_add") or []
    required = {"NET_RAW", "SYS_PTRACE", "SETUID", "SETGID", "SETPCAP"}
    missing = sorted(required - set(cap_add))
    assert not missing, (
        f"executor cap_add must contain {sorted(required)}. Missing: "
        f"{missing}. NET_RAW/SYS_PTRACE = monitoring; SETUID/SETGID/SETPCAP "
        f"= monitor_entrypoint.sh ambient-cap drop. ADR 0013 §Decision."
    )
    # Surface a regression if anything else creeps in — those would
    # need their own ADR justification.
    extra = sorted(set(cap_add) - required)
    assert not extra, (
        f"executor cap_add must contain exactly {sorted(required)}. "
        f"Extra capabilities found: {extra}. Audit + update ADR 0013."
    )


def test_api_keeps_setuid_setgid_for_user_drop() -> None:
    """ADR 0013 §SETUID + SETGID retention: `api` uses a gosu-style
    entrypoint that drops from root to `appuser` at startup. That
    privilege drop requires CAP_SETUID + CAP_SETGID; with
    cap_drop:[ALL] both are removed and the entrypoint errors with
    `failed switching to "appuser": operation not permitted`. Pin
    the retention so a future edit that removes either cap surfaces
    before the live-run smoke hits the bug.
    """
    services = _load_compose()
    cap_add = set(services["api"].get("cap_add") or [])
    assert {"SETUID", "SETGID"}.issubset(cap_add), (
        f"`api` must keep CAP_SETUID + CAP_SETGID for the entrypoint's "
        f"runtime user drop. Got cap_add={sorted(cap_add)}. "
        f"ADR 0013 §SETUID + SETGID retention."
    )
    extra = sorted(cap_add - {"SETUID", "SETGID"})
    assert not extra, (
        f"`api` cap_add must contain exactly SETUID + SETGID. Extra "
        f"capabilities found: {extra}. Audit + update ADR 0013."
    )


def test_ui_keeps_nginx_required_capabilities() -> None:
    """ADR 0013 §UI nginx caps: the official nginx Docker image's
    entrypoint chowns `/var/cache/nginx/client_temp` to UID 101
    (nginx user) and forks workers as that user. The chown + user
    drop need CAP_CHOWN + CAP_DAC_OVERRIDE + CAP_SETUID + CAP_SETGID
    even though the listening socket (port 3000) is non-privileged.
    Surfaced during W21-4 primary live-run smoke.
    """
    services = _load_compose()
    cap_add = set(services["ui"].get("cap_add") or [])
    required = {"SETUID", "SETGID", "CHOWN", "DAC_OVERRIDE"}
    missing = required - cap_add
    assert not missing, (
        f"`ui` must keep {sorted(required)} for the nginx "
        f"entrypoint. Missing: {sorted(missing)}. ADR 0013 §UI nginx caps."
    )
    extra = sorted(cap_add - required)
    assert not extra, (
        f"`ui` cap_add must contain exactly {sorted(required)}. Extra "
        f"capabilities found: {extra}. Audit + update ADR 0013."
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


def _adr_executor_cap_add(adr_text: str) -> set[str]:
    """Extract the executor `cap_add` (kept) set from ADR 0013's Decision
    table — the bracketed cap list in the `automation_executor` row that
    names the retained caps (not the `[ALL]` cap_drop cell).
    """
    rows = [
        line
        for line in adr_text.splitlines()
        if "`automation_executor`" in line and "|" in line
    ]
    assert len(rows) == 1, (
        "expected exactly one `automation_executor` Decision-table row in "
        f"ADR 0013, found {len(rows)}."
    )
    bracketed = re.findall(r"\[([^\]]*)\]", rows[0])
    cap_cells = [cell for cell in bracketed if "NET_RAW" in cell]
    assert len(cap_cells) == 1, (
        f"could not isolate the executor cap_add cell in ADR 0013 row: {rows[0]!r}."
    )
    return {
        token.strip().strip("`") for token in cap_cells[0].split(",") if token.strip()
    }


def test_adr_0013_executor_caps_match_compose() -> None:
    """The ADR 0013 Decision-table executor cap_add set must equal the live
    docker-compose.yml executor cap_add AND the audited set pinned by
    `test_executor_keeps_audited_capabilities`. Ties the prose table to
    reality so an ADR edit that diverges from compose (or vice-versa)
    surfaces in CI rather than as silent doc drift.
    """
    required = {"NET_RAW", "SYS_PTRACE", "SETUID", "SETGID", "SETPCAP"}
    adr_caps = _adr_executor_cap_add(ADR_PATH.read_text(encoding="utf-8"))
    assert adr_caps == required, (
        f"ADR 0013 Decision-table executor cap_add {sorted(adr_caps)} must "
        f"equal the audited set {sorted(required)}."
    )
    compose_caps = set(_load_compose()["executor"].get("cap_add") or [])
    assert adr_caps == compose_caps, (
        f"ADR 0013 Decision-table executor cap_add {sorted(adr_caps)} must "
        f"match docker-compose.yml executor cap_add {sorted(compose_caps)}."
    )


def test_adr_0013_rationale_does_not_underclaim_executor_caps() -> None:
    """ADR 0013 §Rationale must not describe the executor keepset as only
    the two monitoring caps — the executor retains five (the monitoring
    pair plus the setpriv trio justified in §Network capture under
    no-new-privileges). Closes [ES-1 adr0013-rationale-cap-parity].
    """
    normalized = " ".join(ADR_PATH.read_text(encoding="utf-8").split())
    stale = "adding back only monitoring capabilities (`NET_RAW`, `SYS_PTRACE`)"
    assert stale not in normalized, (
        "ADR 0013 §Rationale still under-claims the executor keepset as only "
        "(NET_RAW, SYS_PTRACE); the Decision table + compose retain five caps "
        "(NET_RAW, SYS_PTRACE, SETUID, SETGID, SETPCAP). Update the Rationale "
        "prose to name all five."
    )
