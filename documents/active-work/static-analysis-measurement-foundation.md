# Static Analysis Measurement Foundation

`Last Updated: 2026-07-30`

`Status: PROPOSED — next static-analysis development iteration, ready for owner review. This document does not open a stream; documents/phase.json.active_stream remains null.`

`Parent: static-analysis-improvement-roadmap.md Increment A / SAR-0 + SAR-1 measurement foundation.`

`Product-order boundary: containment safety remains the next product execution gate. This iteration is limited to offline/static contracts, declawed fixtures, measurement, coverage honesty, and the minimum conclusion-policy decision needed to prevent partial scans from reading clean.`

`Owner: ekrem`

`Indicative duration: 3 weeks for one maintainer`

## 1. Iteration Goal

Establish the evidence needed to improve ExTrace static detection without
guessing:

1. define what the static analyzer inspected and what it missed;
2. measure every current rule against labeled, safe fixtures;
3. separate tuning data from release holdout data;
4. make file, byte, parser, time, and finding limits visible;
5. make repeated evaluation deterministic despite audit ULIDs and timestamps;
6. prevent a schema-valid partial scan from being presented as clean;
7. produce a baseline that the following artifact-precision increment can
   compare against.

This iteration does not attempt to improve every rule. It creates the contract,
corpus, evaluator, and coverage evidence that make later precision, taint,
dependency, native, archive, and policy work defensible.

## 2. Starting Evidence

The implemented baseline is:

- 26 production in-house rules across `s1` through `s20`;
- 16 advisory Semgrep rules;
- schema-first Pydantic v2 static findings and tool records;
- a hardened `automation_static_analyzer` container with no network,
  non-root execution, dropped capabilities, and bounded resources;
- CRITICAL findings and `extrace.s2.typosquat` as the implemented blocker
  posture;
- VSIX SHA-256 provenance shared with the analysis job and dynamic report.

The live ESLint 3.0.34 run proved report and SHA-256 provenance but produced
seven MEDIUM findings, including known context errors:

- PNG assets were classified as native binaries;
- README/license HTTP links were classified as suspicious runtime endpoints.

Repository inspection also identified coverage-honesty gaps:

- manifest parsing reads at most 1 MiB and degrades malformed or unreadable
  content to an empty manifest;
- the file walk stops at 50,000 regular files without a report-level cap reason;
- in-house text rules read the first 1 MiB and ignore undecodable bytes;
- Semgrep skips targets above 1,000,000 bytes without making the result partial;
- Semgrep mapping stops at 200 findings without exposing the cap;
- Semgrep blanket-excludes `node_modules` and `*.min.js`;
- `StaticDetectionReport.partial` is not considered by the severity-only gate,
  so a findings-free partial report can receive the clean `ALLOW` reason;
- finding ULIDs vary by run and therefore cannot serve as determinism keys.

These behaviors are baseline cases to measure before changing detector
semantics.

## 3. Iteration Boundaries

### In Scope

- evaluation and corpus contracts;
- rule/capability inventory;
- deterministic rule-bundle and finding fingerprints;
- 10-15 declawed tuning/holdout fixtures;
- a hardened-container evaluation runner;
- TP/FP/FN/TN, precision, recall, noise, runtime, and coverage metrics;
- explicit skip/limit/parse/budget accounting;
- partial-conclusion design decision and the smallest approved honesty fix;
- JSON and Markdown baseline artifacts;
- focused tests, architecture guards, documentation, and reproducible commands.

### Out Of Scope

- new blocker promotion;
- S3/S5 precision fixes before the baseline artifact is recorded;
- new taint, CodeQL, YARA, Trivy, OSV, ML, or model integration;
- live malware, weaponized samples, real C2 endpoints, or host execution;
- dynamic sandbox execution or threat-directed hints;
- database persistence or an Alembic migration;
- operator disposition;
- AI provider calls, vector storage, or RAG;
- broad UI redesign.

