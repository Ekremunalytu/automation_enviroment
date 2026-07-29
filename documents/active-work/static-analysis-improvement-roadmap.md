# Static Analysis Improvement Roadmap

`Last Updated: 2026-07-29`

`Status: PROPOSED — non-active planning document. documents/phase.json.active_stream remains null. Opening an implementation stream, changing gate policy, adding dependencies, or changing shared contracts still requires the normal owner decision and ADR process.`

`Scope: Stream 6 measured-catch-rate and static-primary/threat-directed-dynamic strategy. Product execution order remains containment safety first, then measured detection.`

`Owner: ekrem`

## 1. Purpose

Turn ExTrace's static-analysis prototype into a measured, explainable,
product-grade primary analysis layer without replacing the implemented
architecture.

Preserve the current base: 26 production in-house rules, 16 advisory Semgrep
rules, schema-first findings with partial/provenance records, the hardened
no-network analyzer container, and the block-and-warn gate. CRITICAL findings
block; `extrace.s2.typosquat` remains the only promoted HIGH blocker.

The primary gap is calibration, not rule count. ESLint 3.0.34 proved
report/provenance but exposed context false positives: PNG assets read as
native and documentation URLs as runtime endpoints. Measure first, improve
precision second, then add depth and policy weight.

This plan refines the Stream 6 goals in
[`v1-roadmap.md`](v1-roadmap.md) and
[`POST_POC_BACKLOG.md`](../POST_POC_BACKLOG.md). Its `SAR-*` IDs are stable
implementation slices within this proposal; they do not open a stream or
replace the canonical backlog goal IDs.

## 2. Target Outcome

The target static layer should:

1. classify source, dependency, documentation, asset, native, and unknown
   artifacts by context;
2. measure recall, false positives, incompleteness, runtime, and layer
   contribution;
3. add bounded taint, manifest/dependency/diff, and native/WASM/archive depth;
4. emit auditable, allowlisted hints for threat-directed dynamic analysis;
5. promote blockers only with holdout evidence and an ADR audit trail.

ExTrace remains an evidence-backed risk assessment; static silence does not
prove an extension clean.

## 3. Delivery Sequence

For one maintainer, plan 18-24 weeks; the first two increments should improve
precision within 4-6 weeks.

| Package | Theme | Indicative duration | Product dependency |
|---|---|---:|---|
| SAR-0 | Freeze baseline and measurement contract | 1 week | provenance spine shipped |
| SAR-1 | Labeled corpus and evaluation runner | 2-3 weeks | SAR-0 |
| SAR-2 | Artifact context and false-positive reduction | 2-3 weeks | SAR-1 |
| SAR-3 | AST and bounded taint analysis | 3-4 weeks | SAR-1, SAR-2 |
| SAR-4 | Manifest, dependency, provenance, version diff | 3-4 weeks | SAR-1 |
| SAR-5 | Native, WASM, archive, offline signatures | 3-4 weeks | SAR-1, SAR-2 |
| SAR-6 | Threat-directed dynamic-plan handoff | 3 weeks | containment safety, SAR-3/4/5 |
| SAR-7 | Policy calibration and continuous quality | 2-3 weeks + ongoing | SAR-1 through SAR-6 |

SAR-0 through SAR-5 are static/offline work and may be prepared independently
of the dynamic containment implementation. Live malicious-corpus execution
and SAR-6 product claims remain gated by disposable per-analysis sandboxes and
fail-closed egress from the main v1 roadmap.

## 4. SAR-0 — Baseline And Measurement Contract

### Scope

- Inventory every rule: identity/version, lifecycle, severity/confidence,
  categories, gate effect, artifact scope, tests, and blind spots.
- Record the Semgrep version and rule-bundle fingerprint.
- Run repeatability checks: the same VSIX and rule bundle three times must
  produce the same sorted finding identities and gate decision.
- Capture current tool duration, total duration, files discovered, files
  eligible, files read, files skipped, parse errors, and budget stops.
- Preserve the ESLint 3.0.34 PNG and documentation-URL cases as named
  regression expectations without committing the ignored live VSIX/report.

