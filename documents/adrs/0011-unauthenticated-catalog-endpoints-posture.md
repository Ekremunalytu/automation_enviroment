# ADR 0011: Unauthenticated Catalog Endpoints Posture

- Status: Accepted and implemented (`2026-05-17`)
- Date: 2026-05-17
- Accepted + Implemented: 2026-05-17 via W15-6 on the `week15` branch.
  See the Implementation section below and
  `documents/active-work/W15-codex-uclass-bounds-posture.md`.
- Related: ADR 0001 (Single-Host Appliance), ADR 0002 (Threat Model
  §4 Trust Boundaries / §5 Analyst Operating Environment),
  ADR 0007 (Local Network Binding Discipline)

## Context

`workflows/extension_catalog/router.py` mounts twelve HTTP endpoints
under the API surface (no auth dependency attached at the router
construction site):

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | API root metadata (project name, version, status, docs URL) |
| `GET` | `/health` | Legacy root health probe (preserved by W15-5 for external-monitoring back-compat) |
| `GET` | `/searchExtension` | Read catalog row by publisher + name + version |
| `GET` | `/getExtensionsBaseInfo` | List catalog rows (minimal fields) |
| `GET` | `/getExtensionsAllInfo` | List catalog rows (full detail, with `skip`/`limit` pagination) |
| `POST` | `/createExtension` | Scan `extensions/` for a name, parse `package.json`, persist row |
| `DELETE` | `/deleteExtension` | Remove catalog row |
| `GET` | `/getExtensionScripts` | Read npm scripts sub-resource |
| `GET` | `/getExtensionActivationEvents` | Read `activationEvents` sub-resource |
| `GET` | `/getExtensionCapabilities` | Read capabilities sub-resource |
| `GET` | `/getExtensionContributesAll` | Read full contributes block sub-resource |
| `GET` | `/getExtensionContributesCommands` | Read commands contributes sub-resource |

The Codex Cloud audit `2026-05-10` flagged this surface under
`U10/U11 unauth-catalog-endpoints`: the router declares no
`Depends(...)` auth dependency and accepts any request reaching it.
The audit's open question was whether the single-host scope
(ADR 0001) plus loopback bind default (ADR 0007) constitutes a
sufficient control or whether per-request authentication is required
for parity with mature multi-tenant deployments.

Two facts shape the decision space:

1. **Threat model already trusts the operator on the host.** ADR 0002
   §5 establishes a single-operator environment: the operator is the
   security analyst, not the extension publisher, and "does not
   expect confidentiality guarantees against themselves." The §4
   trust-boundary table (line 102) already covers operator-host
   network interfaces via ADR 0007: loopback by default, LAN exposure
   gated by the single audited `EXTRACE_ALLOW_LAN=1` opt-in.

2. **The UI does not call catalog endpoints.** A scan of
   `ui/src/lib/api/client.ts` (HEAD `4999cab`) shows only
   `/api/activations/*`, `/api/marketplace/*`, `/api/settings/*`, and
   the new `/api/health` (W15-5) are reachable from the UI. Catalog
   endpoints have no UI consumers; their only callers are backend
   tests (`tests/workflows/extension_catalog/test_router.py`,
   `tests/test_health.py`) and operator-side scripts.

The U10/U11 audit finding remained open through W14 because the
question is structural, not behavioral: any per-request auth scheme
must be defended against the threat model, not merely added.

## Decision

**Catalog endpoints remain unauthenticated** under three explicit
preconditions that, together, encode the trusted-environment
assumption in machine-checked form rather than prose:

### 1. Single-host appliance scope (ADR 0001) is unchanged

If ADR 0001 is ever amended to drop single-host scope (multi-tenant
SaaS, hosted appliance), this ADR must be revisited. The mechanical
enforcement is the cross-link in the `Related` header above; a future
PR that amends ADR 0001 must also acknowledge ADR 0011.

### 2. Loopback bind default (ADR 0007 §1) is unchanged

