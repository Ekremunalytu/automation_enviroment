# Boundary And Dependency-Direction Rules

`Last Updated: 2026-05-05`

Detailed boundary, import-graph, and architectural-rule reference. Open
this when the import graph test fails, when adding a new top-level
package, or when reviewing whether a new dependency is allowed.

Module map and high-level shape:
[`../ARCHITECTURE.md`](../ARCHITECTURE.md).

## Canonical Layering

```text
ui/                      ← React SPA, talks to API only
↓
main.py / appcore/api/   ← FastAPI surface
↓
workflows/               ← business behavior per capability
↓
appcore/  packages/      ← shared platform code  +  framework-agnostic
                            contracts/logic
↓
executor/control.py      ← workflow ↔ sandbox boundary
↓
executor/host.py + executor/container/ + executor/flows/
                          ← Docker exec, container runtime
```

## Import-Graph Rules (Enforced By `tests/architecture/`)

- `packages/` must **not** import `workflows/`, `executor/`, `ui/`, or
  `appcore/`. Detection rules consume only contracts.
- `workflows/` reaches sandbox mechanics **only** through
  `executor/control.py` — never directly into `executor/host.py` or
  `executor/flows/`.
- `appcore/contracts/` is the schema source of truth; routers and
  services consume `appcore.contracts.schemas` (the public facade), not
  `schema_defs/*` directly.
- The W8-2 architecture test
  `tests/architecture/test_marketplace_identity_concat.py` blocks raw
  publisher/name/version concat; all sites must route through
  `packages.marketplace_identity.safe_marketplace_slug`.
- The W8-3 architecture test
  `tests/architecture/test_uri_trigger_shell_pattern.py` blocks
  `xdg-open '<f-string>'` shell-template patterns under `appcore/`,
  `executor/`, `workflows/`, `packages/`. The escape hatch is the
  `# arch-allow: xdg-open-shell-string` pragma.

## Storage Rules

- All catalog and analysis-job DB writes go through
  `appcore/storage/crud.py`.
- Thin compatibility wrappers may delegate immediately but must not
  own write logic.
- Pydantic validation precedes insertion (no raw dicts to ORM).
- Use SQLAlchemy 2.0 style only (`select()`, `Session.execute`).
- Use Pydantic v2 APIs only (`model_validate`, `model_dump`,
  `@field_validator`).
- Schema changes require an Alembic migration.
- The uniqueness constraint `(publisher, name, version)` is preserved.

## Sandbox Rules

- Sandbox execution stays Docker-isolated.
- Workflows reach the sandbox only through `executor.control`.
- The harness extension is checksum-verified at executor startup.
- ADR 0007 (local network binding): every host-facing port defaults to
  `127.0.0.1`; LAN exposure is opt-in via `EXTRACE_ALLOW_LAN=1` (host
  side) plus manual compose port editing (Docker side) per
  `documents/runbooks/lan-exposure.md`. Implemented `2026-04-29` via
  W8-7; pinned by `tests/architecture/test_default_bindings.py`.

## Security Rules

- Treat extension input, reports, logs, and VSIX contents as
  adversarial.
- No arbitrary `exec`, unsafe deserialization, or uncontrolled network
  calls.
- No generic `try/except Exception` blocks; narrow the exception set.
- Path-traversal guards on every filesystem write that consumes
  publisher/name/version (reduced to a single helper —
  `safe_marketplace_slug`).
- URI invocations go through argv-form `subprocess.run`, never shell
  string interpolation.

## Operational Rules

- Critical operations stay observable through logs, report fields,
  traces, or metrics.
- No queue-backed or multi-tenant infrastructure unless the product
  assumptions in `ARCHITECTURE.md` change first.
- No new dependencies without explicit approval.
- Compatibility/historical surfaces stay thin and out of new feature
  work.

## Forbidden Top-Level Directories

These were removed during W4 stabilization and must not be recreated:
`routers/`, `scanner/`, `core/`, `database/`, `crud/`, `models/`,
`schemas/`, `apps/`, `legacy_ui/`. New code goes under the canonical
runtime tree (`appcore/`, `packages/`, `workflows/`, `executor/`,
`ui/`, `tests/`). See `PROJECT_STRUCTURE.md` for placement rules.
