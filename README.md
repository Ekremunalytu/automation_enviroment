# ExTrace

`Last Updated: 2026-06-15`

`Last merged weekly: W22 — closed synthetically on the week22 branch, merged to main via PR #31 week22 -> main 2026-05-28 via 1399f82.`

`Active stream: operator-console-honesty (UI-only console-honesty stream, sequenced ahead of Stream 2 per 2026-06-15 direction) — opened on week24 (off main 8250db0); makes decorative/dead Settings + System controls honest (no backend/DB/detection/executor). Prior stream reliability-self-defense merged to main via PR #35 (week23 -> main, 653d807). Tracker: documents/active-work/W24-operator-console-honesty.md.`

`Sources of truth: documents/REFACTOR_STATUS.md (state) · documents/POST_POC_BACKLOG.md (deferred) · documents/REFACTOR_OPTIMIZATION.md §20 (last weekly plan) · documents/phase.json (weekly pointer + active stream).`

ExTrace is a sandboxed analysis platform for suspicious VS Code extensions.
It downloads or ingests an extension, inspects its manifest and source tree,
runs it inside an isolated VS Code environment, and produces evidence that an
analyst can review.

The project is intentionally shaped as a **single-operator security appliance**,
not a public multi-tenant web service. The default setup binds to loopback,
keeps extension samples and reports on the operator machine, and runs sandbox
execution in containers.

## What It Does

ExTrace helps answer four practical questions:

1. **What does this extension declare?**
   It parses manifest metadata, activation events, contributed commands,
   menus, scripts, and related VS Code extension surfaces.
2. **What does the source tree look like before execution?**
   Static rules scan the extracted VSIX tree for risky behavior such as
   reverse shells, download cradles, native loaders, credential exfiltration,
   path traversal surfaces, stylesheet execution, and RMM abuse.
3. **What happens when it runs?**
   The executor launches a real VS Code session under Xvfb/noVNC and drives it
   with Playwright so runtime events can be observed.
4. **What evidence should a reviewer trust?**
   Reports separate static findings, runtime evidence, attempted stimuli,
   health signals, verification gaps, and known blind spots.

The result is not a magic malware verdict. It is an evidence bundle for a human
analyst, with enough structure for regression tests and UI review.

## How It Works

```text
VSIX / extension folder
        |
        v
Manifest + source extraction
        |
        +--> Static pre-check rules
        |
        v
Trigger planning
        |
        v
Dockerized VS Code executor
        |
        v
Activation report + static report + job metadata
        |
        v
React analyst console / API responses
```

Core services:

- **API**: FastAPI backend for catalog ingestion, marketplace search/download,
  analysis jobs, reports, settings, and health.
- **Executor**: Dockerized VS Code + Playwright runtime used to run and observe
  extensions.
- **Static analyzer**: isolated static pre-check container for VSIX-tree rules
  and Semgrep-style checks.
- **Database**: PostgreSQL stores catalog and job metadata.
- **UI**: Vite + React analyst console for reports, rules, marketplace search,
  and simulation status.

For a fuller human overview, read
[documents/how-it-works.md](documents/how-it-works.md).

## Safety Model

Treat every extension, report, log line, and VSIX payload as adversarial.

- Services bind to `127.0.0.1` by default.
- LAN exposure is opt-in and must follow
  [documents/runbooks/lan-exposure.md](documents/runbooks/lan-exposure.md).
- Sandbox execution stays containerized.
- The static analyzer runs without network access.
- Live malware samples must not be committed to this repository.
- Synthetic fixtures and declawed canaries are allowed for tests.
- Reports are evidence, not proof of safety.

The binding decision is recorded in
[documents/adrs/0007-local-network-binding.md](documents/adrs/0007-local-network-binding.md).

## Quick Start For Local Development

Prerequisites:

- Python 3.11+
- Docker / Docker Compose
- PostgreSQL 16 compatible runtime
- Node 20+ for UI work

Common setup:

```bash
make install-dev
make up
make migrate
make dev
```

Default local endpoints:

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Web UI: `http://127.0.0.1:3000`
- noVNC executor view: `http://127.0.0.1:6080/vnc.html`

Useful validation commands:

```bash
make test-local
make test-security
make check-all
make sim-target TARGET=publisher.name
make demo-canary
```

For a shorter operator path, read
[documents/operator-quickstart.md](documents/operator-quickstart.md).

### Optional: code-intelligence tooling

This workspace can use LSP-backed symbol navigation (go-to-definition,
find-references, call hierarchy) through two local Claude Code plugins,
`pyright-lsp` (Python) and `typescript-lsp` (UI). They are per-operator
developer/agent conveniences — not required to build, test, or run ExTrace,
and not provisioned by the repo.

```bash
claude plugin install pyright-lsp typescript-lsp
# Python cross-file resolution also needs a repo-root pyrightconfig.json:
#   {"venvPath": ".", "venv": ".venv"}
```

`mypy` remains the authoritative Python type-checker; pyright only powers
navigation. Note: the first `find-references` of a session can return
same-file-only results — retry it once.

## Air-Gapped Podman Deployment

This branch adds a deployment path for a **headless, air-gapped x86 Fedora
Server** running **rootful Podman** with no compose or internet access on the
target.

High-level flow:

1. Build all images on an internet-connected machine.
2. Export them into one bundle.
3. Copy the bundle to the Fedora Server.
4. Run the stack with plain `podman` through the included controller.

Start here:

- [deploy/podman/README.md](deploy/podman/README.md) — full air-gapped Podman
  deployment guide.
- [deploy/podman/build-bundle.sh](deploy/podman/build-bundle.sh) — build-box
  bundle builder.
