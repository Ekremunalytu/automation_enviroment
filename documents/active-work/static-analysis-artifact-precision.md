# Static Analysis Artifact Precision

`Last Updated: 2026-07-31`

`Status: ACTIVE — SAP-0 through SAP-3 initial precision slice implemented and
validated on codex/static-analysis-artifact-precision. The branch also carries
the static-only Reports presentation correction described in section 3.`

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
| SAP-3 | S5 documentation context | docs/license/source-map and manifest metadata URLs silent; runtime literal still fires | DONE |
| SAP-4 | Inventory and deep-scan selection | dependency/minified inventory plus explicit selection reasons | NEXT |
| SAP-5 | Reachability and deduplication | entrypoint/loader selection; source-map/vendor dedupe | PENDING |
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
- S3 v1.1.0 uses classifier evidence. Native ABI suffixes and PE/ELF/Mach-O
  headers remain actionable; generic opaque NUL-bearing files, images, fonts,
  databases, archives, and WASM are not mislabeled as native executables.
- S5 v1.1.0 excludes documentation, license, and source-map artifacts while
  preserving runtime-source endpoint detection. Parsed manifest fields used
  only for package documentation (`homepage`, `repository`, `bugs`, `funding`,
  author/contributor/license/readme metadata) are removed from endpoint
  matching; runtime configuration values remain visible.
- The SMF `tuning-doc-url` expectation now pins the intended ALLOW result.
- The machine rule inventory now records the SAP-2/SAP-3 artifact roles and
  remaining false-positive boundaries instead of the resolved PNG/docs
  baseline limitations.
- When dynamic analysis is off, Reports `latest` now consumes the independent
  latest-static artifact in both Overview and Rule matrix. Overview renders the
  static decision, gate reasons, findings, coverage, and tool status; dynamic-
  only search, filters, Interactions, Timeline, Event ledger, and Audit are
  disabled. Historical activation reports remain explicitly selectable and
  are never merged with an unrelated static run.
- No severity, confidence, blocker membership, timeout, dependency, DB schema,
  or dynamic execution behavior changed.

## 4. Acceptance Evidence

Focused host checks:

```text
focused artifact/S3/S5/runner/inventory lane: 73 passed
architecture/state pointer lane: 14 passed
Reports UI suite: 178 passed, including latest-static Overview, disabled
dynamic deep-link redirect, latest-static API failure, and historical-report
retention
make test-security: 434 passed
make -e check-all with postgres_test: 2844 passed / 11 skipped / 13 deselected
ruff: all checks passed
git diff --check: passed
```

Hardened-container evaluation after rebuilding the image:

```text
make static-eval SPLIT=tuning: passed
make static-eval SPLIT=all: passed
rules bundle: 077dc7f1e56ae2d080e256a45430275b0ccf71a0dc3abd077614f429b4ed2fb5
samples: TP 6 / FP 0 / FN 0 / TN 5
sample precision: 1.0
sample recall: 1.0
S3 precision/recall: 1.0 / 1.0
S5 precision/recall: 1.0 / 1.0
runtime: p50 1242 ms / p95 1473 ms / total 15234 ms
```

The documentation control changed WARN → ALLOW. The native marker and runtime
network marker remain WARN. All four holdout samples preserve their expected
conclusions.

## 5. Next Slice — SAP-4

Add an inventory record for every discovered file, including:

- normalized path, role, format, size, and bounded hash/header evidence;
- dependency ownership and minified/vendor status;
- manifest/entrypoint reachability;
- explicit `deep_scan`, `inventory_only`, or `skipped` disposition with reason.

Deep analysis remains bounded to first-party code plus dependency/minified
artifacts selected by reachability, change/provenance mismatch, loader
relationship, extension/header mismatch, or another recorded suspicious
signal. No blanket `node_modules` scan is allowed.

## 6. Risks And Assumptions

- Role/format classification is currently consumed by S3/S5 but is not yet
  emitted as report inventory; SAP-4 owns that contract and producer change.
- S5 currently distinguishes artifact context and top-level manifest
  documentation metadata, not full URL-to-sink flow. Sink-aware precision
  remains part of SAP-5/SAR-3 preparation.
- Native suffixes remain evidence for declared ABI artifacts so the declawed
  `.node` corpus marker continues to model packaged native capability.
- The 12-sample corpus proves the pinned regression cases, not universal
  precision. Counts and holdout results must remain visible in later deltas.
- No database schema change is in scope.
