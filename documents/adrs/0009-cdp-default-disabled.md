# ADR 0009: CDP Default-Disabled in the Executor Container

- Status: Accepted and implemented (`2026-05-13`)
- Date: 2026-05-13
- Accepted + Implemented: 2026-05-13 via W14-3 on the `week14` branch
  (commit `941250d`). See the Implementation section below and
  `documents/active-work/W14-codex-acceptance-observability.md`.
- Related: ADR 0007 (Local Network Binding Discipline) §4 "CDP exposure
  is opt-in even on loopback", ADR 0002 (Threat Model §4 Trust
  Boundaries, §5 Analyst Operating Environment).

## Context

ADR 0007 §4 closed the **host → container** CDP exposure seam: the
default `docker compose up` no longer maps the `executor-cdp` socat
sidecar's host port, so an attacker on the operator's network cannot
reach the executor's Chrome DevTools Protocol interface from outside the
container.

ADR 0007 did not close a second seam: **container-internal** CDP. The
executor container always started VS Code with
`--remote-debugging-port=9222` (sourced from
`EXECUTOR_CDP_PORT:-9222` defaults baked into `executor/container/start.sh`,
`executor/container/launch_vscode.sh`, and the `executor` service entry
in `docker-compose.yml`). Inside the container, the CDP interface was
unauthenticated and reachable on `localhost:9222` from any process in
the same network namespace — including the analyzed target extension's
own host process.

The Codex Cloud audit `2026-05-10` flagged this as `M14b
cdp-port-default-disabled`: a malicious VSIX able to reach the loopback
CDP socket can drive the live VS Code workbench, hijack capture, or
disable the harness extension. The default-on behavior is acceptable for
debug profile boots (operator inspects CDP directly via the sidecar) but
not for routine `make up` boots where no operator-side CDP consumer
exists.

## Decision

Container-internal CDP follows the same opt-in posture ADR 0007 §4
applied to host-side exposure: **CDP is off by default; turning it on
requires an explicit `EXECUTOR_CDP_PORT` environment variable**.

### 1. `EXECUTOR_CDP_PORT` defaults to empty

`executor/container/launch_vscode.sh`,
`executor/container/start.sh`, and `docker-compose.yml` (executor service
environment entry) all source the variable with an empty default:

```bash
# Was:
CDP_PORT="${EXECUTOR_CDP_PORT:-9222}"
# Becomes:
CDP_PORT="${EXECUTOR_CDP_PORT:-}"
```

Without an explicit operator-side override, the variable propagates as
an empty string through the executor service env, through `start.sh`,
and into `launch_vscode.sh`. The host-side `executor-cdp` debug-profile
sidecar in `docker-compose.yml` keeps its own `:-9222` fallback because
ADR 0007 §4 already gates it behind the `debug` Compose profile *and*
the Makefile `up-debug` lane explicitly sets the variable before
invoking compose.

### 2. The `--remote-debugging-port` flag is conditionally appended

`launch_vscode.sh` builds a `CDP_FLAG=()` Bash array and only populates
it when `${CDP_PORT}` is non-empty:

```bash
CDP_FLAG=()
if [ -n "${CDP_PORT}" ]; then
    CDP_FLAG=(--remote-debugging-port="${CDP_PORT}")
fi
setsid code --no-sandbox \
    --user-data-dir "${VSCODE_USER_DATA_DIR}" \
    --extensionDevelopmentPath="${HARNESS_EXT_PATH}" \
    "${CDP_FLAG[@]}" \
    --log "${VSCODE_LOG_LEVEL}" \
    "${WORKSPACE_PATH}" \
    </dev/null >/dev/null 2>&1 &
```

When the flag is absent, VS Code starts without binding any CDP port. A
process inside the same container that probes `localhost:9222` (or any
other port) gets a `connection refused`, not an authenticated CDP
session.

### 3. Operator UX is preserved via `make up-debug`

The Makefile `up-debug` recipe explicitly sets the variable before
invoking compose, so the debug profile still works exactly as it did
under ADR 0007 §4:

```make
up-debug:
	@EXECUTOR_CDP_PORT=9222 docker-compose --profile debug up -d
	...
```

`start.sh` reports the active posture in its readiness banner:

```text
CDP   : disabled (set EXECUTOR_CDP_PORT to opt in)
```

becomes

```text
CDP   : localhost:9222
```