No dependency is introduced without a separate explicit owner decision. The
default implementation uses the standard library, current Pydantic contracts,
the existing in-house runtime, and the already pinned Semgrep installation.

## 4. Success Outcomes

At close-out, ExTrace can answer:

- Which rule and ruleset version produced this result?
- Which files and bytes were discovered, selected, read, parsed, skipped, or
  truncated?
- Why was a file skipped?
- Were critical `main` or `browser` entrypoints parsed?
- Did a file, finding, parser, time, or memory bound reduce coverage?
- How many tuning and holdout samples are TP, FP, FN, or TN?
- Which rule families create benign WARN noise?
- Does the same VSIX and rule bundle produce the same normalized findings,
  coverage, metrics, and gate conclusion?
- Can a partial/error/timeout result still be presented as clean?
- What is the measured baseline for Increment B?

## 5. Sub-Iteration Slate

| ID | Package | Deliverable | Depends on | Exit evidence |
|---|---|---|---|---|
| SMF-0 | Baseline freeze | rule inventory, capability matrix, current-limit register, ruleset fingerprint | current main | machine-readable inventory and reviewed Markdown |
| SMF-1 | Evaluation contracts | corpus manifest, expected-result, metric, and run-result contracts | SMF-0 vocabulary | schema validation tests |
| SMF-2 | Safe starter corpus | 10-15 declawed tuning/holdout fixtures and safety metadata | SMF-1 | manifest parity, hash, provenance, and safety tests |
| SMF-3 | Evaluation runner | container-only evaluator, normalized comparison, JSON/Markdown output | SMF-1, SMF-2 | deterministic focused evaluation |
| SMF-4 | Coverage instrumentation | aggregate and per-tool file/byte/parser/limit accounting | SMF-1 | every implemented bound has a visible fixture |
| SMF-5 | Conclusion honesty | owner decision plus approved contract/gate handling for incomplete reports | SMF-4 | partial-without-findings cannot read clean |
| SMF-6 | Metrics and PR gate | confusion matrices, noise/runtime/coverage deltas, small PR corpus | SMF-3, SMF-4 | repeatable baseline command and delta report |
| SMF-7 | Container and full validation | container isolation, adversarial bounds, security and full suite | SMF-3 through SMF-6 | all required gates pass |
| SMF-8 | Close-out and handoff | baseline artifact, decisions, risks, Increment B input | SMF-7 | canonical docs and state reconciled |

SMF IDs are stable within this tracker. They do not create a new top-level
roadmap stream or renumber Stream 6 goals.

## 6. SMF-0 — Baseline Freeze

### Rule Inventory

For every in-house and Semgrep rule record:

```text
rule_id
rule_version
rule_lifecycle
tool
severity
confidence
categories
gate_effect
artifact_roles
positive_tests
negative_tests
known_false_positives
known_blind_spots
runtime_budget
owner
```

The inventory must be generated or parity-checked against the live registries
so documentation cannot silently drift from code.

### Ruleset Fingerprint

Compute a stable fingerprint from:

- normalized in-house rule identity/version/lifecycle metadata;
- the exact Semgrep YAML bytes or a canonical YAML representation;
- the pinned Semgrep version;
- evaluator schema version.

Do not include timestamps, generated ULIDs, absolute host paths, or unordered
dictionary serialization.

### Baseline Artifacts

Suggested outputs:

```text
output/static-evaluation/baseline.json
output/static-evaluation/baseline.md
output/static-evaluation/rule-inventory.json
```

`output/` remains ignored and local. The repository stores contracts, safe
fixtures, tests, and small expected summaries—not live marketplace VSIX files or
operator reports.

## 7. SMF-1 — Evaluation Contracts

### Suggested Package Boundary

```text
packages/analysis_contracts/static_evaluation/
  __init__.py
  corpus.py
  expectations.py
  metrics.py
  result.py
```

This package remains framework-agnostic. It must not import `workflows`,
`executor`, `appcore`, `ui`, or `packages.analysis_engine`.

### Corpus Sample Contract

Minimum fields:

