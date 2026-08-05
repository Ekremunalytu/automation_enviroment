# Static Analysis Improvement Roadmap

`Last Updated: 2026-08-05`

`Status: ACTIVE ROADMAP — Increment A (SMF-0..SMF-8) plus the Increment B SAP-0..SAP-4 baseline merged via PR #40. SAP-5 is branch-published and SAP-6 is implementation-complete locally; Increment B remains active, branch-ready, and unmerged. Later increments, dependencies, detector/blocker changes, and AI work still require their normal owner decision and ADR process.`

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

The 2026-07-30 research pass identified two product-honesty risks now addressed
by the active measurement foundation:

- a schema-valid report with `partial=true` no longer reaches a clean `ALLOW`;
  blocker-free incomplete runs conclude `INCONCLUSIVE`;
- bounded file, byte, target, finding, parser, and time stops now carry coverage
  accounting. Intentional Semgrep vendor/minified exclusions remain visible but
  are not alone a degraded tool state because the in-house production rules
  retain bounded text coverage.

These are not reasons to remove resource bounds or scan every bundled file with
every rule. They require an explicit scan-coverage contract, deterministic
two-tier inspection, and an inconclusive/coverage-aware product conclusion.

This plan refines the Stream 6 goals in
[`v1-roadmap.md`](v1-roadmap.md) and
[`POST_POC_BACKLOG.md`](../POST_POC_BACKLOG.md). Its `SAR-*` IDs are stable
implementation slices within this proposal; they do not open a stream or
replace the canonical backlog goal IDs. The `AI-*` labels are optional,
proposal-local research phases and likewise do not create a new canonical
stream or backlog goal.

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
| AI-0 | Provider-free AI contract and evaluation fixtures | 1-2 weeks | SAR-0 contract vocabulary |
| AI-1 | Opt-in shadow analyst | 2-3 weeks | SAR-1 labels, owner ADR/dependency approval |
| AI-2 | Operator analyst assistant | 2-3 weeks | AI-1 eval gate; never a gate dependency |

SAR-0 through SAR-5 are static/offline work and may be prepared independently
of the dynamic containment implementation. Live malicious-corpus execution
and SAR-6 product claims remain gated by disposable per-analysis sandboxes and
fail-closed egress from the main v1 roadmap.

The AI track is optional and outside the static gate. AI-0 may prepare local
contracts and recorded fixtures without a provider, network, model, or new
dependency. AI-1 and AI-2 require a separate owner decision and ADR; neither is
on the critical path for measured static detection.

## 4. SAR-0 — Baseline And Measurement Contract

### Scope

- Inventory every rule: identity/version, lifecycle, severity/confidence,
  categories, gate effect, artifact scope, tests, and blind spots.
- Record the Semgrep version and rule-bundle fingerprint.
- Run repeatability checks: the same VSIX and rule bundle three times must
  produce the same sorted finding fingerprints and gate decision. Finding ULIDs
  remain audit/event identities and are not the repeatability key.
- Capture current tool duration, total duration, files discovered, files
  eligible, files read, files skipped, parse errors, and budget stops.
- Preserve the ESLint 3.0.34 PNG and documentation-URL cases as named
  regression expectations without committing the ignored live VSIX/report.

Deliver a corpus-manifest schema, JSON/Markdown baseline, capability matrix,
and glossary separating sample/finding and raw/adjusted metrics.

### Implemented Coverage-Honesty Baseline

These implemented behaviors are frozen as named baseline cases:

| Surface | Current bound/behavior | Required observable state |
|---|---|---|
| Manifest | reads at most 1 MiB; malformed/unreadable/non-object becomes an empty manifest | `manifest_status`, bytes read, reason, critical-entrypoint impact |
| File walk | stops after 50,000 regular files | discovered/selected count, `file_cap_reached`, deterministic selection policy |
| In-house text scan | reads up to 32 MiB per file and ignores undecodable bytes | bytes read, truncated/undecodable status, affected rule families |
| Semgrep targets | scans targets up to 32 MiB; larger targets remain bounded | skipped count/paths by role; partial when a critical entrypoint is skipped |
| Semgrep result mapping | stops after 200 mapped findings | `finding_cap_reached`, omitted count when known, partial status |
| Decision gate | `BLOCK > INCONCLUSIVE > WARN > ALLOW` | partial/error/timeout can never carry a clean allow reason |
| Dependency scope | excludes `node_modules` and `*.min.js` from Semgrep while in-house rules retain bounded text coverage | inventory for all files; deep scan selection and skip rationale |