once an operator opts in.

### 4. Playwright orchestration is unaffected

`executor/flows/playwright/vscode/__init__.py:15` reads
`EXECUTOR_CDP_PORT` to build `CDP_URL`. If a future control path inside
the executor needs to drive VS Code via CDP (e.g. a scenario that
attaches to the workbench), the orchestration code is already
parameterized — operators who invoke that path set
`EXECUTOR_CDP_PORT=9222` (the same opt-in lane as `make up-debug`) and
the Playwright stack reaches the now-bound port. The routine
analysis pipeline does not exercise that path; the harness extension
drives capture from inside VS Code rather than from a host-side
Playwright session against CDP.

### 5. Architecture test guards the default

`tests/architecture/test_cdp_port_default.py` pins four content-level
invariants:

- `launch_vscode.sh` sources `CDP_PORT` with the empty default
  (`${EXECUTOR_CDP_PORT:-}`); the literal `9222` fallback is absent.
- `launch_vscode.sh` carries the conditional `CDP_FLAG=()` /
  `if [ -n "${CDP_PORT}" ]` shape; the unconditional
  `--remote-debugging-port="${CDP_PORT}"` argument is absent.
- `start.sh` mirrors the empty default.
- `docker-compose.yml` executor service env sources
  `EXECUTOR_CDP_PORT: ${EXECUTOR_CDP_PORT:-}` (empty default).

The test fails if a future change re-introduces the `9222` fallback at
the executor layer or unconditionally appends the CDP flag.

## Consequences

### Positive

- Closes the container-internal seam ADR 0007 §4 did not cover. A
  malicious VSIX able to reach `localhost:9222` from inside the
  container now hits a closed port; the attack surface for CDP
  hijacking shrinks to the debug-profile boot, which an operator
  consciously opts into.
- Operator UX is unchanged: `make up` is loopback-only and CDP-closed,
  `make up-debug` opens CDP exactly as before via the same Makefile
  lane.
- Defense-in-depth pair with ADR 0007 §4: host-side exposure
  *and* in-container enablement are both gated behind the same opt-in
  variable, so a future regression to either layer is independently
  visible through its own architecture test.

### Negative

- A future feature that wants the executor to drive CDP for itself (e.g.
  a verification scenario that attaches to the workbench from a sibling
  process) needs an explicit `EXECUTOR_CDP_PORT` opt-in. This is the
  intended posture, not a side effect — automation that needs CDP must
  declare it.
- One additional architecture test must stay green; future changes that
  legitimately need different defaults must update both the test and
  this ADR.

### Follow-On

- Implemented as W14-3 in the W14 — Codex M-class Acceptance window;
  see `documents/active-work/W14-codex-acceptance-observability.md`
  §"W14-3" for the close evidence (`941250d`).
- README "Service Endpoints" block (lines 252-264) and Makefile
  `up-debug` recipe documentation already point at the debug-profile
  CDP availability; no further README changes were needed because the
  user-visible UX is identical.
- ADR 0007 stays authoritative for the **host → container** CDP
  exposure seam; this ADR documents the **container-internal**
  complement.

## Implementation

Landed `2026-05-13` on `week14` (W14-3, commit `941250d`).

- `executor/container/launch_vscode.sh` — `CDP_PORT` empty default;
  `CDP_FLAG=()` array conditionally populated when the port is set.
- `executor/container/start.sh` — same empty default; readiness banner
  now reports `disabled (set EXECUTOR_CDP_PORT to opt in)` when the env
  var is missing.
- `docker-compose.yml` — executor service `EXECUTOR_CDP_PORT` env
  sources the empty default. The `executor-cdp` debug-profile sidecar
  keeps its own `:-9222` fallback because the Makefile lane sets the
  env var explicitly before invoking compose.
- `Makefile` — `up-debug` recipe now exports
  `EXECUTOR_CDP_PORT=9222` before `docker-compose --profile debug up
  -d` so the debug profile UX is unchanged.
- `tests/architecture/test_cdp_port_default.py` — 4 content cases
  pinning the empty default + conditional flag append + start-script
  mirror + compose empty default. Wired into `make test-security`.
- `documents/active-work/W14-codex-acceptance-observability.md`
  §"W14-3 — Codex M-class external surface hardening" — full landing
  evidence (sub-commit table, module locations, test deltas).
