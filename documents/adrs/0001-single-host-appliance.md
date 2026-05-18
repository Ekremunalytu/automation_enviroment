# ADR 0001: Single-Host Appliance Model

- Status: Accepted
- Date: 2026-04-15

## Context

ExTrace currently behaves like a single-operator analysis appliance, not a
distributed control plane. The catalog/storage path is stable enough, but the
dynamic-analysis path still couples web orchestration, planner behavior, job
state, executor control, and report interpretation too tightly.

The current refactor needs a clear operating model so boundary cleanup does not
accidentally drift into premature microservice design or distributed runtime
work.

## Decision

For this refactor cycle, ExTrace is explicitly treated as:

- a single-host appliance
- a single active sandbox analysis system
- a Docker-isolated executor model
- a boundary-first refactor, not a deployment-count expansion

The following rules apply:

- sandbox execution remains isolated in Docker
- no new dependencies are introduced without explicit approval
- the first refactor steps prioritize contracts, planner boundaries, and durable
  job metadata before heavier runtime changes
- microservice decomposition is out of scope for this phase

## Consequences

### Positive

- the refactor has a stable target shape
- early work can focus on smaller, safer boundaries
- Week 1-4 changes stay aligned with the existing deployment model

### Negative

- some heavier runtime corrections are intentionally deferred
- single-host assumptions remain explicit until later expansion work is
  justified

### Follow-On

- reviewed after Week 4 closure on `2026-04-20`; the single-host appliance
  model still stands for W5 security work
- promote any post-W5 runtime changes only if the repo is stable enough to
  absorb them
- ADR 0011 (`2026-05-17`, W15-6) cites this ADR as one of three load-bearing
  preconditions for keeping catalog endpoints unauthenticated. Any future
  amendment dropping the single-host scope (multi-tenant or hosted SaaS
  shift) must also revisit ADR 0011 — the trusted-environment assumption
  for the catalog router is encoded as a cross-link there.