Bounds stay in place. The change is that every bounded stop becomes measurable
and its effect on conclusion quality is explicit.

### Scan-Coverage Contract

Prefer an additive shared contract such as `StaticScanCoverage` rather than
tool-specific ad hoc dictionaries. At minimum it records:

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

Per-tool records explain local coverage; the report carries the conservative
aggregate. Paths in skip details remain bounded, normalized, and capped so the
coverage record cannot become a second report-bloat vector.

The owner selected a separate aggregate `INCONCLUSIVE` conclusion without
changing raw rule severity or the terminal blocker path. ADR 0016 records the
precedence and dynamic-continuation semantics.

Do not manufacture a fake rule ID to carry a tool-coverage failure.

### Exit Gate

- Every production rule has a positive test, a negative test, and documented
  ownership.
- Identical inputs produce deterministic rule ordering, finding fingerprints,
  coverage accounting, and gate outcome.
- Every enforced file/byte/time/finding cap has a fixture and a visible reason.
- A schema-valid partial report cannot be presented with a clean allow reason.
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

### Starter Corpus

The first 10-15 fixtures should cover the existing false positives and the
highest-value supported flows:

| Family | Positive/adversarial fixture | Required benign lookalike |
|---|---|---|
| Artifact role | renamed PE/ELF or archive with safe inert bytes | real PNG/font/database containing NUL bytes |
| Network context | runtime cleartext endpoint reaching a network sink | README/license/changelog URL |
| Dependency | entrypoint-reachable modified vendored module | ordinary lockfile-aligned `node_modules` sample |
| Obfuscation | invisible Unicode plus decoder plus inert dynamic-sink marker | localized Unicode and minified benign source |
| Credential flow | synthetic secret source to inert webhook sink | secret read with local-only use |
| Download-to-exec | response-to-write-to-inert-spawn marker | download-to-cache without execution |
| Webview | message data to inert command/filesystem sink | strict message schema and allowlisted dispatch |
| Workspace trust | workspace-controlled value to inert process sink | trusted-workspace guard and fixed argument map |
| Coverage | malformed/oversized manifest, parse failure, budget/target cap | fully parsed small extension |
| Dormancy/platform | safe delayed/platform-gated marker chain | legitimate platform-specific capability |

No fixture contains a working C2 endpoint, credential, destructive command, or
executable payload. High-cost limit cases use controlled test doubles where the
real cardinality would make ordinary tests wasteful.

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
- Corpus provenance and safety classification validate before the evaluator
  opens sample contents.

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

### Two-Tier Dependency And Bundle Scan

Replace blanket deep-scan exclusion with two bounded tiers:

1. **Inventory tier for every file:** normalized path, role, size, hash,
   extension/magic agreement, first bytes, dependency ownership, manifest or
   entrypoint reachability, and version-diff state.
2. **Deep-analysis tier:** first-party code plus dependency/minified artifacts
   selected because they are entrypoint-reachable, newly changed, provenance-
   inconsistent, extension-mismatched, loader-linked, or otherwise suspicious.

Ordinary vendored bundles remain lower-confidence and deduplicated. The report
must say why a dependency was deeply scanned, inventory-only, or skipped. This
recovers current attack surface without turning `node_modules` into unbounded
Semgrep noise.

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
| Workspace-to-process | Workspace configuration, task/debug field, file content | Process/shell; trust guard plus fixed command/argument map |
| Webview-to-capability | `onDidReceiveMessage` payload | Command, filesystem, process, network; schema plus allowlist |

Every taint rule needs a positive flow, sanitizer-negative, unrelated-token
negative, and at least one indirection/evasion variant.

The first implementation remains bounded and intraprocedural where required by
the pinned Semgrep engine. Unsupported cross-file flow is reported as a known
coverage limit; it is not approximated by raising token-co-occurrence severity.

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
- `extensionPack`, `extensionDependencies`, `extensionKind`, platform/
  architecture gates, and silent background activation.

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
  extension-pack edges, entrypoints, capabilities, obfuscation, or opaque
  bundles;
- removed source paired with newly added binary/minified content;
- bundled dependency bytes that diverge from lockfile/source provenance;
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