`appcore/api/config.py` defaults `API_HOST=127.0.0.1`,
`docker-compose.yml` carries the explicit `127.0.0.1:` prefix on
default-profile `ports:` entries, and `tests/architecture/
test_default_bindings.py` pins these. Catalog endpoints are
reachable from the LAN only if an operator deliberately flips
`EXTRACE_ALLOW_LAN=1`.

### 3. LAN exposure requires operator-side hardening

The runbook [`documents/runbooks/lan-exposure.md`](../runbooks/lan-exposure.md)
already mandates a pre-flight checklist before `EXTRACE_ALLOW_LAN=1`
is acceptable in operator practice: firewall rules, an
authenticating reverse proxy in front of the API, an explicit CORS
allow-list, and a rotated PostgreSQL password. Reverse-proxy auth
is the correct control surface for LAN exposure because it covers
every API surface uniformly (catalog, marketplace, activations,
settings) without per-router code change.

### Sub-decisions

- **Scope of this ADR.** ADR 0011 covers `workflows/extension_catalog/
  router.py` only. The marketplace router (`/api/marketplace/*`) and
  settings router (`/api/settings/*`) posture are out of scope and
  remain whatever they currently are; their posture is not implied
  by this decision and must be argued separately if challenged.
- **Legacy `/health` route.** The legacy root `/health` on the
  catalog router (preserved by W15-5 for external-monitoring
  back-compat) falls under this ADR's posture — same single-host /
  loopback / opt-in-LAN preconditions.
- **`/api/health` route.** The dedicated `/api/health` route on the
  new `appcore/api/health_router.py` (W15-5) is explicitly **out of
  scope**. Health endpoints are conventionally open and do not
  require ADR coverage.
- **Future posture shift.** Migration to per-request authentication
  (HMAC marker, session, OAuth, etc.) requires an ADR 0011 amendment
  with explicit motivation, not a silent code change. The
  architecture gate landed in `tests/architecture/
  test_catalog_endpoint_posture.py` mechanically prevents drift.

### Why not per-request HMAC marker auth

The W13-1 launch-scoped HMAC pattern (`executor/flows/playwright/
health/reconciliation.py:39-115`) is sometimes cited as a transferable
template. It is not, for two reasons:

1. **Scope mismatch.** W13-1 HMAC is a per-launch, single-shot
   in-container handshake between `launch_vscode.sh` (producer of
   `/results/_extrace_harness_python_secret`) and the Python
   reconciliation path (consumer, reads + unlinks). It is not an
   HTTP-request authenticator. An HTTP-request variant would require
   header signing, time-window nonce, replay protection, and a
   secret-distribution channel to non-UI clients — substantially
   more design than "mirror W13-1".
2. **Threat-model motivation is absent.** ADR 0002 §5 does not
   define an adversary class that targets the operator from inside
   their own host. Adding per-request auth defends against an
   adversary class the threat model does not name; the cost is
   real, the benefit is conjectural.

Per-request HMAC remains a natural follow-on **if** the threat model
later expands (multi-operator, hosted appliance, or a same-host
adversary class such as a default-on CDP `debug` profile becoming
the norm).

## Consequences

### Positive

- The trusted-environment assumption that already holds for the rest
  of the API surface (marketplace, activations, settings) is now
  explicitly stated for the catalog surface, with the same
  preconditions cited and the same opt-in escape hatch.
- Zero behavioral code churn — no secret distribution problem, no UI
  breaking change (UI does not call these endpoints), no test surface
  rewrite.
- The architecture gate landed alongside this ADR locks the posture:
  a future PR that attaches an auth `Depends(...)` to the catalog
  router or adds a new catalog endpoint without ADR amendment fails
  the gate before review.
- Forward path is preserved. ADR 0011 amendment + HTTP-request HMAC
  marker auth (a real adaptation of W13-1, not a copy) is the
  natural next step if the threat model expands.

### Negative

