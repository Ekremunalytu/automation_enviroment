# Rule Lifecycle + ADR 0003 Cross-Ref

`Last Updated: 2026-04-29`

Detection-rule authoring + the boundary between activation-layer
`signal_summary` and rule-driven `DetectionReport.verdict`. Top-level
contract map: [`../DETECTION_SEMANTICS.md`](../DETECTION_SEMANTICS.md).

## Where Rules Live

- `packages/analysis_engine/rules/` — A1 / A2 / A3 / A4 / A6 live; A5
  - A7 deferred (`POST_POC_BACKLOG.md`).
- Rules import only contracts (`packages/analysis_contracts/`); never
  runtime, web, or storage layers (enforced by
  `tests/architecture/test_import_graph.py`).
- Allow-lists under `packages/analysis_engine/allowlists/`
  (`benign_domains.txt`, `popular_extensions.txt`).

## ADR 0003 — Detection Taxonomy

`documents/adrs/0003-detection-taxonomy.md` is the authoritative
specification for:

- MITRE ATT&CK alignment.
- Severity / confidence vocabulary (shared between
  `DetectionFinding.confidence` and `risk_signals[*].confidence_tier`).
- `DetectionReport` contract shape.
- Verdict rollup (`clean` / `suspicious` / `inconclusive` /
  `malicious`).
- Rule lifecycle stages.

Pending W8-6 addendum (§6) — content-sample secret redaction policy;
see [`../active-work/W8-security.md`](../active-work/W8-security.md)
item W8-6.

## Activation-Layer vs Detection-Layer Vocabulary

| Layer | Carrier | Where it lives |
|---|---|---|
| Sandbox behavioral heuristic | `ActivationReport.signal_summary.level` (`benign` / `needs_review` / `suspicious` / `likely_malicious`) | `executor/flows/playwright/signals.py` |
| Authoritative detection verdict | `DetectionReport.verdict` (`clean` / `suspicious` / `inconclusive` / `malicious`) | `packages/analysis_contracts/detection/` + verdict rollup |

The W7 rename consolidated authoritative verdict semantics into the
detection layer. Do not surface activation-layer `signal_summary` as
the final verdict.

## Rule Authoring Pointers

- DTOs: `packages/analysis_contracts/detection/`
  (`DetectionReport`, `DetectionFinding`, `Confidence`, `Verdict`,
  `AdversaryClass`, `RuleLifecycle`, `RuleExecutionStatus`).
- Quantizer: `packages.analysis_contracts.quantize_confidence` —
  shared between `DetectionFinding.confidence` and
  `risk_signals[*].confidence_tier`.
- Engine runner: `tests/platform/engine/test_rule_runner.py` is the
  reference exercise; mirror its fixture pattern for new rules.
- Per-class tests: `tests/security/rules/test_a<N>_*.py`.
- Coverage contract: `tests/security/test_rule_coverage.py` enforces a
  per-class canary + rule pair for every Must-class adversary.
- Attribution gating: `tests/security/rules/test_rule_attribution.py`
  asserts target-only attribution.

## Adding A Rule

1. Pick the adversary class; confirm coverage gap in
   `test_rule_coverage.py`.
2. Add the rule under `packages/analysis_engine/rules/`; consume only
   contracts.
3. Add a T1 canary fixture under `extensions/malicious/<name>/` with
   `LABEL.yaml`.
4. Add per-class test under `tests/security/rules/test_a<N>_*.py`.
5. Update `test_rule_coverage.py` if the canary set changes.
6. Run `make test-security` (current cross-tree lane; entry baseline was
   45 cases on `2026-04-27`) and `make demo-canary-offline` (<30 s
   detection-engine sanity).

## Rejected From W8-W13

- `correlative_suspicious_activity` benign-baseline regression: post-W6
  `signal_policy` thresholds tightened (2026-04-21). Re-evaluation at
  W13 documentation consolidation pass.
- `risk_signals` category expansion (e.g. credential-stuffing
  patterns) — deferred until A5/A7 land.

See `archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md` §11.12 for
review-rejected detection items.