ATT&CK models malicious behavior; CWE/OSV model vulnerability and dependency
risk. A package may be vulnerable without being malicious, or malicious without
a known CVE. Preserve both axes through measurement, API, export, and UI.

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

## 13. First Three Implementation Increments

### Increment A — `static-analysis-measurement-foundation`

Indicative duration: 2-3 weeks. This is the recommended first package.
The executable next-iteration tracker is
[`static-analysis-measurement-foundation.md`](static-analysis-measurement-foundation.md).

Deliverables:

- additive corpus-manifest and evaluation-result contracts;
- rule/capability inventory and deterministic rule-bundle fingerprint;
- `StaticScanCoverage` design plus instrumentation for the current limits;
- 10-15 declawed tuning/holdout fixtures;
- container-only evaluator producing JSON and Markdown;
- TP/FP/FN/TN, precision/recall, benign WARN/noise, coverage, p50/p95, and
  determinism metrics;
- an explicit test and design decision for partial-without-findings;
- named ESLint PNG and documentation-URL regression expectations.

Candidate implementation map:

```text
packages/analysis_contracts/static_detection/coverage.py
packages/analysis_contracts/static_evaluation/
static_runtime/evaluation.py
scripts/static_eval.py
tests/static_corpus/manifest.json
tests/static_runtime/test_evaluation_manifest.py
tests/static_runtime/test_evaluation_metrics.py
tests/static_runtime/test_evaluation_determinism.py
tests/static_runtime/test_evaluation_partial_results.py
```

Exact paths may be adjusted during implementation to preserve the existing
minimal-image import boundary. Evaluation writes file artifacts; no database
migration is part of Increment A.

Increment A explicitly does not:

- change rule severity, confidence, lifecycle, or blocker membership;
- change S3/S5 matching behavior before recording the baseline;
- introduce a parser, model, provider, CVE database, or external corpus;
- execute a fixture on the host;
- persist evaluation rows in the application database.

### Increment B — `static-analysis-artifact-precision`

Indicative duration: 2-3 weeks after A.

Deliverables:

- role and magic/header classification;
- explicit opaque/native/archive/WASM distinctions;
- S3 and S5 context fixes;
- inventory-tier dependency and minified-bundle coverage;
- entrypoint/reachability-based deep-scan selection;
- source-map/vendor deduplication;
- before/after evaluation report proving the benign-noise reduction without
  supported-family recall regression.

### Increment C — `static-analysis-bounded-taint`

Indicative duration: 3-4 weeks after A and B.

Deliverables:

- Semgrep taint rules for path, credential, download-to-exec, workspace, and
  webview flows;
- source, sink, sanitizer, and propagator evidence;
- parser/unsupported-entrypoint coverage;
- positive, sanitizer-negative, unrelated-token, and evasion fixtures for each
  flow;
- advisory-only rollout and measured comparison against current search rules.

Do not begin with Trivy, CodeQL, broad YARA/regex batches, or ML while
measurement and artifact precision remain unresolved.

## 14. Prioritized Detection Backlog

### Tier A — Highest Product Value

| Priority | Detection family | Required evidence shape | Initial posture |
|---:|---|---|---|
| 1 | Workspace/config/URI/webview input to process, code, or filesystem | source-to-sink plus missing trust/allowlist/containment guard | advisory |
| 2 | Secret/credential to network or webhook | secret source and reachable egress sink | advisory |
| 3 | Download to write/load/execute | response/file propagation into process or loader | advisory |
| 4 | Webview capability abuse | scripts/CSP/resource/message context plus dangerous sink | advisory |
| 5 | Manifest capability graph | suspicious conjunction, not a single capability | risk score/advisory |
| 6 | Dependency and version-diff anomaly | new edge/bytes/capability plus provenance or reachability | review priority |
| 7 | Native/WASM/archive loader relationship | format identity plus loader/platform/reference | advisory |
| 8 | Invisible code and decoder chain | Unicode density plus reconstruction plus dynamic/process/network sink | advisory |
| 9 | Dormancy/platform/locale gating | gate plus delayed/decrypted/high-risk capability | advisory |

No Tier A family becomes a blocker in the increment that introduces it.

### Tier B — Useful After Tier A Measurement

- lifecycle script and Git/URL dependency risk;
- language server, debugger, task provider, authentication provider, and remote
  extension-host capability analysis;