Deliver a corpus-manifest schema, JSON/Markdown baseline, capability matrix,
and glossary separating sample/finding and raw/adjusted metrics.

### Exit Gate

- Every production rule has a positive test, a negative test, and documented
  ownership.
- Identical inputs produce deterministic rule ordering and gate outcome.
- No severity, confidence, or blocker-policy change is included in SAR-0.

## 5. SAR-1 — Labeled Corpus And Evaluation Runner

### Corpus Design

Keep rule tuning separate from the final score:

- **tuning:** visible positive and benign examples used during rule work;
- **holdout:** hidden-from-tuning examples used for release acceptance;
- **adversarial variants:** minified, renamed, split-file, encoded,
  platform-gated, delayed, and benign-lookalike variants of supported families.

Each manifest carries stable ID, SHA-256, label/family/variant/platform,
provenance and safety state, expected gate, `must_fire`/`may_fire`/
`must_not_fire`, and expected blind or inconclusive reasons.

Live malware never enters ordinary host-side tests. Fixtures stay declawed and
must follow the existing malicious-fixture safety policy. Evaluation occurs in
the hardened static container.

### Metrics

Produce JSON and Markdown for per-rule/family precision and recall,
sample/finding false positives, benign WARN/noise, partial reasons, p50/p95
runtime, layer contribution, misses, and platform/format blind spots.

Add a focused command such as:

```text
make static-eval CORPUS=tests/static_corpus
```

The exact command name may be finalized during implementation; it must not
execute corpus contents on the host.

### Exit Gate

- Tuning and holdout results are separate.
- A rule-level confusion matrix is reproducible.
- Partial/error/timeout results cannot be counted as a clean pass.
- Baseline deltas are visible before a PR changes rule behavior.

## 6. SAR-2 — Artifact Context And Precision

### Artifact Roles

Classify before rules run: manifest, first-party/dependency runtime,
documentation/license/test, asset/source-map/configuration, native/WASM,
archive, or unknown.

Classification should combine relative path, extension, magic/header,
manifest entrypoint reachability, dependency ownership, and bounded content
inspection. Extension alone is not authoritative.

### Precision Work

- Replace the S3 "unknown suffix plus NUL byte equals native" behavior with
  format-aware classification for images, fonts, databases, archives, PE,
  ELF, Mach-O, and WASM.
- Separate "opaque binary" from "native executable."
- Correlate native severity with a loader/reference where possible.
- Distinguish documentation/license/changelog URLs from runtime endpoint
  literals.
- Treat a URL reaching `fetch`, `axios`, `http`, `net`, `WebSocket`, or a
  comparable sink differently from an inert prose link.
- Deduplicate repeated findings originating from source maps or vendored
  bundles.
- Do not blanket-ignore dependencies: mark ownership and lower confidence
  unless runtime reachability or a dangerous lifecycle/loader relationship
  raises it again.

### Exit Gate

- ESLint PNG and documentation URL regressions no longer produce actionable
  S3/S5 findings.
- A renamed PE/ELF fixture and a runtime cleartext endpoint still fire.
- Malicious holdout recall does not regress.
- Gate policy remains unchanged while benign WARN noise falls measurably.

## 7. SAR-3 — AST And Bounded Taint

Start with Semgrep taint mode because Semgrep is already pinned in the
hardened container. Do not add CodeQL or another heavy engine until the
existing tool's measured limits justify it.

### First Flows

| Flow | Sources | Sinks / sanitizer |
|---|---|---|
| Path traversal | Request path, URI, webview, command argument | Filesystem access; canonical containment is the sanitizer |
| Credential exfiltration | Environment, configuration, secret store/files | Fetch, HTTP, WebSocket, webhook |
| Download-to-exec | Response body or downloaded file | Child process, shell, PowerShell, dynamic loader |

Every taint rule needs a positive flow, sanitizer-negative, unrelated-token
negative, and at least one indirection/evasion variant.

### Parse Coverage

