# ADR 0007: Local Network Binding Discipline

- Status: Proposed
- Date: 2026-04-25
- Related: ADR 0001 (Single-Host Appliance), ADR 0002 (Threat Model §4 Trust Boundaries, §5 Analyst Operating Environment)

## Context

ADR 0001 declares ExTrace a single-host appliance and ADR 0002 §5 assumes the
operator runs the platform on "an isolated workstation or dedicated server".
Neither assumption is mechanically enforced today. In practice the shipped
defaults expose every analyzer service on every network interface of the
operator host:

- `.env.example:46` — `API_HOST=0.0.0.0` (uvicorn binds all interfaces).
- `.env.example:59-62` — `API_CORS_ALLOW_ORIGINS=*` plus
  wildcard methods/headers, so any origin reachable on the LAN can drive the
  API from a browser context.
- `docker-compose.yml:27-28` — API port mapped as
  `"${API_PORT:-8000}:${API_PORT:-8000}"`; without an explicit IP prefix the
  Docker daemon binds `0.0.0.0` on the host.
- `docker-compose.yml:66-68` — executor exposes the noVNC port (default
  `6080`) and the **Chrome DevTools Protocol** port (default `9222`) the
  same way. CDP is unauthenticated by design and grants full control of the
  VS Code instance running inside the sandbox to anyone who can reach it.
- `docker-compose.yml:101-102` — UI port `3000` mapped the same way.
- `docker-compose.yml:11-12,119-120` — PostgreSQL `5432` and the test
  database `5434` mapped the same way; default credentials in
  `.env.example` are `postgres / postgres`.
- `.env.example:82-84` — a `SECURITY NOTICE` comment tells the operator the
  application is "for INTERNAL USE ONLY" and "Ensure it runs in a trusted
  network", but enforcement is operator-side only.

This is acceptable on an isolated workstation. It is not acceptable on a lab
LAN, on a developer laptop attached to public Wi-Fi, or on a shared host —
all realistic operator environments. A single LAN-adjacent attacker with a
route to the host can:

- attach to CDP `9222` and execute arbitrary JavaScript in the live VS Code
  instance, hijack capture, or pivot via the harness extension;
- view the noVNC stream `6080` and read whatever the analyzed extension
  displays (including secrets emitted into terminal/output channels);
- POST to `/api/marketplace/analyze/start` and run analyses against
  attacker-supplied fixtures;
- query PostgreSQL with the default credentials and read or mutate the
  catalog and `analysis_jobs` table.

The threat model (ADR 0002 §1) puts these capabilities out of scope only
because the operating environment is trusted. The defaults break that
premise.

## Decision

The operator's trusted-environment assumption is encoded in code and
configuration so that going outside it requires an explicit, auditable
opt-in.

### 1. Loopback by default

Every host-facing port defaults to `127.0.0.1`. This applies to:

- API (`API_HOST` setting and the FastAPI/uvicorn launch command).
- UI dev server / production proxy.
- Executor noVNC port (`EXECUTOR_NOVNC_PORT`).
- Executor CDP port (`EXECUTOR_CDP_PORT`).
- PostgreSQL primary and test databases.

In `docker-compose.yml`, host port mappings use the explicit IP form:

```yaml
ports:
  - "127.0.0.1:${API_PORT:-8000}:${API_PORT:-8000}"
```

instead of the ambiguous `"${API_PORT:-8000}:${API_PORT:-8000}"` form, so
the Docker daemon does not silently bind `0.0.0.0`.

### 2. LAN exposure is opt-in

Operators who genuinely need LAN access (multi-host lab, remote analyst
workstation) set a single environment variable:

- `EXTRACE_ALLOW_LAN=1`

When set, the canonical entrypoints (Makefile targets, `appcore/api/config.py`
post-init, the compose `ports:` selector) substitute `0.0.0.0` for the bind
addresses listed in (1). No other variable enables LAN exposure.

A short `documents/runbooks/lan-exposure.md` runbook documents what an
operator must additionally harden before flipping the flag (firewall rules,
authenticating reverse proxy in front of the API, CORS allow-list, rotated
PostgreSQL password).

### 3. CORS is allow-list by default

`API_CORS_ALLOW_ORIGINS` defaults to `http://localhost:3000` (the UI dev
port) instead of `*`. Wildcards become opt-in via the same
`EXTRACE_ALLOW_LAN=1` env var, or explicitly via a comma-separated origin
list. `API_CORS_ALLOW_CREDENTIALS=false` stays — wildcard origins with
credentials are never permitted.

### 4. CDP exposure is opt-in even on loopback

The default operator never needs to reach CDP from the host; the executor
container drives Playwright internally. The compose port mapping for
`EXECUTOR_CDP_PORT` is gated behind a Compose profile (`debug`) and is
absent from the default service set. Operators who want host-side CDP
inspection run `docker compose --profile debug up`.

### 5. Default PostgreSQL credentials are non-secret strings

`.env.example` retains the existing dev defaults (`postgres / postgres`)
but a new comment block makes it explicit:

- These credentials are dev-only.
- They are reachable only because the listener binds loopback.
- A production or shared-host deployment must rotate them before flipping
  `EXTRACE_ALLOW_LAN=1`.

### 6. Architecture test guards the default

`tests/architecture/test_default_bindings.py` (new) loads
`appcore/api/config.py` settings with no env overrides and asserts:

- `settings.api.HOST == "127.0.0.1"`.
- `settings.api.CORS_ALLOW_ORIGINS != ["*"]`.
- The compose file's `ports:` entries that map host ports either carry an
  explicit `127.0.0.1:` prefix or are gated behind a non-default profile.

The test fails if a future change re-introduces a `0.0.0.0` default or a
host-bound CDP port without the `debug` profile.

## Consequences

### Positive

- Threat model assumptions move from prose to enforced configuration.
- A casual `make dev` on a laptop attached to public Wi-Fi no longer
  exposes CDP, the API, or the database to the LAN.
- Operators who genuinely need LAN exposure have a single, auditable knob
  (`EXTRACE_ALLOW_LAN`) and a runbook listing the prerequisite hardening.
- ADR 0002 §4 trust-boundary table can be extended with an explicit
  "Operator host network interfaces — loopback by default, opt-in LAN" row
  without inventing new policy.

### Negative

- Multi-host development setups (rare today) need one extra env var.
- A reverse proxy or VPN front-end is now the operator's responsibility for
  any non-loopback deployment; this used to be implicit but is now spelled
  out.
- One additional architecture test must stay green; future changes that
  legitimately need different defaults must update both the test and this
  ADR.

### Follow-On

- Implemented as `REFACTOR_OPTIMIZATION.md` §11.5 item 7 (W8-7) in the
  W8-W13 external-review integration window.
- README and AGENTS.md update points: the API surface section, the
  "Service Endpoints" block in the root `README.md`, and the
  `documents/runbooks/` index.
- ADR 0002 §4 trust-boundary table is appended with the operator-host
  network interface row in the same change set; ADR 0002 itself stays
  authoritative for the threat model.
- `.env.example` is rewritten so the security notice describes both the
  loopback default and the `EXTRACE_ALLOW_LAN` opt-in, instead of leaving
  enforcement to the operator alone.