- clipboard/authentication input to webhook or raw socket;
- extension-pack/dependency graph deltas;
- cross-file and cross-extension write relationships;
- publisher history and unusual release cadence, when provenance is available;
- OSV/CVE inventory as a separate vulnerability axis with freshness evidence.

### Tier C — Keep Low-Confidence Or Avoid

- bare `eval`, `child_process`, network API, crypto address, or minified-file
  presence;
- domain, hash, IOC, file extension, NUL byte, or entropy alone;
- CVE presence as proof of maliciousness;
- undocumented AI score or AI-only blocker;
- broad regular-expression batches without benign negatives and holdout
  measurement.

## 15. Tool Adoption Strategy

| Tool/capability | Decision | Admission evidence | Main constraint |
|---|---|---|---|
| In-house Python | Keep for bounded manifest, inventory, format, and conjunction logic | existing isolation and unit baseline | avoid duplicating parsers/dataflow engines |
| Semgrep taint | Use first | SAR-1 baseline and per-flow fixtures | bounded/intraprocedural and parser coverage |
| CodeQL | Defer to measured cross-file miss | concrete Semgrep miss, license/runtime/image/DB design | operational and image cost |
| YARA | Defer to offline signature use case | versioned bundle, benign negatives, rollback | signature staleness and FP |
| Trivy/OSV | Separate vulnerability track | DB freshness/provenance and not-applicable semantics | CVE is not maliciousness |
| CycloneDX | Candidate dependency/SBOM representation | deterministic completeness and relationship mapping | do not replace internal report contracts |
| SARIF | Export adapter later | stable internal schema and result mapping | not the internal source of truth |
| TLSH/fuzzy hash | Defer | labeled same-family/version utility | collision/threshold calibration |
| ML/LLM | Gate-external only | AI evals, data policy, shadow evidence | nondeterminism and prompt injection |

Every new executable dependency needs explicit approval, a pinned version,
container/image impact, offline/no-network posture, failure semantics,
observability, update/rollback plan, and measured incremental contribution.

## 16. AI Integration Roadmap

### Boundary Decision

The static analyzer and decision gate never depend on a model provider,
external network, or nondeterministic model response. AI consumes an already
validated, persisted, deterministic report through a separate optional service.
There is no AI-to-gate, AI-to-executor, shell, URL-open, or arbitrary-tool path.

```text
VSIX
  -> hardened no-network static analyzer
  -> canonical report + deterministic gate
  -> persistence
  -> redacted deterministic AI context pack
  -> optional provider adapter
  -> strict Pydantic output validation + policy guard
  -> advisory analyst view
```

### Allowed AI Tasks

- explain findings using cited evidence already present in the report;
- cluster/deduplicate related findings without deleting raw records;
- identify missing evidence, likely benign context, and analyst questions;
- summarize manifest, dependency, and version-diff risk;
- propose allowlisted dynamic-hint candidates for policy/human approval;
- in development, propose candidate rules plus positive, negative, and evasion
  fixtures; never merge or promote them automatically.

### Forbidden AI Tasks

- change raw severity, confidence, gate decision, or blocker membership;
- claim that silence proves safety;
- execute extension content or follow instructions found in source, comments,
  README, reports, logs, or VSIX metadata;
- open extension-supplied URLs or invoke shell/network tools;
- upload the full VSIX or secrets by default;
- generate arbitrary dynamic commands or unbounded hint values;
- become required for activation coverage, static analysis, or job completion.

Extension contents are prompt-injection input. Treat every snippet as quoted
data, never as system/developer instructions.

### AI Context Pack

The provider-facing input is a new minimal contract, not the raw report dump:

```text
schema_version
vsix_sha256
rules_bundle_fingerprint
report_fingerprint
coverage_summary
manifest_capability_summary
artifact_role_summary
normalized_findings
bounded_redacted_evidence
version_diff_summary
operator_question
```

Every snippet remains bounded and redacted. The pack excludes known secret
values, raw binaries, archives, full source trees, host paths, credentials,
Docker state, and unrelated reports.

### AI Output Contract

Use strict structured output with:

```text
summary
risk_themes
finding_explanations
missing_evidence
benign_context_hypotheses
review_questions
dynamic_hint_candidates
rule_candidate_notes
citations
refusal_or_error
```

Each factual statement cites a finding fingerprint and evidence reference.
Unknown or insufficient evidence is explicit. Pydantic rejects extra fields,
unknown hint types, raw commands, URLs outside the existing evidence set, and
oversized output.