Report files discovered, eligible, parsed, skipped, unsupported, oversized,
and failed. A parser failure or unsupported critical entrypoint must make the
tool/report partial rather than silently allowing.

### Exit Gate

- Loose token co-occurrence fixtures remain silent.
- True source-to-sink fixtures fire with source and sink evidence.
- Parse coverage is operator-visible.
- Runtime stays within the existing static-analysis budget.
- No new taint rule becomes a blocker in the same increment that introduces
  it.

## 8. SAR-4 — Manifest, Dependency, Provenance, Version Diff

### Manifest Capability Graph

Model relationships among:

- activation events, `main`/`browser` entrypoints, contributed commands and
  their `when` clauses;
- views, tasks, debuggers, authentication providers, webviews, URI handlers,
  workspace-trust posture, and lifecycle scripts;
- platform/architecture gates and silent background activation.

Prefer conjunctions such as silent startup plus credential access plus
background network capability over treating each capability as malicious.

### Dependency Inventory

Parse lockfiles and bundled dependency trees offline. Record ownership,
version/source, lifecycle scripts, Git/URL dependencies, native/WASM content,
and manifest/artifact inconsistencies. Do not add Trivy/CVE policy until DB
freshness and provenance have an audited design.

### Version Diff

Compare the same publisher/name against a prior analyzed version:

- newly added activation events, scripts, domains, executables, dependencies,
  entrypoints, capabilities, obfuscation, or opaque bundles;
- removed source paired with newly added binary/minified content;
- publisher/identity anomalies.

A diff is a risk and review-priority signal, not proof of malice. Missing
history must be explicit (`no_baseline_version`), not interpreted as no change.

### Exit Gate

- Capability graphs and dependency inventories are deterministic.
- Same-version self-diff is empty.
- Missing lockfile/history and unsupported formats are explicit.
- Version-diff contribution is measured on tuning and holdout samples.

## 9. SAR-5 — Native, WASM, Archive, Offline Signatures

### Bounded Artifact Inspection

Begin with dependency-free or already-approved parsers for:

- PE, ELF, Mach-O, WASM, ZIP/archive, shebang scripts, and MSI recognition;
- architecture, entry/import metadata, executable state, size, and hash;
- loader/reference relationships in extension source.

Add higher-value correlations: native artifact plus `dlopen`, platform gate
plus `.node`, WASM plus network/process bridge, runtime archive extraction,
download plus executable write/spawn, and embedded RMM configuration.

### YARA And Later Tools

YARA remains a candidate for offline signature and conjunction rules, but
requires an ADR amendment, dependency approval, rule-bundle versioning, benign
negative coverage, and rollback. A signature match alone does not
automatically imply BLOCK.

Trivy, TLSH, CodeQL, and MSI parsing remain follow-ups. Enroll them only after
a measured use case and update/freshness design; ADR 0016 already reserves the
future tool/evidence slots.

### Adversarial Bounds

Enforce nested depth, extracted bytes, file count, compression ratio,
per-file reads, parser timeout, path traversal, and link policy. No inspected
artifact executes.

### Exit Gate

- Images and generic opaque binaries are not mislabeled as native executables.
- Renamed executables are recognized.
- Archive-bomb fixtures terminate inside budget.
- Parser degradation is partial/inconclusive, never clean.
- Container network/capability boundaries remain unchanged.

## 10. SAR-6 — Threat-Directed Dynamic Handoff

This package crosses static, marketplace-planner, and executor boundaries and
requires its own design note or ADR. It starts only after the containment gate
supports safe live execution.

Static output may emit allowlisted hint types:

```text
trigger_command
trigger_uri
seed_secret
observe_domain
accelerate_time
route_platform
watch_file
watch_process
```

Each hint carries rule IDs, priority, and a bounded value. It never carries
arbitrary code or shell commands.

Examples:

- `globalState` dormancy -> seed state or advance virtual time;
- hardcoded endpoint -> observe through controlled proxy/sinkhole;
- credential access -> seed a synthetic credential;
- command/URI contribution -> prioritize the matching trigger;
- `win32` guard -> route to a compatible runner or report unavailable;
- download cradle -> intensify file/process/network observation.