```text
schema_version
sample_id
relative_path
sha256
split
label
families
variant
platform
provenance
safety_state
expected_gate
must_fire
may_fire
must_not_fire
expected_coverage
expected_inconclusive_reasons
notes
```

Required semantics:

- `split` is `tuning` or `holdout`;
- `label` distinguishes malicious-behavior, vulnerable, benign, and coverage-
  control cases without collapsing these axes;
- hashes are lowercase canonical SHA-256;
- relative paths cannot escape the corpus root;
- every sample has a safety state and provenance note;
- `must_fire`, `may_fire`, and `must_not_fire` rule IDs are unique and known;
- contradictory expectations fail validation before any sample is opened.

### Evaluation Result Contract

Capture:

```text
evaluation_id
schema_version
rules_bundle_fingerprint
corpus_manifest_sha256
started_at
completed_at
sample_results
rule_metrics
family_metrics
coverage_summary
runtime_summary
determinism_summary
errors
```

Timestamps and evaluation IDs are audit metadata. Deterministic comparison uses
the normalized result payload with volatile fields excluded.

## 8. SMF-2 — Safe Starter Corpus

### Fixture Matrix

| Family | Positive or adversarial case | Required benign/control case |
|---|---|---|
| Artifact role | renamed executable/archive containing inert marker bytes | genuine PNG/font/database containing NUL bytes |
| Network context | cleartext URL reaching an inert network-call marker | README/license/changelog URL |
| Dependency scope | entrypoint-reachable modified vendored module | ordinary lockfile-aligned dependency |
| Obfuscation | invisible Unicode plus decoder plus inert sink marker | localized Unicode and benign minified source |
| Credential flow | synthetic secret source to inert webhook marker | secret read used only locally |
| Download flow | response to write to inert spawn marker | download to cache without execution |
| Webview | message payload to inert command/filesystem marker | strict schema and allowlisted dispatch |
| Workspace trust | workspace-controlled value to inert process marker | trust guard and fixed argument map |
| Manifest | malformed, non-object, oversized, missing entrypoint | valid small manifest and entrypoint |
| Coverage | parser error, target cap, finding cap, budget stop | fully parsed small extension |
| Dormancy/platform | delayed/platform-gated inert capability chain | legitimate platform-specific feature |

### Safety Rules

- No fixture connects to a network endpoint.
- No fixture contains a working shell, destructive command, credential, or
  executable payload.
- Process/network/filesystem sinks are inert source-text markers and are never
  executed.
- Real malware bytes and live VSIX archives are forbidden.
- Corpus evaluation happens in the hardened static container.
- High-cardinality limits use dependency injection or controlled test doubles
  instead of committing 50,000 files or 200 findings.
- Every fixture SHA-256 is checked before evaluation.

### Tuning And Holdout

The first corpus may be small, but the split is mandatory:

- tuning fixtures are visible during rule and evaluator implementation;
- holdout expectations are not used to tune a rule in the same change;
- a future larger benign corpus can extend the manifest without changing metric
  semantics;
- aggregate metrics always report tuning and holdout separately.

## 9. SMF-3 — Evaluation Runner

### Runtime Boundary

Suggested implementation:

```text
static_runtime/evaluation.py
scripts/static_eval.py
```

The host command prepares explicit read-only corpus and writable output mounts,
then invokes the existing static-analyzer container. It never imports or
executes sample code on the host.

### Evaluator Flow

1. Validate the corpus manifest before opening sample contents.
2. Resolve and contain every relative path under the corpus root.
3. Verify sample SHA-256 and safety metadata.
4. Select tuning, holdout, or both through an explicit CLI argument.
5. Run the same production static runner and rule bundle used by the product.
6. Normalize findings into stable fingerprints.
7. Compare `must_fire`, `may_fire`, `must_not_fire`, expected gate, and expected
   coverage.
8. Calculate rule, family, sample, coverage, and runtime metrics.
9. Write schema-valid JSON.
10. Derive Markdown from the JSON result; JSON remains the machine source of
    truth.

