# REFACTOR_OPTIMIZATION

`Last Updated: 2026-05-11 (W13 active; W13-1..W13-4 closed; §11.10 current acceptance bar aligned)`

W0-W13 plan document: stabilization + security + post-PoC external-review
integration. **Slim canonical** — full historical content is frozen under
dated snapshots:

- latest full snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-11.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-11.md)
- older snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md)

## Anchor Map

- §10 / §10.7 → W0-W7 PoC window and acceptance bar.
- §11 / §11.0 - §11.4 → W8-W13 external-review integration frame.
- §11.5 → W8 tracker:
  [`active-work/W8-security.md`](active-work/W8-security.md).
- §11.6 - §11.10 → W9-W13 weekly briefs.
- §11.11 - §11.14 → cross-ref, rejected, lane, and exit criteria summaries.

## §10 — W0-W7 PoC Stabilization Window (closed 2026-04-23)

PoC window closed `2026-04-23` with §10.7 acceptance bar 11/11 green.
Detailed W0-W7 plan history lives in the archive.

### §10.7 — PoC acceptance checklist (W7 sonu, closed 2026-04-23)

- [x] Legacy top-level business directories removed.
- [x] `packages/` import-graph enforcement exists.
- [x] VS Code version pinned; harness extension checksum verified.
- [x] Executor control boundary exists.
- [x] A1/A2/A4/A6 canaries and rules landed; A3 landed in the W7 buffer.
- [x] Benign baseline, scenario-dropout honesty, verdict rollup, UI finding
  display, `make test-security`, and demo acceptance were green.

## §11 — W8-W13 External Review Integration Window (2026-04-24+)

§11 integrates the post-PoC external reviews without moving the W0-W7 PoC
acceptance bar. Review snapshots live under `archive/reviews/`.

### §11.0 — Neden §11, §10'a ek satır değil

W8-W13 work is post-PoC hardening and modularization. Keeping it under §11
preserves the audit trail that §10.7 already closed.

### §11.1 — Entry Gate

W8 entry gate was met `2026-04-27`: PR345 PRs 1-5 landed, ADR 0006 accepted,
`make test-security` entry baseline was green, demo acceptance was green, and
W8-0 deterministic harness readiness landed.

Current closure chain: W8 closed `2026-04-29`; W9 closed `2026-05-04` via
PR #9; W10 closed `2026-05-04` via PR #11; W11 closed `2026-05-05` via
PR #14; W12 closed `2026-05-10` via PR #18; W13 is active.

### §11.2 — Haftalık dağılım (W8-W13)

| Hafta | Etiket | Status |
|---|---|---|
| W8 | Security hardening | closed `2026-04-29`; W8-8 deferred |
| W9 | Executor/detection boundary | closed `2026-05-04`; ADR 0008 accepted |
| W10 | Contract hygiene + planner cleanup | closed `2026-05-04`; PR #11 |
| W11 | Monitor lifecycle split | closed `2026-05-05`; PR #14 |
| W12 | Executor subpackaging + attribution cleanup | closed `2026-05-10`; PR #18 |
| W13 | Test expansion + observability | active; W13-1..W13-4 closed |

### §11.3 — Haftalar arası bağımlılıklar

- W10 depends on W9 package-mode import discipline.
- W11 depends on W10 typed contracts.
- W12 depends on W11 monitor lifecycle split.
- W13 locks in W8-W12 regression coverage and pulls audit follow-ups.

### §11.4 — Non-goals

Queue-backed distributed workers, multi-tenant accounts, broad run-history
infrastructure, and speculative UI/product expansion remain outside W8-W13
unless pulled from `POST_POC_BACKLOG.md` with a stable ID.

### §11.5 — W8 Güvenlik Sıkılaştırma

Moved to [`active-work/W8-security.md`](active-work/W8-security.md). W8 is
closed for active work; retained for W8-1..W8-9 stable-ID references.

### §11.6 — W9 Executor/Detection Boundary

W9 closed `2026-05-04` via PR #9. ADR 0008 container package-mode invocation
is accepted; dual-import fallback and runtime `sys.path.insert` debt were
removed.

### §11.7 — W10 Contract Hygiene + Planner Cleanup

