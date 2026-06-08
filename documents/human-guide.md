# ExTrace Human Documentation

This is the readable entry point for people who want to understand, run, or
review ExTrace. It lives alongside the agent-optimized planning docs in
`documents/`, but you do not need to read those first.

Start here:

1. [How ExTrace Works](how-it-works.md)
   - What the system is, what evidence it collects, and where the major
     components fit.
2. [Operator Quickstart](operator-quickstart.md)
   - Local development, local sandbox operation, and the air-gapped Podman
     deployment path.
3. [API And Request Flows](api-and-flows.md)
   - Main backend flows and route reference.
4. [Risk Register](risks.md)
   - Accepted tradeoffs, security posture, and known operational limits.
5. [Air-gapped Podman Deployment](../deploy/podman/README.md)
   - Full guide for running ExTrace on a headless Fedora Server with rootful
     Podman and no target-side internet.

## Which Docs Should I Read?

| Goal | Read |
|---|---|
| Understand the product | [how-it-works.md](how-it-works.md) |
| Run ExTrace locally | [operator-quickstart.md](operator-quickstart.md) |
| Check backend request flow or routes | [api-and-flows.md](api-and-flows.md) |
| Deploy to an offline Fedora Server | [../deploy/podman/README.md](../deploy/podman/README.md) |
| Review accepted risks | [risks.md](risks.md) |
| Modify the codebase | [../AGENTS.md](../AGENTS.md) and [AGENT_CONTEXT.md](AGENT_CONTEXT.md) |
| Investigate current roadmap state | [REFACTOR_STATUS.md](REFACTOR_STATUS.md) |
| Pick up deferred work | [POST_POC_BACKLOG.md](POST_POC_BACKLOG.md) |
| Check architecture decisions | [adrs/](adrs/) |

## Human Guides Vs Agent Docs

Everything lives under `documents/`, but it serves two audiences:

- **Human guides** — this file plus `how-it-works.md`, `operator-quickstart.md`,
  `api-and-flows.md`, and `risks.md`. Readable, narrative, and the best first
  read for a new reviewer or operator.
- **Agent and canonical docs** — `README.md` (the agent routing map),
  `AGENT_CONTEXT.md`, `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, the ADRs,
  runbooks, lane docs, and phase trackers. Precise, dense, and pinned by tests.
  They are the source of truth for detailed state but are not the best first
  read.

When the two ever disagree, the canonical docs — and ultimately the code and
tests — win.