### AI Audit Record

Record:

- provider and pinned model snapshot;
- prompt/template version and hash;
- input context hash and report/VSIX SHA-256;
- output schema version;
- provider settings that affect reproducibility;
- token use, latency, cost, refusal, validation error, and retry count;
- user opt-in state and data-retention mode;
- final human disposition, when supplied.

Do not store hidden chain-of-thought or use it as audit evidence.

### AI Evaluation Gate

Keep AI metrics separate from detector recall:

- schema-valid output rate;
- evidence-citation validity and evidence faithfulness;
- unsupported-claim rate;
- analyst disposition agreement;
- dangerous false-downgrade rate;
- prompt-injection success rate;
- secret/redaction leakage rate;
- latency and per-report cost;
- repeatability at the pinned snapshot.

Candidate acceptance targets before AI-2:

- dangerous false downgrade: 0%;
- prompt-injection tool/action success: 0%;
- known-secret leakage: 0%;
- valid citation references: 100%;
- schema-valid output: at least 99% before retry;
- no AI failure changes or blocks the deterministic job result.

These are safety bars, not claims of model correctness. Model selection is made
on a held-out ExTrace evaluation set across at least two cost/quality tiers;
never by choosing the newest model without measurement.

### AI Delivery Phases

| Phase | Scope | Exit gate |
|---|---|---|
| AI-0 | Local contracts, deterministic context-pack builder, recorded output fixtures, injection/redaction tests; no provider | contracts and evals pass with provider disabled |
| AI-1 | Explicit opt-in shadow calls; no UI verdict weight; compare against human labels | safety targets met, retention/cost documented, owner accepts ADR |
| AI-2 | Advisory analyst summary, review questions, rule/hint candidates | human-in-the-loop path verified; no write/gate/tool authority |

Do not add vector storage or RAG in AI-0/AI-1. Reports are structured and small;
introduce retrieval only if measured context limits or cross-report research
needs justify its data lifecycle and access-control cost.

## 17. Threat And Standards Research Register

Primary sources to revisit when rules or contracts change:

| Area | Source | Roadmap use |
|---|---|---|
| VS Code trust | [Workspace Trust](https://code.visualstudio.com/api/extension-guides/workspace-trust) | workspace-controlled source and trust-guard semantics |
| Manifest surface | [Extension Manifest](https://code.visualstudio.com/api/references/extension-manifest) | entrypoints, dependencies, packs, capabilities |
| Activation | [Activation Events](https://code.visualstudio.com/api/references/activation-events) | silent/background and provider activation graph |
| Webview | [Webview API](https://code.visualstudio.com/api/extension-guides/webview) | CSP, resource roots, messages, sanitization |
| Browser extension host | [Web Extensions](https://code.visualstudio.com/api/extension-guides/web-extensions) | `browser` entrypoint and Node API availability |
| Taint semantics | [Semgrep glossary](https://semgrep.dev/docs/writing-rules/glossary) | source/sink/sanitizer/propagator and engine limits |
| Cross-file R&D | [CodeQL JavaScript data flow](https://codeql.github.com/docs/codeql-language-guides/analyzing-data-flow-in-javascript-and-typescript/) | later measured interprocedural candidate |
| Evaluation | [OWASP Benchmark](https://owasp.org/www-project-benchmark/) | TP/FP/FN/TN and speed methodology |
| Evaluation corpus | [NIST SARD](https://samate.nist.gov/SARD/) | labeled-case methodology, not a VSIX corpus substitute |
| Invisible code | [MITRE ATT&CK T1027.018](https://attack.mitre.org/techniques/T1027/018/) | precise behavior mapping for invisible-code chains |
| Supply chain | [CycloneDX specification](https://cyclonedx.org/specification/overview/) | dependency relationships and completeness |
| Vulnerability schema | [OSV schema](https://ossf.github.io/osv-schema/) | separate dependency-vulnerability axis |
| Provenance | [SLSA provenance](https://slsa.dev/spec/v1.2/provenance) | artifact origin and build relationship vocabulary |
| Result exchange | [SARIF 2.1](https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html) | later export adapter |
| Current campaign | [Koi GlassWorm fifth wave](https://www.koi.ai/blog/glassworm-hits-mcp-5th-wave-with-new-delivery-techniques) | extension-pack/dependency and staged-version abuse |
| Disguised payloads | [ReversingLabs fake-image research](https://www.reversinglabs.com/blog/malicious-vs-code-fake-image) | magic/header, vendored dependency, fake extension |
| Unicode campaign | [Aikido GlassWorm research](https://www.aikido.dev/blog/glassworm-returns-unicode-attack-github-npm-vscode) | invisible encoding and dynamic reconstruction |
| Structured AI | [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) | strict provider-output contract |
| AI evaluation | [OpenAI Evals](https://developers.openai.com/api/docs/guides/evals) | labeled held-out AI evaluation |
| AI data controls | [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data) | retention, opt-in, minimization decision |
| Prompt injection | [Designing agents to resist prompt injection](https://openai.com/index/designing-agents-to-resist-prompt-injection/) | untrusted-content boundary and action isolation |

Threat blogs seed hypotheses and declawed fixtures; they do not directly create
blockers, IOC truth, or product claims. Reconfirm source date, affected
versions, and primary evidence when implementing a rule.

## 18. Delivery Governance

### Required Owner Decisions

| Decision | Latest responsible point | Required artifact |
|---|---|---|
| Partial conclusion representation | before SAR-0 contract lands | ADR 0016 amendment or scoped successor ADR |
| Shared coverage contract fields | before implementation | schema review and UI/API compatibility note |
| New parser/tool dependency | before dependency change | ADR, pin, image/cost/rollback assessment |
| New blocker | after holdout evidence | ADR amendment, version, zero-FP proof, rollback |
| Persist evaluation/AI records | before DB change | storage lane review and Alembic migration |
| External AI provider | before AI-1 | AI ADR, dependency approval, data/retention policy |
| Threat-directed dynamic hints | before SAR-6 | cross-boundary design note/ADR and containment proof |

### Pull Request Slicing

Keep reviewable boundaries:

1. contracts and fixtures;
2. evaluator and metrics;
3. coverage instrumentation;
4. gate/conclusion honesty after the owner decision;
5. artifact classifier;
6. individual rule families;
7. AI contracts/evals;
8. AI provider adapter only after approval.

Do not combine a new detector, severity increase, blocker promotion, dependency,
and contract migration in one PR.

### Rollback

Every rule/tool package preserves:

- prior rule bundle and version;
- before/after corpus report;
- feature or lifecycle downgrade path where appropriate;
- additive contract compatibility;
- no deletion or rewriting of historical raw findings;
- a documented way to disable an optional provider/tool without disabling the
  deterministic in-house analysis.

## 19. Milestone View

| Milestone | Packages | Product evidence |
|---|---|---|
| M1 — Honest baseline | SAR-0 | every bound visible; partial cannot read clean; deterministic fingerprints |
| M2 — Measured detector | SAR-1 | tuning/holdout corpus, confusion matrices, runtime and coverage |
| M3 — Usable precision | SAR-2 | PNG/docs regressions fixed with no measured recall loss |
| M4 — Flow-aware analysis | SAR-3 | source-to-sink evidence and visible parse coverage |
| M5 — Supply-chain depth | SAR-4, SAR-5 | capability/dependency/diff/native/archive evidence |
| M6 — Safe targeting | containment gate, SAR-6 | allowlisted targeted hints and measured layer contribution |
| M7 — Calibrated policy | SAR-7 | lifecycle and blocker decisions backed by holdout data |
| M8 — Optional AI analyst | AI-0 through AI-2 | advisory help passes injection, leakage, citation, and HITL gates |

## 20. Cross-Cutting Invariants

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
- AI remains optional, gate-external, tool-less, bounded, redacted, and
  provider-disabled by default.
- Source code, reports, logs, manifests, and AI context are adversarial data,
  never instructions.

## 21. Planning State

Increment B is active as
`documents/phase.json.active_stream = static-analysis-artifact-precision`,
with Increment A plus SAP-0 through SAP-4 merged via PR #40. SAP-5 reachability
and exact source-map/vendor deduplication is complete and published on the
feature branch but is not merged. SAP-6 full delta and close-out is
implementation-complete locally; the unmerged Increment B stream is
branch-ready. Containment safety remains the next product/release gate. Increment C
stays separately reviewable and requires its own activation. AI-0 may be
planned as a provider-free contract exercise, but AI-1 does not begin without
an explicit owner/ADR/data-policy decision.