The planner records hint requested/applied/skipped and a reason. Broad UI
stimulation remains fallback evidence rather than silently replacing a failed
targeted plan.

### Exit Gate

- Only allowlisted hint types cross the boundary.
- Missing platform/containment support produces an explicit skip reason.
- Targeted-plan contribution is measured against broad fallback.
- Low dynamic run quality cannot override static WARN or produce a clean
  aggregate.

## 11. SAR-7 — Policy Calibration And Continuous Quality

Keep distinct:

- severity: impact if the behavior is malicious;
- confidence: strength/specificity of the evidence;
- coverage: how much relevant content was inspected;
- verdict: aggregate decision;
- run quality: reliability/completeness of this execution.

### Blocker Promotion

Any new HIGH blocker or change to CRITICAL semantics requires:

- an ADR amendment and auditable commit;
- holdout-corpus evidence;
- zero blocker false positives across the reviewed benign corpus;
- explicit rule-version change and rollback plan;
- no unresolved partial/parser blind spot that could make the decision
  misleading.

### Finding Identity And Disposition

Add a stable finding fingerprint based on rule ID, normalized artifact role,
normalized path, source/sink or stable match shape—not line number alone.

Operator disposition later annotates but never deletes findings or rewrites
raw verdicts. B8 uses raw metrics. A vulnerability axis remains separate from
maliciousness and needs explicit owner/shared-contract approval.

### Rule Lifecycle

Use a measured progression:

```text
experimental -> candidate -> production -> deprecated
```

A production rule needs a threat hypothesis, positive and multiple negative
fixtures, an evasion variant, severity/confidence rationale, category mapping,
version, runtime measurement, corpus metrics, UI catalog metadata, security
test enrollment, and error/partial behavior coverage.

## 12. Quality Gates

### Required Test Layers

Run rule and false-positive units, contracts, import/container boundaries,
determinism and adversarial bounds, a small PR corpus, full holdout evaluation,
and bounded manual marketplace validation.

### Provisional Targets

Baseline SAR-1 results must be recorded before permanent numeric policy is
approved. Initial candidate targets are:

- blocker false-positive rate: 0%;
- partial/incomplete scan reported as clean: 0%;
- verdict variance for identical input and rule bundle: 0%;
- supported-family holdout recall: at least 85%;
- unexplained p95 runtime regression: no more than 20%;
- p95 actionable findings per benign package: no more than one.

The last three are calibration candidates, not current product claims.

### Per-Increment Verification

- focused rule and evaluation tests;
- `make test-security` with new security files enrolled explicitly;
- static runtime and container tests;
- `make check-all` with required services;
- `git diff --check`;
- Markdown lint/link checks for changed documentation.

## 13. First Two Implementation Increments

| Increment | Scope | Outcome |
|---|---|---|
| A — measurement | Baseline, corpus evaluator, tuning/holdout split, ESLint expectations | Rule noise and layer contribution become measurable |
| B — precision | Artifact roles/magic, S3/S5 context, deduplication | Measured user-visible precision gain |

Do not begin with Trivy, CodeQL, broad YARA/regex batches, or ML while
precision and measurement remain unresolved.

## 14. Cross-Cutting Invariants

- Static parsing stays inside the hardened no-network container.
- `static_runtime` keeps its minimal import boundary.
- No dependency is introduced without explicit approval.
- Tool output maps into schema-first contracts.
- Adversarial paths, reports, source, archives, and binaries stay bounded.
- Partial/error/timeout states never silently become ALLOW.
- Gate policy is not a mutable operator/config shortcut.
- Raw findings and measurement are never deleted by disposition.
- External CVE/IOC data requires freshness/provenance evidence.
- SAR-0 through SAR-5 use file artifacts; persistence needs separate approval.

## 15. Planning State

This plan does not declare work started:
`documents/phase.json.active_stream` remains `null` and containment safety is
the next gate. Open Increment A, then B; keep later packages separately
reviewable.