- An operator who flips `EXTRACE_ALLOW_LAN=1` without reading the
  runbook exposes catalog mutate endpoints
  (`POST /createExtension`, `DELETE /deleteExtension`) to the LAN
  along with the rest of the API. The runbook covers this; ADR 0011
  cites it explicitly. Defense-in-depth via a reverse proxy in front
  of the API is the operator's responsibility per ADR 0007 §2.
- The architecture gate's endpoint-count invariant is intentionally
  strict: a new catalog endpoint added later trips the gate, forcing
  an ADR 0011 amendment review at the same time. This is the
  designed-in friction — silent surface expansion under a posture
  ADR is the failure mode the gate exists to prevent.
- One additional architecture test must stay green; future
  legitimate posture shifts must update the test and amend this
  ADR.

### Follow-On

- Posture-shift triggers (intentional list — any of these warrants
  an ADR 0011 amendment, not a silent code change):
  - ADR 0001 amended to drop single-host scope (multi-tenant or
    hosted SaaS).
  - ADR 0002 §1 amended to add an adversary class that targets the
    operator from inside their own host (e.g., a same-host
    extension reaching the API over the docker bridge).
  - CDP `debug` profile is promoted to default-on (ADR 0009
    amended), which would put a same-host process in CDP-reach of
    the API surface.
- If a posture shift lands, the W13-1 HMAC pattern is **adapted**,
  not copied. HTTP-request auth requires header signing (e.g.,
  `X-ExTrace-Signature: <hmac-sha256>`), a time-window nonce, a
  shared-secret distribution channel for non-UI clients, and a
  per-route allow-list. ADR 0007's
  `documents/runbooks/lan-exposure.md` already nominates a reverse
  proxy as the canonical control surface; per-route HMAC is the
  defense-in-depth complement, not a replacement for reverse-proxy
  auth.

## Implementation

Landed `2026-05-17` on `week15` (W15-6).

- `workflows/extension_catalog/router.py` — module docstring states
  the posture and cites ADR 0011 verbatim; an inline comment at the
  `router = APIRouter(tags=["core"])` construction site (line 33-37)
  documents that the absence of an auth `Depends(...)` is
  intentional and locked by this ADR + the architecture gate.
  Behavioral code unchanged.
- `tests/architecture/test_catalog_endpoint_posture.py` (new) —
  three AST-level invariants:
  - `test_catalog_router_module_cites_adr_0011` — the router module
    docstring contains the substring `ADR 0011` so doc decay
    cannot silently strand the posture rationale.
  - `test_catalog_router_has_no_auth_dependency` — the
    `APIRouter(...)` construction site does not attach a
    `dependencies=[...]` kwarg whose callable names match the
    auth-like regex `^(auth|require_|verify_|hmac_|marker_).*`.
    Silent drift to Option B via a one-liner is prevented.
  - `test_catalog_router_endpoint_count_locked` — the decorator
    count for `@router.<verb>` is locked at twelve (eleven listed
    endpoints plus `/` root). A new endpoint added later fails the
    gate, forcing an ADR 0011 amendment review.
- `documents/POST_POC_BACKLOG.md` — `[FOLLOWUP
  codex-2026-05-10-U10-U11-unauth-catalog-endpoints]` moves from
  open to Verified Closed Audit Trail.
- ADR 0002 is **not** amended. ADR 0011 cites §4 row 102 (operator
  host network interfaces, ADR 0007) and §5 (analyst operating
  environment) as load-bearing prerequisites without restating
  them.

Verification at landing time:

- `pytest tests/architecture/test_catalog_endpoint_posture.py -v`
  → 3 passed.
- `pytest tests/architecture/ -q` → 191 passed / 4 deselected
  (W15-5 baseline 188 + 3 new gate cases from the new file).
- `pytest tests/workflows/extension_catalog/test_router.py
  tests/test_health.py -q` → 42 passed (no behavioral regression).
- `make test-security` → 215 passed.
- `make markdownlint` → clean.

The gate-count delta is `+1 gate file` (`test_catalog_endpoint_
posture.py`) with three test functions; the W14-6 "extend, do not
duplicate" check applied — no existing gate covered router posture
invariants, so a new file is appropriate.