### Deterministic Finding Fingerprint

Use normalized fields such as:

```text
vsix_sha256
rule_id
rule_version
artifact_role
normalized_relative_path
evidence_type
normalized_match_shape
source_sink_shape
```

Do not use the generated finding ULID, timestamp, absolute path, raw secret, or
line number alone. Line numbers may be supporting metadata.

### Command Shape

Candidate interface:

```text
make static-eval CORPUS=tests/static_corpus SPLIT=tuning
make static-eval CORPUS=tests/static_corpus SPLIT=holdout
```

The exact flags may change during implementation, but the command must be
non-interactive, deterministic, container-only, and suitable for CI.

## 10. SMF-4 — Coverage Instrumentation

### Shared Coverage Contract

Prefer an additive `StaticScanCoverage` contract:

```text
files_discovered
files_selected
files_eligible
files_scanned
files_parsed
files_skipped_by_reason
bytes_considered
bytes_read
manifest_status
critical_entrypoints
critical_entrypoints_parsed
file_cap_reached
finding_cap_reached
unsupported_formats
coverage_reasons
```

Per-tool records carry tool-local coverage. The report carries the conservative
aggregate and the reasons that affect conclusion quality.

### Required Skip Reasons

Use a bounded enum or validated identifiers, including:

```text
file_cap
target_too_large
text_truncated
undecodable
unsupported_suffix
parser_error
manifest_missing
manifest_malformed
manifest_too_large
critical_entrypoint_missing
critical_entrypoint_unparsed
rule_timeout
tool_timeout
tool_error
finding_cap
budget_stop
excluded_inventory_only
```

Skip-detail paths are normalized and capped. Aggregate counts remain available
even when the evidence-path list is truncated.

### Instrumentation Targets

Likely touched files:

```text
packages/analysis_contracts/static_detection/report.py
static_runtime/context.py
static_runtime/rules/_common.py
static_runtime/semgrep_runner.py
static_runtime/static_runner.py
```

Schema changes land before producer changes. Generated UI contracts are updated
only if the shared API report exposes the additive coverage object during this
iteration.

## 11. SMF-5 — Conclusion Honesty

### Decision Required

ADR 0016 currently defines `ALLOW/WARN/BLOCK`. Before changing the conclusion
contract, the owner chooses and records one of:

1. partial-without-blocker becomes `WARN` with a dedicated coverage cause; or
2. a separate aggregate `INCONCLUSIVE` conclusion is introduced while raw
   severity and terminal blocker behavior remain unchanged.

The preferred product semantics are a separate conclusion-quality state, but
the implementation decision must account for existing API/UI contracts and
avoid conflating a detector rule with a tool failure.

### Invariants

- Do not create a fake finding or fake rule ID.
- CRITICAL and the promoted HIGH blocker behavior remain unchanged.
- An unreadable/schema-invalid report continues to fail closed.
- Partial/error/timeout cannot carry the clean allow reason.
- Dynamic low-quality or skipped execution cannot erase the static coverage
  warning.
- Historical raw findings and reports are not rewritten.

### Required Compatibility Review

If a shared conclusion enum changes, inspect:

```text
packages/analysis_contracts/static_detection/gate.py
appcore/contracts/schema_defs/static_analysis_bundle.py
workflows/marketplace/static_analysis.py
workflows/marketplace/analysis_reports.py
scripts/generate_ui_contracts.py
ui/src/lib/adapters/job.ts
ui/src/features/simulation/SimulationPage.tsx
```

No DB migration is expected because the static report is persisted as a file,
but this assumption must be rechecked against the implementation diff.

## 12. SMF-6 — Metrics And Quality Gate

### Metric Definitions

For supported families:

```text
precision = TP / (TP + FP)
recall = TP / (TP + FN)
false_positive_rate = FP / (FP + TN)
```

When a denominator is zero, emit `not_applicable` rather than zero or a
misleading perfect score.

Report:

- sample-level and finding-level confusion matrices;
- per-rule and per-family precision/recall;
- benign packages producing WARN;
- actionable findings per benign package;
- partial/inconclusive rate and reason distribution;
- files/bytes discovered, parsed, scanned, and skipped;
- p50/p95 per-tool and total runtime;
- deterministic comparison mismatches;
- misses and unsupported platform/format cases;
- static layer contribution when a comparable dynamic label exists, without
  overstating the small initial corpus.

### Provisional Acceptance Targets

These are iteration gates, not product-wide claims:

- partial/incomplete scan presented as clean: 0%;
- blocker false positives in reviewed benign fixtures: 0%;
- verdict/fingerprint variance for identical input and rule bundle: 0%;
- schema-valid JSON and Markdown parity: 100%;
- corpus hash/provenance/safety validation: 100%;
- supported-family holdout recall candidate: at least 85%;
- unexplained p95 runtime regression: no more than 20%;
- p95 actionable findings per benign package candidate: no more than one.

The last three remain provisional until the baseline is large enough to be
meaningful.

### PR And Full-Corpus Modes

- **PR mode:** small tuning/control subset, schema and determinism, no network.
- **Release mode:** full tuning plus holdout evaluation.
- **Manual marketplace mode:** bounded benign validation only; reports stay
  ignored under `output/`.

## 13. Tests

### New Focused Tests

Suggested files:

```text
tests/static_runtime/test_evaluation_manifest.py
tests/static_runtime/test_evaluation_metrics.py
tests/static_runtime/test_evaluation_determinism.py
tests/static_runtime/test_evaluation_partial_results.py
tests/static_runtime/test_scan_coverage.py
tests/static_runtime/test_semgrep_coverage_limits.py
tests/workflows/marketplace/test_static_partial_gate.py
tests/architecture/test_static_evaluation_import_boundary.py
tests/architecture/test_static_corpus_manifest_parity.py
```

### Required Cases

- manifest path traversal and duplicate sample ID rejected;
- invalid/missing hash, provenance, or safety state rejected;
- contradictory `must_fire`/`must_not_fire` rejected;
- unknown rule expectation rejected;
- tuning and holdout remain separate;
- zero-denominator metrics become `not_applicable`;
- finding order and ULID differences do not change normalized metrics;
- same input/ruleset three times produces the same fingerprint and conclusion;
- file, target, text, finding, timeout, and parser bounds are visible;
- critical entrypoint skip makes coverage incomplete;
- partial-without-findings cannot receive a clean allow reason;
- output path remains contained;
- fixture content is never executed on the host;
- `static_runtime` and evaluation contracts preserve import boundaries.

### Verification Commands

```text
.venv/bin/pytest -q tests/static_runtime/
.venv/bin/pytest -q tests/workflows/marketplace/test_static_partial_gate.py
.venv/bin/pytest -q tests/architecture/
make test-security
make static-eval CORPUS=tests/static_corpus SPLIT=tuning
make static-eval CORPUS=tests/static_corpus SPLIT=holdout
make check-all
git diff --check
```

Markdown lint and link validation are required for all changed roadmap,
contract, and runbook documentation.

## 14. Pull Request And Commit Slices

Keep the implementation serial in one worktree and one Docker stack:

1. **SMF-0:** inventory, fingerprint vocabulary, baseline-limit register.
2. **SMF-1:** Pydantic evaluation contracts and contract tests.
3. **SMF-2:** safe corpus manifest, fixtures, hash/safety/parity tests.
4. **SMF-3:** evaluator, normalization, JSON/Markdown output.
5. **SMF-4:** additive coverage contract and producer instrumentation.
6. **SMF-5:** ADR decision and conclusion-honesty implementation.
7. **SMF-6:** Make target, PR/release evaluation modes, metrics.
8. **SMF-7:** container, security, architecture, and full validation.
9. **SMF-8:** close-out evidence and Increment B handoff.

Do not combine a new detector, severity change, blocker promotion, dependency,
and shared-contract change. No blocker or rule-behavior tuning belongs in this
iteration.

