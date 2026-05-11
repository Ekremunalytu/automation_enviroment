# Runbook: LAN Exposure (`EXTRACE_ALLOW_LAN`)

`Last Updated: 2026-05-11`

This runbook covers the deliberate, opt-in path to expose ExTrace services
on the operator host's LAN interfaces. Per ADR 0007, every host-facing
port binds `127.0.0.1` by default; LAN exposure is a configuration change
that ships with no built-in authentication, so the operator's duties
listed below are not optional.

## When to Use

Apply this runbook only when **all** of the following are true:

- A second host on the same network needs to reach the API or UI (remote
  analyst workstation, multi-host lab, Playwright driver running on a
  peer machine).
- The operator can guarantee the network path is trusted (private VLAN,
  WireGuard peer link, or LAN behind a perimeter firewall — **not**
  public Wi-Fi).
- The operator is willing to put an authenticating reverse proxy in
  front of port `8000` before flipping the flag.

If any of those is unmet, **do not run this runbook**. The default
loopback binding is the correct posture and `EXTRACE_ALLOW_LAN` should
stay unset.

## Pre-Flight Checklist

Each item must be confirmed before flipping the flag — order matters.

1. **Firewall on the operator host.** The host's perimeter firewall must
   reject inbound `8000`, `3000`, `6080`, `9222`, `5432`, and `5434` from
   networks outside the trust boundary. On macOS this is the application
   firewall + per-port pf rules; on Linux this is `ufw` / `nftables` /
   `iptables`. Verify from a peer host on the *untrusted* network that
   `nc -zv <host-ip> 8000` fails.

2. **Authenticating reverse proxy in front of port 8000.** Stand up an
   nginx / Caddy / Traefik instance with TLS termination and HTTP basic
   auth or mTLS, listening on the LAN-facing IP. Forward the proxy's
   backend to `http://127.0.0.1:8000` (still loopback on the ExTrace
   side — the proxy bridges the trust boundary).

3. **Explicit CORS allow-list.** Do **not** rely on the
   `EXTRACE_ALLOW_LAN=1` wildcard substitution (it is a development
   convenience, not a security feature — `*` with credentials is
   silently rejected by the browser CORS spec). Set
   `API_CORS_ALLOW_ORIGINS` to a comma-separated explicit list of origins
   the proxy will serve, e.g. `https://extrace.lab.local,https://analyst.lab.local`.

4. **Rotate `POSTGRES_PASSWORD`.** The dev default `postgres` is reachable
   today only because the listener binds `127.0.0.1`. Generate a 32-char
   secret, replace it in `.env` (`POSTGRES_PASSWORD=...`), and restart
   the postgres + api containers. Verify the new credential before
   proceeding.

5. **Re-read the threat model.** ADR 0002 §5 assumes a single-operator
   trust model; LAN exposure widens that boundary. Confirm the new
   reachers (peers on the LAN) are subject to the same threat model.

## Configure

Two paths, depending on whether you run the API in host mode or in Docker.

### Host-mode (`make dev-lan`)

```bash
EXTRACE_ALLOW_LAN=1 make dev-lan
```

The target emits a one-line warning to stdout before uvicorn launches:

```text
⚠️  ADR 0007 — LAN binding requested. Read documents/runbooks/lan-exposure.md first.
```

This banner is intentional — it is the only in-process signal that the
loopback default has been bypassed. If the warning does not appear, the
flag is not active and the process is still loopback-bound.

The `APISettings.model_post_init` hook in
[appcore/api/config.py](../../appcore/api/config.py) substitutes
`HOST=0.0.0.0` and (if you did not set an explicit allow-list) restores
`CORS_ALLOW_ORIGINS=*` when the app settings still hold the loopback
defaults. The `make dev-lan` recipe currently passes `uvicorn --host
0.0.0.0` directly, so `API_HOST=... make dev-lan` does **not** narrow the
socket bind; use `make dev`/direct uvicorn for a custom host, or pull
`[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]` to change the
recipe and add a regression gate.

### Docker (`make up`)

The compose `ports:` mappings carry an explicit `127.0.0.1:` host-IP
prefix; that is **structural** and is not affected by
`EXTRACE_ALLOW_LAN`. To expose Docker services on the LAN you must edit
[docker-compose.yml](../../docker-compose.yml) directly:

```yaml
services:
  api:
    ports:
      - "${API_PORT:-8000}:${API_PORT:-8000}"   # drop the 127.0.0.1: prefix
```

The architecture test
[`tests/architecture/test_default_bindings.py`](../../tests/architecture/test_default_bindings.py)
will fail after this edit; that is intentional. Add a comment marking
the deviation and the operator's hardening evidence (proxy hostname,
firewall rule ID), and gate the test via a CI variable if your fork
ships a non-default operator profile.

Host-side CDP exposure (port 9222) stays behind the `debug` Compose
profile regardless of `EXTRACE_ALLOW_LAN` — start it with `make up-debug`
only when you need host-side CDP inspection on the operator host itself.

## Verify

From a peer host on the trusted LAN:

```bash
# Through the reverse proxy (TLS + auth) — expected: 200
curl -u "<user>:<pass>" https://<lan-ip>/health

# Direct to the API (bypassing proxy) — expected: connection refused
# unless you also dropped the 127.0.0.1: compose prefix
nc -zv <lan-ip> 8000
```

From the *untrusted* network (e.g. a guest Wi-Fi):

```bash
# Expected: connection refused / timeout
nc -zv <lan-ip> 8000 9222 5432 6080 3000
```

Run the architecture suite to confirm the in-process settings still
honor ADR 0007:

```bash
make test-security
```

## Rollback

```bash
unset EXTRACE_ALLOW_LAN
make down
make up
```

Settings revert to loopback on the next process start. If you also
edited `docker-compose.yml`, restore the `127.0.0.1:` prefixes from
`git diff docker-compose.yml`.

## Code References

- [appcore/api/config.py](../../appcore/api/config.py) —
  `_allow_lan()`, `APISettings.model_post_init` (substitution logic),
  default values for `HOST`, `CORS_ALLOW_ORIGINS`,
  `CORS_ALLOW_CREDENTIALS`.
- [docker-compose.yml](../../docker-compose.yml) — host-IP prefixes on
  every default-profile `ports:` entry; `executor-cdp` socat sidecar
  under `profiles: ["debug"]`.
- [.env.example](../../.env.example) — security notice block describing
  the loopback default and the opt-in path.
- [Makefile](../../Makefile) — `dev`, `dev-lan`, `up`, `up-debug` targets.
- [tests/architecture/test_default_bindings.py](../../tests/architecture/test_default_bindings.py)
  — regression gate for the loopback / opt-in / compose discipline.
- [documents/adrs/0007-local-network-binding.md](../adrs/0007-local-network-binding.md)
  — decision record this runbook implements.
