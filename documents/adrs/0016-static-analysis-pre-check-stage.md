# ADR 0016 — Static Analysis Pre-Check Stage

- Status: Proposed (design intent recovered from the abandoned
  `extrace-static` branch; resumed serially on branch `static`. Flips to
  Accepted + implemented at the stream close-out ES-5.)
- Date: 2026-05-29
- Authors: ekrem + Claude
- Driving stream: Static Analysis Pre-Check Stream — ES-0 doc-reconcile
- Related: ADR 0002 (threat model), ADR 0003 (detection taxonomy), ADR
  0005 (packages charter), ADR 0008 (container packaging), ADR 0013
  (container isolation baseline)
- Source: `documents/active-work/extrace-static-stream-handoff.md` —
  frozen design intent preserved after the `extrace-static` branch was
  abandoned 2026-05-28. The four decisions below were vetted in operator
  review on that branch; this ADR re-homes them so the trail is not lost.

## Context

The analysis pipeline today is **dynamic-only**: every analyze job pays
1–5 minutes of Docker sandbox spin (`automation_executor`, VS Code +
Playwright) even when an extension is obviously malicious. A large class
of adversarial markers is observable **without executing the extension**:

- `package.json` manifest red flags (`activationEvents: ["*"]` wildcard,
  suspicious permission combinations, missing or generic publisher)
- Typosquatting against popular-extension identities
- Embedded native binaries (`.node` / `.so` / `.dylib`)
- JavaScript patterns such as `eval` / `Function` / `child_process` /
  `vm.runInContext` over attacker-controlled input

A pre-execution static stage adds three things the dynamic stage cannot:

1. **Cheap reject path** for known-bad extensions — terminal rejection
   before any sandbox spin.
2. **Defense-in-depth** — catches markers a malicious extension can
   suppress, delay, or environment-fingerprint at activation time (the
   class ADR 0002 §3 + ADR 0015 treat as evasion).
3. **Detection-surface expansion** orthogonal to the dynamic threat
   model and the ADR 0003 detection taxonomy.

This stage was first built on the `extrace-static` branch (ES-0 + ES-1
landed), then abandoned 2026-05-28 because parallel-worktree development
on a shared-Docker project cost more operationally than it saved. The
design was preserved in the handoff doc cited above and is now resumed
serially on a single branch named `static`, one Docker stack.

## Decision

### 1. Block-and-warn semantics

The static stage gates the dynamic stage:

- **CRITICAL findings → new terminal job status `rejected_static`.** The
  dynamic stage is skipped and downstream steps are marked `skipped`.
- **LOW / MEDIUM findings → warn.** The dynamic stage proceeds and the
  warnings ride along in the combined bundle.
- One curated HIGH-confidence blocker is promoted to BLOCK via a
  frozenset, not config: `_PROMOTED_HIGH_BLOCKERS =
  frozenset({"extrace.s2.typosquat"})`. Changes to this set require an
  amendment to this ADR plus a commit audit trail — never a silent
  config flip.

`rejected_static` is **terminal** and stays out of
`ACTIVE_ANALYSIS_JOB_STATUSES`; the partial unique index
`uq_analysis_jobs_single_active` is not widened to include it.

### 2. Separate hardened container `automation_static_analyzer`

Static analysis runs in a dedicated Docker service — NOT inline in
`install_extension` and NOT inside the existing executor. The security
envelope:

- `network_mode: "none"`, `cap_drop: [ALL]`, `no-new-privileges: true`
- non-root user, no `cap_add`, no `docker.sock` mount
- `mem_limit: 1g`, `cpus: 1.0`
- read-only mount of the extensions input
  (`/extensions-input:ro`); read-write mount of results (`/results:rw`)

The container parses untrusted manifest JSON, walks an untrusted file
tree, and (from ES-4) runs Semgrep over untrusted JavaScript; isolating
that work is the primary security surface, consistent with ADR 0013.

### 3. Schema-first contract landing

Pydantic contracts land **before** any tool runner. Tools map INTO the
schema; the schema is never bent to fit a tool's output quirks. This
prevents the failure mode of "schema evolves to fit Semgrep → forced
refactor when YARA / Trivy enroll in v2". The static-detection contracts
reuse the dynamic `Severity` / `Confidence` / `RuleLifecycle` /
`AdversaryClass` enums **by identity**, not as parallel clones, per the
ADR 0005 packages charter.

### 4. MVP tool stack: in-house Python rules + Semgrep

The MVP ships two tools writing into one `StaticDetectionReport`:

- **In-house Python rules** — 6 production rules across `s1` (manifest),
  `s2` (typosquat, reusing the dynamic `a3_typosquat` matcher), `s3`
  (file-tree heuristics) namespaces.
- **Semgrep** — 4 custom YAML rules for the JS patterns above, run with
  `--metrics=off` and no external network.

