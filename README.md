# ExTrace

`Last Updated: 2026-08-03 — Last merged weekly: W22 via PR #31 (week22 -> main, 1399f82). Frozen tracker: documents/active-work/W22-coverage-promotion-hard-tier.md.`

`Active named stream: static-analysis-artifact-precision; SAP-0..SAP-4 are complete and SAP-5 is next. Containment safety remains the next product/release gate.`

ExTrace is a sandboxed analysis platform for suspicious VS Code extensions. It
combines manifest inspection, static rules, isolated runtime observation, and
structured reports for a human analyst.

It is a single-operator security appliance, not a public multi-tenant scanner.
Reports are evidence to review, not proof that an extension is safe or
malicious.

## Analysis Flow

```text
VSIX / extension folder
        |
        v
Manifest and source extraction
        |
        +--> isolated static pre-check
        |
        v
Trigger planning
        |
        v
Dockerized VS Code + Playwright execution
        |
        v
Static report + activation report + job metadata
        |
        v
React analyst console / API
```

ExTrace answers four questions:

1. What does the extension declare?
2. What risky patterns appear before execution?
3. What happens inside the sandbox?
4. How complete and trustworthy was the observation?

The last question matters: attempted stimuli, verified evidence, health
signals, and observation gaps are reported separately.

## Quick Start

Prerequisites: Python 3.11+, Docker with Compose, a PostgreSQL 16-compatible
runtime, and Node 20+ for UI work.

```bash
make install-dev
make up
make migrate
make dev
```

Default endpoints:

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- UI: `http://127.0.0.1:3000`
- noVNC: `http://127.0.0.1:6080/vnc.html`

Useful checks:

```bash
make test-local
make test-security
make check-all
make sim-target TARGET=publisher.name
make demo-canary
```

For an operator-focused setup, use
[documents/operator-quickstart.md](documents/operator-quickstart.md).

## Safety Model

- Services bind to `127.0.0.1` by default.
- LAN exposure is explicit and follows
  [documents/runbooks/lan-exposure.md](documents/runbooks/lan-exposure.md).
- Extension execution stays containerized.
- The static analyzer has no network access.
- Extension input, VSIX contents, reports, and logs are adversarial.
- Real malware samples are not committed; tests use synthetic or declawed
  fixtures.

The binding decision is recorded in
[ADR 0007](documents/adrs/0007-local-network-binding.md).

## Project Layout

```text
appcore/        configuration, contracts, database, storage
packages/       framework-agnostic analysis logic
workflows/      backend workflows
executor/       sandbox control and Playwright runtime
static_runtime/ static pre-check runtime and rules
ui/             React + Vite analyst console
tests/          Python and architecture tests
documents/      canonical docs, ADRs, runbooks, trackers
deploy/podman/  air-gapped Podman deployment
```

Hard architecture and security rules live in [AGENTS.md](AGENTS.md).

## Deployment And Documentation

For headless air-gapped Fedora deployments with rootful Podman, start at
[deploy/podman/README.md](deploy/podman/README.md).

Choose documentation by task:

- Human overview: [documents/human-guide.md](documents/human-guide.md)
- Architecture and data flow:
  [documents/how-it-works.md](documents/how-it-works.md)
- API and request flows:
  [documents/api-and-flows.md](documents/api-and-flows.md)
- Risks and accepted tradeoffs: [documents/risks.md](documents/risks.md)
- Agent routing: [documents/AGENT_CONTEXT.md](documents/AGENT_CONTEXT.md)
- Operational recovery: [documents/runbooks/](documents/runbooks/)
- Architecture decisions: [documents/adrs/](documents/adrs/)

## Project State

W22 is the last merged weekly close-out. Later work uses named streams without
advancing that pointer. The latest merged named stream is
`verdict-provenance-reproducibility` (W26), merged via PR #38 at `bfb2d2d`;
`static-analysis-artifact-precision` is the active offline/static stream;
SAP-0 through SAP-4 are complete and SAP-5 is next.
Containment safety remains the next product/release execution gate in
[documents/active-work/v1-roadmap.md](documents/active-work/v1-roadmap.md) §4;
the measurement stream does not displace it.

Canonical state and history:

- [documents/REFACTOR_STATUS.md](documents/REFACTOR_STATUS.md)
- [documents/phase.json](documents/phase.json)
- [documents/POST_POC_BACKLOG.md](documents/POST_POC_BACKLOG.md)
- [documents/REFACTOR_OPTIMIZATION.md](documents/REFACTOR_OPTIMIZATION.md)
