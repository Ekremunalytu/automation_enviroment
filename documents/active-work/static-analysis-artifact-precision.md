# Static Analysis Artifact Precision

`Last Updated: 2026-08-05`

`Status: ACTIVE — the SMF foundation plus SAP-0 through SAP-4 and the
production-bundle precision follow-up merged to main via PR #40. The merged
baseline includes the static-only Reports presentation correction described in
section 3, the Reports-integrated Static analysis inspection tab, and the Rules
whitelist visibility/normalization follow-up. SAP-5 is complete locally but not
pushed or merged; SAP-6 is next.`

`Parent: static-analysis-improvement-roadmap.md Increment B / SAR-2.`

`Merge boundary: PR #40 carried the committed SMF foundation and SAP-0..SAP-4
baseline into main. SAP-5 is complete on the local feature branch and remains
unpublished. The stream remains active for SAP-6 full delta and close-out.`

`Product-order boundary: containment safety remains the next mandatory
product/release gate. This stream is offline/static and does not claim safe
dynamic execution.`

## 1. Goal

Reduce benign static WARN noise without weakening supported detection:

1. classify artifact role and bounded magic/header evidence before applying
   file-context-sensitive rules;
2. stop treating every unknown-suffix NUL-bearing file as a native executable;
3. separate documentation URLs from runtime endpoint literals;
4. recover bounded dependency and minified-bundle visibility;
5. deduplicate source-map/vendor echoes;
6. prove the delta against the SMF tuning and untouched holdout corpus.

Gate policy stays unchanged: `BLOCK > INCONCLUSIVE > WARN > ALLOW`.

## 2. Sub-Iterations

| ID | Package | Exit evidence | Status |
|---|---|---|---|
| SAP-0 | Activation and baseline lock | stacked branch, active tracker, SMF corpus retained | DONE |
| SAP-1 | Artifact role and header classifier | bounded stdlib classifier; role/magic tests | DONE |
| SAP-2 | S3 native precision | PNG/font/database/archive/WASM/opaque distinctions; renamed PE/ELF still fire | DONE |
| SAP-3 | S5 and production-bundle context | docs/license/source-map/test and manifest metadata URLs silent; runtime literal remains visible; unrelated bundle regions cannot form attack chains | DONE |
| SAP-4 | Inventory and deep-scan selection | dependency/minified inventory plus explicit selection reasons | DONE |
| SAP-5 | Reachability and deduplication | entrypoint/loader selection; source-map/vendor dedupe | DONE |
| SAP-6 | Full delta and close-out | tuning/holdout report, runtime budget, full gates, handoff | NEXT |

## 3. Implemented Initial Slice

- `static_runtime/artifacts.py` classifies manifest, first-party/dependency
  runtime, documentation, license, test, asset, source-map, configuration,
  native, WASM, archive, and unknown roles.
- A bounded 512-byte header read distinguishes PNG, JPEG, GIF, WebP, fonts,
  SQLite, ZIP/gzip/7z/RAR/tar, PE, ELF, Mach-O, WASM, opaque binary, text, and
  unknown formats.
- PE classification validates the bounded `PE\0\0` offset; an `MZ` prefix alone
  is insufficient.
- S3 v1.2.0 uses classifier evidence. Native ABI suffixes and PE/ELF/Mach-O
  headers remain actionable; generic opaque NUL-bearing files, images, fonts,
  databases, archives, and WASM are not mislabeled as native executables.
- S5 v1.2.0 excludes documentation, license, source-map, and test artifacts while
  preserving runtime-source endpoint detection. Parsed manifest fields used
  only for package documentation (`homepage`, `repository`, `bugs`, `funding`,
  author/contributor/license/readme metadata) are removed from endpoint
  matching; runtime configuration values remain visible.
- The SMF `tuning-doc-url` expectation now pins the intended ALLOW result.
- The machine rule inventory now records the SAP-2/SAP-3 artifact roles and
  remaining false-positive boundaries instead of the resolved PNG/docs
  baseline limitations.
- S10/S14/S15/S17/S18 now require all conjuncts inside an 8 KiB lexical region;
  S10 additionally requires the same process/socket variables on both bridge
  directions. S16 requires `getExtension` or install-root provenance and bounded
  assignment-to-sink flow instead of treating every non-`context`
  `extensionUri` receiver as foreign.
- S5 no longer parses bare ASN.1 OIDs as IPv4 endpoints, ignores license/test and
  reference-namespace URLs, and requires source URLs to be runtime-bound. S9
  requires a quantified wallet regex, so AES lookup arrays and MIPS `bc1[ft]`
  instructions stay silent.
- Native presence, oversized bundles, standalone base64/hex data, short
  invisible-Unicode runs, reserved-publisher names, untrusted-workspace support,
  and paired certificate/private-key material are INFO inventory signals. They
  remain visible but do not independently produce WARN/BLOCK.
- When dynamic analysis is off, Reports `latest` now consumes the independent
  latest-static artifact in both Overview and Rule matrix. Overview renders the
  static decision, gate reasons, findings, coverage, and tool status; dynamic-
  only search, filters, Interactions, Timeline, Event ledger, and Audit are
  disabled. Historical activation reports remain explicitly selectable and
  are never merged with an unrelated static run.
