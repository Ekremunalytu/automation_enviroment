# Static Analysis Artifact Precision

`Last Updated: 2026-08-03`

`Status: ACTIVE — SAP-0 through SAP-4 and the production-bundle precision
follow-up are implemented on codex/static-analysis-artifact-precision. The
branch also carries the static-only Reports presentation correction described
in section 3, the Reports-integrated Static analysis inspection tab, and the
Rules whitelist visibility/normalization follow-up. SAP-5 is next.`

`Parent: static-analysis-improvement-roadmap.md Increment B / SAR-2.`

`Stacking boundary: this branch starts from the committed and pushed
static-analysis-measurement-foundation head. SMF is not merged; PR, merge, and
remote publication are separate actions. Successor branch publication was
authorized on 2026-07-31; PR/merge were not.`

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
| SAP-5 | Reachability and deduplication | entrypoint/loader selection; source-map/vendor dedupe | NEXT |
| SAP-6 | Full delta and close-out | tuning/holdout report, runtime budget, full gates, handoff | PENDING |

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
- Semgrep preserves its first-party pass and exclusions, then uses the remaining
  shared 30-second deadline for at most 256 exact dependency/minified paths
  selected by direct manifest entrypoint, in-house evidence, or extension/header
  mismatch. Findings are fingerprint-deduplicated into one tool record; a target
  cap or exhausted second-pass budget is visible as partial coverage rather than
  silent ALLOW.
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
focused SAP-4 UI lane: 5 passed
full UI suite: 189 passed
UI production build: passed
rendered browser QA: desktop + 390x844 mobile, no horizontal overflow or
console errors; inventory search/filter and responsive table interactions passed
make test-security: 530 passed
make check-all: 2904 passed / 11 skipped / 13 deselected
make test-smoke: 4 static-container checks passed / 9 executor-only checks
skipped because the executor service was not running
ruff: all checks passed
git diff --check: passed
```

Hardened-container evaluation after rebuilding the image:

```text
make static-eval SPLIT=tuning: 8/8 passed
make static-eval SPLIT=all: 12/12 passed
rules bundle: a22f07391424da90c6fc142bac01c357b4cc8878c866a9c7780f922e914a4d18
corpus bundle: 6e1c71a6d12965ee6184883e284c94a0a9b1b51c4a6a4c6f3c6d6e5c4a3162b7
binary samples: TP 5 / FP 0 / FN 0 / TN 5; 2 coverage controls
sample precision: 1.0
sample recall: 1.0
sample false-positive rate/noise: 0.0 / 0.0
S3 precision/recall: 1.0 / 1.0
S5 precision/recall: 1.0 / 1.0
runtime: p50 1232 ms / p95 1507 ms / total 15055 ms
```

The documentation control changed WARN → ALLOW. Native presence is now an INFO
inventory signal and the native marker is a benign ALLOW control; the runtime
network marker remains WARN. All four holdout samples preserve their expected
conclusions.

Live in-house production-bundle regression (local unpacked artifacts):

```text
GitHub.copilot-1.388.0                  BLOCK 9  -> ALLOW 4 INFO
GitHub.copilot-chat-0.48.1             BLOCK 14 -> ALLOW 5 INFO
dbaeumer.vscode-eslint-3.0.34          WARN 2   -> ALLOW 0
esbenp.prettier-vscode-12.4.0          WARN 3   -> ALLOW 2 INFO
ms-python.python-2026.5.2026070801      BLOCK 8  -> ALLOW 4 INFO
```

## 5. Next Slice — SAP-5

Extend the bounded selection model with:

- transitive import and loader-graph reachability beyond direct manifest
  entrypoints;
- source-map and vendor-echo deduplication without suppressing unique evidence;
- deterministic provenance for each reachability and deduplication decision.

Deep analysis remains bounded to first-party code plus dependency/minified
artifacts selected by recorded evidence. No blanket `node_modules` scan is
allowed. Lockfile resolution, real provenance comparison, and version diff stay
in SAR-4 rather than being inferred in SAP-5.

## 6. Risks And Assumptions

- Artifact inventory can materially enlarge a report, so path/reason bounds,
  the shared 50,000-file cap, and deterministic ordering remain mandatory.
- The second Semgrep pass is limited to 256 exact targets and the unchanged
  shared deadline. A cap or budget stop deliberately degrades coverage to
  partial/INCONCLUSIVE when no stronger blocker exists.
- S5 currently proves runtime binding with bounded lexical context, not full
  URL-to-sink taint. Full reachability remains part of SAP-5/SAR-3 preparation.
- Native suffixes remain evidence for declared ABI inventory, while S13 owns the
  suspicious native-loader conjunction and its blocker semantics.
- The 12-sample corpus proves the pinned regression cases, not universal
  precision. Counts and holdout results must remain visible in later deltas.
- No database schema change is in scope.