## 15. Three-Week Execution Schedule

### Week 1 — Contracts And Safe Inputs

- SMF-0 baseline inventory and fingerprint.
- SMF-1 corpus/result contracts.
- SMF-2 initial tuning and holdout manifests.
- Contract, parity, path, hash, and safety tests.
- Owner review of the partial-conclusion decision options.

Week 1 gate: schema and safe corpus validate; no detector behavior changes.

### Week 2 — Evaluator And Coverage

- SMF-3 container-only evaluator.
- Deterministic normalized findings and metrics.
- SMF-4 file/byte/parser/cap coverage instrumentation.
- JSON/Markdown baseline.
- Focused static runtime and architecture tests.

Week 2 gate: every implemented bound is visible and repeated evaluation is
stable.

### Week 3 — Conclusion Honesty And Close-Out

- SMF-5 approved conclusion-policy change.
- SMF-6 PR/release modes and final metrics.
- Full tuning and holdout run.
- Security, architecture, container, and `make check-all` gates.
- SMF-8 baseline evidence and Increment B handoff.

Week 3 gate: no incomplete result reads clean; the measured baseline is
reproducible and reviewable.

## 16. Risks And Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Small corpus gives unstable percentages | false confidence | report counts with rates; mark thresholds provisional |
| Holdout leaks into tuning | inflated recall | split in contract and PR review; report separately |
| Coverage schema bloats reports | storage/UI noise | aggregate counts plus capped detail; additive contract |
| Real high-cardinality fixtures bloat Git | maintenance and runtime cost | controlled test doubles for caps |
| Determinism check compares ULIDs/timestamps | false variance | normalized fingerprint excludes volatile fields |
| Partial policy becomes a fake security rule | misleading cause | dedicated coverage reason/conclusion state |
| `node_modules` scope explodes runtime | p95 regression | inventory now; deep scan deferred to Increment B |
| Contract change breaks UI/API adapters | product regression | schema-first compatibility review and generated-contract tests |
| Evaluator diverges from production runner | invalid baseline | invoke the same production static runner/ruleset |
| Roadmap work appears to open a stream | lifecycle drift | keep `phase.json.active_stream=null` until explicit activation |

## 17. Iteration Acceptance Bar

The iteration closes only when:

- all SMF-0 through SMF-8 deliverables are complete or explicitly deferred with
  an owner-approved reason;
- every production rule appears in the inventory;
- the starter corpus is safe, hashed, provenance-labeled, and split;
- JSON is the canonical evaluation result and Markdown matches it;
- three identical runs have zero normalized result and conclusion variance;
- all current limits produce visible coverage reasons;
- partial/error/timeout cannot be presented as clean;
- no severity, blocker, or S3/S5 detector behavior changed;
- no new dependency or DB migration landed without explicit approval;
- security, architecture, container, focused, and full repository gates pass;
- baseline results and known blind spots are recorded;
- Increment B receives a concrete before/after precision target.

## 18. Increment B Handoff

The next package, `static-analysis-artifact-precision`, consumes:

- rule and capability inventory;
- stable ruleset/finding fingerprints;
- tuning and holdout corpus;
- baseline confusion matrices;
- PNG and documentation-URL regression cases;
- dependency/minified inventory counts;
- skip and parser coverage;
- runtime baseline;
- known S3/S5 and artifact-role false positives.

Increment B may then change artifact classification and S3/S5 behavior while
proving:

- benign WARN noise decreases;
- renamed executable and runtime network fixtures still fire;
- holdout recall does not regress;
- runtime remains inside the approved budget.

## 19. Activation And State

Merging this roadmap to `main` approves the planning artifact, not execution.
To start implementation later:

1. owner confirms the partial-conclusion option and iteration scope;
2. create the implementation branch;
3. update `documents/phase.json.active_stream` and canonical state docs together
   if the iteration is formally opened as the active named stream;
4. keep containment safety as the release/product execution gate;
5. implement SMF-0 first and preserve this tracker as the acceptance source.