- Reports `Static analysis inspection`, placed beside `Rule matrix`, consumes
  the newest static artifact regardless of dynamic-analysis mode. It presents
  the gate decision, measured file
  coverage, severity distribution, tool execution time/status, coverage gaps,
  filterable findings, evidence-file footprint, and exact source snippets.
  INFO inventory remains visible without being presented as actionable risk.
- Every retained VSIX file now emits a schema-v2-compatible artifact inventory
  entry with a normalized path, role/format, size, SHA-256 of at most the first
  512 bytes, header-byte count, extension/header agreement, nearest scoped or
  nested dependency owner, vendor/minified flags, direct-entrypoint status,
  disposition, and bounded deterministic reasons. Legacy reports default to an
  empty inventory.
- File discovery, manifest entrypoint resolution, classification, coverage, and
  inventory reuse one cached analysis context. The existing 50,000-file and
  32 MiB per-target limits remain authoritative; unreadable and oversized files
  are explicit `skipped` entries.
- Coverage language is layer-specific: `files_discovered` / `files_scanned`
  account for every retained artifact, while `files_parsed` proves bounded
  in-house parsing of supported text formats and Semgrep reports its own
  JavaScript/TypeScript eligibility separately. Therefore `106/106` is a true
  complete result only when the aggregate has no coverage reason or skipped
  supported path; it is not a claim that binary or unsupported formats were
  executed as source code.
- Semgrep preserves its first-party pass and exclusions, then uses the remaining
  shared 600-second deadline for at most 256 exact dependency/minified paths
  selected by direct manifest entrypoint, in-house evidence, or extension/header
  mismatch. Findings are fingerprint-deduplicated into one tool record; a target
  cap or exhausted second-pass budget is visible as partial coverage rather than
  silent ALLOW.
- The shared product/evaluator default is now 600 seconds, which is also the
  validated hard maximum. App settings, the executor mirror, runtime/evaluator
  CLIs, Make helpers, and Docker's budget-plus-five-second wall bound share one
  contract; values outside 5-600 seconds fail closed.
- Copilot Chat's selected 9.2 MiB dependency bundle proved the former 768 MiB
  Semgrep / 1 GiB container envelope too small after the time-budget fix. The
  isolated analyzer now has 2 GiB/1 CPU and Semgrep has a 1536 MiB per-file
  ceiling; network/capability/non-root boundaries remain unchanged.
- A Semgrep structural-parser error or per-rule timeout now triggers one
  exact-path, same-deadline generic-language fallback carrying the same 16 rule
  IDs. At most 20 eligible failed paths, each no larger than 32 MiB, enter that
  fallback. Successful fallback paths are recorded as
  `structural_fallback_files` / paths; a fallback timeout, tool error, unhandled
  or excess path, exhausted shared budget, or remaining parser error still
  degrades the report instead of being relabeled clean.
- Base-pass dependency exclusions now cover node_modules, vendor/vendors, and
  all supported minified JavaScript/TypeScript suffixes through the shared
  artifact policy. Dedupe remains location-aware, so identical code on distinct
  source lines stays visible.
- Node-style manifest entrypoints with dotted but extensionless paths still
  receive the bounded supported-suffix resolution pass before inventory and
  deep-target selection.
- Static inspection now shows disposition/vendor/minified summaries, accessible
  path/owner/reason search, role/disposition filters, the selection-evidence
  table, and 50-row client pagination. Its table and report tabs remain locally
  scrollable at the 390x844 mobile acceptance size without widening the page.
- Rules now exposes the shipped whitelist as a read-only operator surface:
  trusted network domains include reviewed owner/purpose metadata, organization
  cards expose publisher namespaces and exact typosquat-baseline identities,
  and the API states the four dynamic rules affected by domain filtering.
  `host:port` observations (including sandbox loopback traffic) normalize before
  matching. Publisher/company identity alone never suppresses a behavioral
  finding.
- No blocker membership, timeout, dependency, DB schema, or dynamic execution
  behavior changed. Weak standalone heuristics were deliberately reclassified
  to INFO; proven critical/high conjunctions retain their existing gate effect.

## 4. Acceptance Evidence

Focused host checks:

```text
focused SAP-4 contract/runtime lane: 122 passed
focused worker-session isolation regression: 6 passed
focused timeout/resource contract lane: 101 passed
focused structural-fallback lane: 103 passed
coverage-completeness boundary regressions: 4 passed
focused SAP-4 UI lane: 5 passed
full UI suite: 189 passed
UI production build: passed
rendered browser QA: desktop + 390x844 mobile, no horizontal overflow or
console errors; inventory search/filter and responsive table interactions passed
make test-security: 535 passed
make check-all: 2933 passed / 11 skipped / 14 deselected
make test-smoke: 13 passed / 1 unavailable fixture skipped
ruff: all checks passed
git diff --check: passed
```

Hardened-container evaluation after rebuilding the image:

