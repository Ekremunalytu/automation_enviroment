# Demo Scenario — A1 Credential-Read → Network Exfil

`Last Updated: 2026-04-25`

## Purpose

Stakeholder-facing end-to-end demo that proves the ExTrace PoC stack
detects a realistic VS Code extension performing **credential file
read followed by outbound network exfiltration** — adversary class
**A1** in ADR 0002 §4, rule `extrace.a1.credential_read_then_network`
(production lifecycle, MITRE ATT&CK `T1555 → T1041`).

The demo uses the T1 internal canary
[`extensions/malicious/t1-a1-credential-read-canary/`](../extensions/malicious/t1-a1-credential-read-canary/)
and exercises the full pipeline:

```text
ActivationReport (canary fixture)
        │
        ▼
packages.analysis_engine.runner.run_detection
        │
        ▼
DetectionReport  ────► UI ReportsPage → FindingCard → Evidence deep-link
```

Two runnable flavors are provided — pick whichever suits the audience.
A third flavor (`make demo-canary`) was added on 2026-04-25 and runs the
same A1 detection contract end-to-end against the new
`t1-demo-runnable-canary` declawed fixture; see *Flavor C* below.

## Canary at a Glance

- **Manifest:** [`t1-a1-credential-read-canary/LABEL.yaml`](../extensions/malicious/t1-a1-credential-read-canary/LABEL.yaml)
  - `tier: T1` (internal synthetic canary; safe for CI)
  - `expected_detections.must_fire`: `["extrace.a1.credential_read_then_network"]`
  - `category.taxonomy`: `["attack.T1555"]`
- **Fixture:** [`t1-a1-credential-read-canary/activation_report.json`](../extensions/malicious/t1-a1-credential-read-canary/activation_report.json)
  - Activation at `rel_time_s 0.2`
  - `file` read of `/home/executor/.ssh/id_rsa` at `rel_time_s 4.0`
    (`attribution_status: "strong"`, `is_target_extension_event: true`)
  - `network` POST to `collector.evil.invalid/upload` at `rel_time_s 18.0`
    (same attribution; within the 60 s correlation window the rule requires)

The A1 rule
([`packages/analysis_engine/rules/a1_credential_read_then_network.py`](../packages/analysis_engine/rules/a1_credential_read_then_network.py))
joins these two events because the credential path matches
`_CREDENTIAL_PATH_PATTERN`, the host is not in the benign allow-list,
and `|Δt| ≤ 60 s`. Expected output: one finding at
`severity=critical, confidence=high`.

## Flavor A — Offline (fastest, CI-safe) ~30 s

Use this when no Docker daemon is available or when you want a
deterministic demo for a recording. Runs the package-local detection
engine directly against the canary's stored `activation_report.json`.

### Steps

1. Activate the project venv:

   ```bash
   source .venv/bin/activate
   ```

2. Run the acceptance script (written in Phase 2 of the W7 plan):

   ```bash
   python scripts/demo_acceptance.py
   ```

   The script:
   - Loads `extensions/malicious/t1-a1-credential-read-canary/activation_report.json`
     via `workflows.marketplace.analysis_reports.run_local_analysis`
   - Pretty-prints the resulting `DetectionReport` (verdict, rule, finding,
     evidence event IDs)
   - Asserts the acceptance contract below and exits `0` on success.

### Acceptance contract

| # | Assertion | Why |
|---|---|---|
| 1 | `detection_report.verdict ∈ {"malicious", "suspicious"}` | A1 rule must elevate verdict off `clean`. |
| 2 | Exactly one finding carries `rule_id == "extrace.a1.credential_read_then_network"` | The A1 rule fired. |
| 3 | Finding `severity == "critical"` AND `confidence == "high"` | Matches §10.7 bar: `confidence ≥ medium`, `severity ≥ high`. |
| 4 | Finding `evidence` holds 2 refs: a `filesystem_read` for the `.ssh/id_rsa` event and a `network_request` for `collector.evil.invalid` | Evidence deep-link targets exist in the paired report. |
| 5 | `detection_report_invariant_issues(detection_payload, activation_payload) == []` | Cross-layer link invariant (ADR 0003 §4) holds: every evidence event_id resolves in the ActivationReport. |
| 6 | `rule_execution_record.status == "fired"` for A1; no rule in `rules_executed` reports `"error"` | Runner clean (ADR 0003 §5). |

## Flavor B — Live UI Walkthrough (stakeholder demo) ~5 min

Use this when presenting to a non-technical audience or when you need
to show the analyst UI. Requires Docker.

### Prerequisites

```bash
make install-dev
make migrate          # Postgres schema up to head
make exec-build       # Executor + VS Code pinned image
```

### Steps

