# ADR 0007: Local Network Binding Discipline

- Status: Accepted and implemented (`2026-04-29`)
- Date: 2026-04-25 (doc-sync `2026-05-05`)
- Accepted: 2026-04-27 — promoted ahead of W8-7 implementation; no content changes vs the 2026-04-25 Proposed text.
- Implemented: 2026-04-29 via W8-7 (`feat/w8-7-lan-binding-defaults`); see the Implementation section below and `REFACTOR_STATUS.md`.
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

When set, `appcore/api/config.py` `model_post_init` substitutes `0.0.0.0`
and `*` for the loopback bind addresses on the host (FastAPI/CORS) surfaces,
and Makefile targets (`dev-lan`) wire the env var through. **Docker
exposure is not controlled by `EXTRACE_ALLOW_LAN`**: the compose `ports:`
mappings carry literal `127.0.0.1:` prefixes and require manual editing per
[`runbooks/lan-exposure.md`](../runbooks/lan-exposure.md). No other variable
enables LAN exposure.

The [`documents/runbooks/lan-exposure.md`](../runbooks/lan-exposure.md)
runbook owns the operator-side pre-flight checklist for what must be
hardened before flipping the flag (firewall rules, authenticating reverse
proxy in front of the API, explicit CORS allow-list, rotated PostgreSQL
password, and a re-read of the ADR 0002 threat model with the widened
trust boundary in mind). Runbook content is the canonical source of
truth — the items above are paraphrased and may evolve as the
operator-side trust posture is sharpened.

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

- Implemented as §11.5 item 7 (W8-7) in the
  [`REFACTOR_OPTIMIZATION` full snapshot](../archive/plans/REFACTOR_OPTIMIZATION_full_2026-06-15.md),
  within the W8-W13 external-review integration window.
- README and AGENTS.md update points: the API surface section, the
  "Service Endpoints" block in the root `README.md`, and the
  `documents/runbooks/` index.
- ADR 0002 §4 trust-boundary table is appended with the operator-host
  network interface row in the same change set; ADR 0002 itself stays
  authoritative for the threat model.
- `.env.example` is rewritten so the security notice describes both the
  loopback default and the `EXTRACE_ALLOW_LAN` opt-in, instead of leaving
  enforcement to the operator alone.
- ADR 0011 (`2026-05-17`, W15-6) cites §1 (Loopback by default) as one
  of three load-bearing preconditions for keeping catalog endpoints
  unauthenticated. The `documents/runbooks/lan-exposure.md` pre-flight
  checklist remains the canonical control surface for LAN exposure —
  reverse-proxy auth covers every API surface uniformly. Any amendment
  to §1 that drops the loopback default must also revisit ADR 0011.

## Implementation

Landed `2026-04-29` on `feat/w8-7-lan-binding-defaults` (W8-7).

- `appcore/api/config.py` — `APISettings.HOST` defaults to `127.0.0.1`,
  `CORS_ALLOW_ORIGINS` defaults to `http://localhost:3000`,
  `CORS_ALLOW_CREDENTIALS` defaults to `False`. The
  `model_post_init` hook substitutes `0.0.0.0` and `*` only when
  `EXTRACE_ALLOW_LAN` is truthy *and* the field still holds the loopback
  default; explicit env overrides win over the substitution.
- `docker-compose.yml` — every default-profile `ports:` entry carries
  the explicit `127.0.0.1:` host-IP prefix. The CDP port (`9222`) is
  routed through a new `executor-cdp` socat sidecar under
  `profiles: ["debug"]`; the default `docker compose up` does not start
  it.
- `.env.example` — defaults match the post-init values; the security
  notice block describes the loopback posture and the opt-in path.
- `Makefile` — `dev` and `run` bind `127.0.0.1`; new `dev-lan` target
  flips `EXTRACE_ALLOW_LAN=1`; new `up-debug` target starts the
  `debug` profile (CDP exposed via the sidecar).
- `documents/runbooks/lan-exposure.md` — operator-side pre-flight
  checklist (firewall rules, reverse-proxy auth, explicit CORS
  allow-list, rotated PostgreSQL password, ADR 0002 threat-model
  re-read) that must precede any LAN exposure. The runbook is the
  canonical control surface; the items above are summarized.
- `tests/architecture/test_default_bindings.py` — 14 cases pinning
  loopback defaults, the truthy/falsy semantics of `EXTRACE_ALLOW_LAN`,
  the compose host-IP prefix discipline, and the CDP `debug`-profile
  gate. Wired into `make test-security`.
- ADR 0002 §4 (Trust Boundaries) — new "Operator host network
  interfaces" row added in the same change set, per the Follow-On note
  above.