```text
make static-eval SPLIT=tuning: 8/8 passed
make static-eval SPLIT=all: 12/12 passed
rules bundle: 6496cf0ff536854d8cf36677e61141880a1bac87a741fd58a47802203ff3c1b5
corpus bundle: 6e1c71a6d12965ee6184883e284c94a0a9b1b51c4a6a4c6f3c6d6e5c4a3162b7
binary samples: TP 5 / FP 0 / FN 0 / TN 5; 2 coverage controls
sample precision: 1.0
sample recall: 1.0
sample false-positive rate/noise: 0.0 / 0.0
S3 precision/recall: 1.0 / 1.0
S5 precision/recall: 1.0 / 1.0
runtime: p50 1361 ms / p95 1629 ms / total 16676 ms
```

The documentation control changed WARN → ALLOW. Native presence is now an INFO
inventory signal and the native marker is a benign ALLOW control; the runtime
network marker remains WARN. All four holdout samples preserve their expected
conclusions.

Live Copilot Chat timeout/resource regression:

```text
original: in-house 106/106; Semgrep 9/10; budget_stop on sdk/index.js
600-second budget: Semgrep 10/10; budget_stop removed
2 GiB container / 1536 MiB Semgrep: prior OOM removed
Node syntax check: valid JavaScript
Semgrep 1.164.0 structural pass: parser_error on the generated bundle
generic fallback: 16 rules loaded, 11 findings, 0 errors, 1 fallback file
final report: partial=false; coverage reasons=[]; decision=WARN
```

The resource change removes artificial time/memory exhaustion. The generic
fallback then runs the rule set over the parser-incompatible source instead of
accepting an unscanned gap; its use remains explicit in the report. Here,
`106/106` means all 106 retained artifacts were accounted for by the aggregate
in-house coverage, every supported text artifact parsed, and Semgrep's one
structural failure was resolved by fallback. Any residual parser, size, target,
or budget gap would make the conclusion partial/INCONCLUSIVE instead.

Live in-house production-bundle regression (local unpacked artifacts):

```text
GitHub.copilot-1.388.0                  BLOCK 9  -> ALLOW 4 INFO
GitHub.copilot-chat-0.48.1             BLOCK 14 -> ALLOW 5 INFO
dbaeumer.vscode-eslint-3.0.34          WARN 2   -> ALLOW 0
esbenp.prettier-vscode-12.4.0          WARN 3   -> ALLOW 2 INFO
ms-python.python-2026.5.2026070801      BLOCK 8  -> ALLOW 4 INFO
```

## 5. Completed Slice — SAP-5

The bounded selection model now includes:

- transitive import and loader-graph reachability beyond direct manifest
  entrypoints;
- source-map and vendor-echo deduplication without suppressing unique evidence;
- deterministic provenance for each reachability and deduplication decision.

Acceptance evidence:

- lexical-tie-break BFS resolves bounded relative/bare Node-style imports,
  literal and folded loader references, native/WASM loaders, and source maps;
- node/edge/byte/depth/read/parse loss remains visible and coverage-degrading,
  while ordinary unresolved references remain bounded diagnostics;
- exact vendor/minified bytes and exact bounded `sourcesContent` echoes are the
  only suppression paths; unique, partial, malformed, or oversized evidence is
  retained;
- generated TypeScript contracts and the Reports Static Inspection UI surface
  reachability provenance, unresolved references, and deterministic
  canonical-to-duplicate records;
- focused backend `62/62`, UI `192/192`, `make check-all` and `make test-local`
  `2951 passed / 11 skipped`, security `536/536`, smoke `13 passed / 1 skipped`,
  and tuning/holdout/all static-eval splits passed on 2026-08-05.

Deep analysis remains bounded to first-party code plus dependency/minified
artifacts selected by recorded evidence. No blanket `node_modules` scan is
allowed. Lockfile resolution, real provenance comparison, and version diff stay
in SAR-4 rather than being inferred in SAP-5.

## 6. Next Slice — SAP-6

Produce the full measured tuning/holdout delta, record the shared runtime
budget and retained/suppressed evidence changes, rerun all handoff gates, and
close the named stream without changing containment product ordering.

## 7. Risks And Assumptions

- Artifact inventory can materially enlarge a report, so path/reason bounds,
  the shared 50,000-file cap, and deterministic ordering remain mandatory.
- The second Semgrep pass is limited to 256 exact targets and the unchanged
  shared deadline. A cap or budget stop deliberately degrades coverage to
  partial/INCONCLUSIVE when no stronger blocker exists.
- Structural fallback is limited to 20 eligible paths and 32 MiB per path under
  that same deadline. The boundary tests require the 21st path, an oversized
  path, and a path reached after budget exhaustion to remain visibly partial;
  there is no universal or unbounded "all files" claim.
- S5 currently proves runtime binding with bounded lexical context, not full
  URL-to-sink taint. SAP-5 reachability only selects additional deep-scan
  targets; SAR-3 still owns full taint semantics.
- Native suffixes remain evidence for declared ABI inventory, while S13 owns the
  suspicious native-loader conjunction and its blocker semantics.
- The 12-sample corpus proves the pinned regression cases, not universal
  precision. Counts and holdout results must remain visible in later deltas.
- No database schema change is in scope.