- [deploy/podman/extrace-ctl.sh](deploy/podman/extrace-ctl.sh) — server-side
  Podman controller.

Prefer SSH tunnels for remote access to the headless server. Bind services on a
LAN only after rotating secrets and applying the LAN exposure runbook.

## Project Layout

```text
appcore/             Shared platform code: config, DB, storage, contracts
packages/            Framework-agnostic analysis contracts and logic
workflows/           Backend business workflows
executor/            Sandbox control and Playwright runtime
static_runtime/      Static pre-check rules and Semgrep-style rules
ui/                  React + Vite analyst console
tests/               Python and architecture tests
documents/           Canonical architecture, status, ADR, agent docs, and human guides
deploy/podman/       Air-gapped Podman deployment bundle
```

Boundary rules that matter:

- Database writes go through `appcore/storage/crud.py`.
- Pydantic validation happens before insertion.
- SQLAlchemy 2.0 and Pydantic v2 APIs are required.
- `packages/` must stay framework-agnostic.
- Workflows reach sandbox mechanics through `executor.control`.
- Static and dynamic detection rules consume contracts, not app internals.

The full agent-facing rules live in [AGENTS.md](AGENTS.md).

## API Surface

Main routes:

- `GET /health`
- `GET /searchExtension`
- `POST /createExtension`
- `POST /api/marketplace/download`
- `POST /api/marketplace/analyze`
- `POST /api/marketplace/analyze/start`
- `GET /api/marketplace/analyze/{job_id}`
- `POST /api/marketplace/analyze/{job_id}/cancel`
- `GET /api/activations`
- `GET /api/activations/latest`
- `GET /api/settings/security/thresholds`
- `PUT /api/settings/security/thresholds`

The UI uses the background analysis route and then polls
`GET /api/marketplace/analyze/{job_id}` for job status.

Full route and request-flow reference:

- [documents/api-and-flows.md](documents/api-and-flows.md)

## Current Status

The weekly refactor line is closed through **W22**. W22 was merged to `main`
through PR #31 (`week22 -> main`, `1399f82`) on 2026-05-28. Later work lands as
named feature streams without advancing the weekly pointer.

Weekly close-out ledger:

| Phase | Merge fact | Frozen tracker |
|---|---|---|
| W13 | PR #20 `week13 -> main` `772deb3` | `active-work/W13-test-expansion-observability.md` |
| W14 | PR #21 `week14 -> main` `4e03c8d` | `active-work/W14-codex-acceptance-observability.md` |
| W15 | PR #22 `week15 -> main` `6161472` | `active-work/W15-codex-uclass-bounds-posture.md` |
| W16 | PR #23 `week16 -> main` `1b6d43f` | `active-work/W16-regression-and-audit-closeout.md` |
| W17 | PR #25 `week17 -> main` `bff565d` | `active-work/W17-carryover-and-lifecycle-harness.md` |
| W18 | PR #26 `week18 -> main` `9874e79` | `active-work/W18-heartbeat-refactor.md` |
| W19 | PR #28 `week19 -> main` `c879603` | `active-work/W19-live-run-root-cause.md` |
| W20 | PR #29 `week20 -> main` `64a3c3d` | `active-work/W20-coverage-promotion-easy-wins.md` |
| W21 | PR #30 `week21 -> main` `5dc18aa` | `active-work/W21-coverage-promotion-mid-tier.md` |
| W22 | PR #31 `week22 -> main` `1399f82` | `active-work/W22-coverage-promotion-hard-tier.md` |

Latest merged named stream:

- `reliability-self-defense`, merged via PR #35 (`653d807`) on `2026-06-12`.
- Closed v1.0 trust-floor bars B1/B3/B4 plus self-defense fixes F-2/F-3.
- Tracker: `documents/active-work/W23-reliability-self-defense.md`.

Earlier named streams include `podman-airgapped-deploy` (air-gapped deployment
bundle + human-readable documentation), `security-development`,
`extension-trigger-matrix`, and Static Analysis Pre-Check.

Detailed status is intentionally not duplicated here:

- [documents/REFACTOR_STATUS.md](documents/REFACTOR_STATUS.md) — current state
  and merge history.
- [documents/POST_POC_BACKLOG.md](documents/POST_POC_BACKLOG.md) — deferred
  work and pull-next items.
- [documents/REFACTOR_OPTIMIZATION.md](documents/REFACTOR_OPTIMIZATION.md) —
  weekly planning record.
- [documents/phase.json](documents/phase.json) — machine-readable weekly
  pointer and active stream.

## Documentation Map

For people:

- [documents/human-guide.md](documents/human-guide.md) — human documentation
  index.
- [documents/how-it-works.md](documents/how-it-works.md) — readable architecture
  and data flow.
- [documents/api-and-flows.md](documents/api-and-flows.md) — backend routes and
  request flows.
- [documents/operator-quickstart.md](documents/operator-quickstart.md) — local
  and air-gapped operating paths.
- [documents/risks.md](documents/risks.md) — risk register and accepted
  tradeoffs.

For maintainers and agents:

- [AGENTS.md](AGENTS.md) — hard rules.
- [documents/AGENT_CONTEXT.md](documents/AGENT_CONTEXT.md) — task routing.
- [documents/agent-lanes/](documents/agent-lanes/) — lane-specific read paths.
- [documents/README.md](documents/README.md) — canonical document guide.
- [documents/adrs/](documents/adrs/) — architecture decisions.
- [documents/runbooks/](documents/runbooks/) — operational recovery runbooks.

The detailed historical trackers remain in `documents/active-work/` and
`documents/archive/`. They are preserved for evidence and stable IDs, but they
are no longer the first thing a normal reader should open.