W10 closed `2026-05-04` via PR #11. `schema_version`, planner registry
cleanup, typed health/coverage models, executor action enum, and W10
contract gates landed.

### §11.8 — W11 Monitor Lifecycle Split

W11 closed `2026-05-05` via PR #14. W11-1..W11-8 split monitor runtime,
report assembly, scenario accounting, monitor facade, workflow service, and
storage CRUD modules. Tracker:
[`active-work/W11-monitor-lifecycle.md`](active-work/W11-monitor-lifecycle.md).

### §11.9 — W12 Executor Subpackaging + Attribution Cleanup

W12 closed `2026-05-10` and merged via PR #18 (`33a0852`). Tracker is frozen:
[`active-work/W12-executor-subpackaging.md`](active-work/W12-executor-subpackaging.md).

Closed scope:

- W12-0 security pull-forward: file-backed output-signal redaction.
- W12-1 executor subpackaging: ≤10 flat Playwright modules, 10 package dirs,
  `python -m` shims, and import-cycle gates.
- W12-2 attribution facade cleanup: public facade trimmed, companion follow-ups
  closed.
- W12-3 `raw_context` discriminated union typing.
- W12-4 entrypoint dispatch extraction: `runner.py::main` under 200 LoC.
- W12-5 `runtime_capture/extension_host.py` split + body-preview redaction
  architecture gate.
- UI/API Dockerfile digest pins, W12 close-out coverage, and Codex CRITICAL
  subprocess-output redaction fix.

Final close evidence is archived at
[`archive/active-work/W12-close-acceptance-completed-2026-05-10.md`](archive/active-work/W12-close-acceptance-completed-2026-05-10.md).

#### §11.9.1 — `runtime_capture/extension_host.py` Split Scoping

§11.9.1 is closed by W12-5. Full scoping detail lives in the W12 tracker and
archive snapshot; current code keeps `extension_host.py` as a thin facade over
focused runtime-capture modules.

### §11.10 — W13 Test Expansion + Observability

Entry conditions were met `2026-05-10`: W12 closed and merged; W12 close
baseline `make check-all` was green at close commit `e8a9926`
(`make test-local` 1452 / `make test-security` 211 /
`tests/architecture/` 76). Active tracker:
[`active-work/W13-test-expansion-observability.md`](active-work/W13-test-expansion-observability.md).

Goal: benign silence fixture breadth, stale singleton-lock and `.env`
regression gates, executor logger/run-ID observability, and W8-W12 regression
lock-in.

Audit pull-forwards:

- W13-1 closed `[FOLLOWUP codex-2026-05-10-H6-spoofable-harness-markers]`.
- W13-2 closed `[FOLLOWUP codex-2026-05-10-H5-writable-vscode-launcher]`.
- W13-3 closed `[FOLLOWUP codex-2026-05-10-H4-cancel-concurrent-race]`.
- W13-4 closed `[FOLLOWUP w13-3-close-pass-cancellation-test-hardening]`.
- W13-5 next: `[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]`.
- Still open for W13 acceptance: `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]`
  and `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]`.

Original §11.10 candidates that remain open are tracked in
`POST_POC_BACKLOG.md` and the W13 tracker Candidate Items table.

### §11.11 — Cross-Reference

External review findings are tracked by stable IDs in `POST_POC_BACKLOG.md`;
closed W8-W12/W13 items stay visible there only as audit trail summaries.

### §11.12 — Rejected Or Out-Of-Scope Items

Rejected review findings and WONT-FIX decisions live in the archive snapshots.
Current WONT-FIX audit item: M14a, workspace ownership by design.

### §11.13 — Paralel Lane Assignments

Use `documents/AGENT_CONTEXT.md` and the lane docs for routing. Active W13
work generally starts from `security-detection`, `executor-runtime`,
`platform-storage`, or `ui` depending on the stable ID.

### §11.14 — W13-End Overall Exit Criteria

Before W13 closes:

- H3, M1, and M9 are either closed or explicitly deferred with acceptance
  rationale.
- W13 tracker has final close evidence and current test counts.
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, `documents/README.md`, and
  relevant lane docs point to the same active/closed state.
- Slim canonicals remain short; verbose evidence is archived first.