1. **Bring the stack up** — three terminals:

   ```bash
   # Terminal 1 — API
   make dev

   # Terminal 2 — sandbox executor
   make exec-up

   # Terminal 3 — UI dashboard
   make ui-up
   ```

   Open <http://localhost:5173> (UI) and
   <http://localhost:8000/docs> (API Swagger).

2. **Ingest the canary as a local fixture.** The offline path already
   supports this — drive it through the UI via the Simulation page, or
   from the terminal:

   ```bash
   curl -X POST http://localhost:8000/api/marketplace/analyze/start \
     -H 'Content-Type: application/json' \
     -d '{
       "publisher": "extrace",
       "name": "t1-a1-credential-read-canary",
       "version": "0.0.1",
       "fixture_path": "extensions/malicious/t1-a1-credential-read-canary"
     }'
   ```

   The API returns `{ "job_id": "<ulid>" }`. Poll until `completed`:

   ```bash
   curl http://localhost:8000/api/marketplace/analyze/<job_id>
   ```

   The response carries both `activation_report` (link) and
   `detection_report` (inline).

3. **Walk the UI.**
   - Navigate to `Reports → extrace.t1-a1-credential-read-canary`.
   - `ReportsPage`
     ([`ui/src/features/reports/ReportsPage.tsx`](../ui/src/features/reports/ReportsPage.tsx))
     renders a single red `FindingCard` titled **"Credential file read
     followed by outbound request"**, verdict badge `malicious`,
     severity `critical`, confidence `high`.
   - Click **"Show evidence"** on the finding card. The Evidence tab
     scrolls to and highlights `file-0001` (the `.ssh/id_rsa` read)
     and `network-0001` (the `collector.evil.invalid` POST).
   - Open the **Automation Health** chip: status `healthy`, no blockers.
   - The **Signal Summary** chip (activation-layer heuristic) shows
     `likely_malicious` — separated from the authoritative detection
     verdict as required by the W7-entry vocabulary split.

4. **(Optional) Show silence on a benign baseline.** Repeat step 2
   with `publisher=extrace, name=fixture-chat, version=0.0.1`. The
   Reports page renders `clean` with **no findings**; this proves the
   W6 correlative-signal FP floor holds.

## Flavor C — Demo Runnable Canary (`make demo-canary`) ~1 min

Use this when you want to demonstrate that the rule engine fires
end-to-end against an extension that **does** run real, declawed code
inside the sandbox — not just a stored `activation_report.json`. The
fixture `extensions/malicious/t1-demo-runnable-canary/` carries:

- localhost-only POST to `127.0.0.1:8787` with a 500 ms timeout
  (network signal source)
- workspace-local file write (filesystem signal source)
- explicit `onCommand` activation (no auto-fire)
- a dedicated `extrace.demo.runnable_canary` rule with a
  `target_extension_expected` gate so it cannot false-positive on
  unrelated extensions

### Steps

1. **Offline (no Docker):**

   ```bash
   make demo-canary-offline
   ```

   Validates the fixture against the rule engine without spinning up the
   executor. Equivalent to `python scripts/demo_acceptance.py` but
   targets the demo-canary fixture and rule.

2. **End-to-end (requires Docker):**

   ```bash
   make exec-up           # one-time per session
   make demo-canary       # builds + runs the canary in the sandbox
   ```

   Watch the resulting report under `output/`; the
   `extrace.demo.runnable_canary` finding fires with the expected
   evidence chain. Use this as a fast smoke for capture-pipeline
   regressions after touching `executor/flows/playwright/attribution/`
   or `runtime_capture/`.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `verdict == "clean"` on canary | `.gitignore` excluded the canary fixture from the working tree | Verify `extensions/malicious/t1-a1-credential-read-canary/` exists; re-check allow-list entries in `.gitignore` |
| Invariant test fails (`event_id not in ActivationReport`) | Canary `activation_report.json` modified without updating rule evidence refs | Run `make test-security`; fix the per-rule fixture test output |
| `make exec-up` cannot start | Docker daemon down, or `EXECUTOR_VSCODE_VERSION` not pinned | `docker ps` to confirm daemon; set `.env` `EXECUTOR_VSCODE_VERSION=1.116.0` |

## References

- ADR 0002 §4 — A1 threat model.
- ADR 0003 §3, §4, §5 — Severity/Confidence, evidence linking invariant,
  verdict rollup with error dominance.
- ADR 0004 — T1 canary policy.
- `documents/REFACTOR_OPTIMIZATION.md` §10.7 — PoC acceptance checklist.
- [`tests/security/rules/test_a1_credential_read_then_network.py`](../tests/security/rules/test_a1_credential_read_then_network.py)
  — per-rule fire test.
- [`tests/security/test_detection_report_invariants.py`](../tests/security/test_detection_report_invariants.py)
  — evidence event_id resolution + quantization thresholds.