Deferred to v2, each via a separate amendment to this ADR + its own
sub-iter: YARA (embedded-artifact + base64-decoder co-occurrence), Trivy
filesystem CVE scanning (needs a DB-freshness audit-trail design), TLSH
fuzzy-hash identity, and CodeQL interprocedural taint. The v2 evidence
types and tool slots are nonetheless **pre-shipped onto the schema
Literals at ES-1** (zero runtime cost, no forced migration when v2
enrolls).

### Job step contract

The canonical analysis-job step order gains two steps,
`static_analysis` and `decision_gate`, extending the order to seven. To
deliver the cheap-reject value, the static steps run **before** the
sandbox is spun; the producer (`empty_job_steps`) and the step Literal
are extended together in the same commit (ES-3b) to avoid the validator
regression documented in the handoff.

## Consequences

### Positive

- Known-bad extensions are rejected without paying for sandbox spin.
- Detection surface expands into pre-execution markers that resist the
  evasion classes of ADR 0002 §3 / ADR 0015.
- Schema-first + by-identity enum reuse keeps the static and dynamic
  detection contracts coherent and migration-stable.
- The hardened container keeps untrusted-file parsing off the host and
  off the executor, consistent with ADR 0013.

### Negative

- A second Docker image + service to build, run, and keep version-pinned
  (Semgrep wheel pin is load-bearing for rule semantics).
- Static heuristics carry false-positive risk; mitigated by the
  block-and-warn gradient (only CRITICAL + the one promoted typosquat
  BLOCK; everything else WARN/ALLOW) and per-rule fire/silent tests.
- A determined adversary can still defeat purely static markers; the
  dynamic stage remains the primary behavioral surface, and the two
  compose into a `CombinedAnalysisBundle`.

### Operational notes

- Feature-flagged via `settings.static_analysis.ENABLED`, OFF by default
  until the stream close-out (ES-5) flips it after smoke evidence passes.
- New security-lane tests must be enrolled into the explicit file list in
  the `test-security` Makefile target; it does not auto-discover.

## Implementation Roadmap (ES-0 → ES-5)

Stable sub-iter IDs; tracked in
`documents/active-work/static-analysis-pre-check-stream.md`.

- **ES-0** — this ADR (Proposed) + lane doc + stream tracker + ADR
  existence arch test.
- **ES-1** — schema landing: static-detection contracts, combined
  bundle, `rejected_static` terminal status, `static_report_path` ORM
  column + Alembic migration. Does NOT touch the step Literal.
- **ES-2** — hardened `automation_static_analyzer` container scaffold +
  runtime stub.
- **ES-3a** — the 6 in-house Python rules + static runner.
- **ES-3b** — decision gate + orchestrator wiring; the 7-step order +
  `empty_job_steps` extension land here in one commit.
- **ES-4** — Semgrep integration (version-pinned wheel + 4 custom rules).
- **ES-5** — close-out: UI surfaces, `AnalyzeResponse` extension, smoke
  evidence, feature-flag flip; this ADR flips to Accepted + implemented.

## Alternatives Rejected

**Option A — run static checks inline in `install_extension`.**
Rejected: parsing untrusted files on the host / inside the executor
violates the ADR 0013 isolation posture; a dedicated `network_mode:
none` container is the correct boundary.

**Option B — let the tools define the schema (schema-after-tools).**
Rejected: Semgrep's JSON shape would leak into the contract and force a
migration when YARA / Trivy enroll. Schema-first with mappers is the
disciplining principle.

**Option C — single-tool MVP (in-house only, or Semgrep only).**
Rejected: in-house rules cover manifest / identity / file-tree cheaply
but miss dataflow JS patterns; Semgrep covers JS patterns but is
heavyweight for manifest checks. The two compose for breadth at low
incremental cost.

**Option D — resume on a parallel `extrace-static` worktree.**
Rejected: this is the documented lesson from the 2026-05-28 abandonment.
Parallel-worktree streams on a shared-Docker project add `container_name`
collisions, port juggling, and two-stack overhead that exceed the
parallelism benefit. Resume serially on one branch (`static`), one stack.

## References

- `documents/active-work/extrace-static-stream-handoff.md` — frozen
  design intent + the four locked decisions + the ES-1 regression note.
- `documents/adrs/0002-threat-model.md` §3 — evasion classes the static
  stage hardens against.
- `documents/adrs/0003-detection-taxonomy.md` — finding taxonomy the
  static findings extend.
- `documents/adrs/0005-packages-charter.md` — packages boundary +
  by-identity enum reuse.
- `documents/adrs/0013-container-isolation-baseline.md` — isolation
  posture the static container inherits.
- `AGENTS.md` — no-external-services rule (Semgrep runs offline,
  `--metrics=off`).
- Semgrep CLI reference — `https://semgrep.dev/docs/cli-reference`.
