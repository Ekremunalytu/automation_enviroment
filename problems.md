# Project Analysis - Current Issues

`Last Updated: 2026-04-20`

This file tracks known issues against the current refactored architecture.

## High Priority

1. Analysis reliability still depends on executor reload correctness.
   - Relevant paths:
     - `executor/host.py`
     - `executor/flows/playwright/reload_vscode.py`
     - `executor/flows/playwright/vscode.py`
   - Risk:
     - a run can still appear operationally healthy until the VS Code workbench
       and extension-host surfaces fully reconnect.

2. Harness-extension integrity is still not checksummed.
   - Relevant paths:
     - `executor/flows/harness_extension/`
     - `documents/REFACTOR_STATUS.md`
   - Risk:
     - the helper extension sits on a trust boundary and still needs W5
       supply-chain attestation.

3. Dynamic-analysis reports are still file-backed.
   - Relevant paths:
     - `workflows/activation_reports/router.py`
     - `output/`
     - `workflows/marketplace/job_service.py`
   - Risk:
     - jobs are durable in Postgres, but report history and comparisons remain
       artifact-first.

## Medium Priority

1. Security scaffold coverage is ahead of dedicated CI wiring.
   - Relevant paths:
     - `tests/security/`
     - `Makefile`
     - `.github/workflows/ci.yml`
   - Risk:
     - manifest and coverage-contract tests exist, but the repo still needs a
       dedicated CI lane and install-guard automation to match ADR 0004's full
       target state.

2. Some trigger scenarios remain sensitive to workspace path mismatches.
   - Relevant paths:
     - `executor/flows/playwright/entrypoint.py`
     - `executor/flows/playwright/workspace.py`
     - `executor/container/start.sh`
   - Risk:
     - trigger bait files may not land where VS Code is actually operating.

3. UI request/client logic is still thinner than the generated contract layer.
   - Relevant paths:
     - `scripts/generate_ui_contracts.py`
     - `ui/src/lib/api/client.ts`
     - `ui/src/lib/adapters/`
   - Risk:
     - generated DTOs reduce drift, but request composition and view-model
       adapters can still drift from backend semantics.

## Lower Priority

1. File-backed report retention and cleanup policy is still implicit.
   - Relevant path:
     - `output/`

2. Historical `apps/` placeholders can still confuse newcomers.
   - Relevant paths:
     - `apps/api/README.md`
     - `apps/ui/README.md`

## Validation Notes

- The architecture references in this file use canonical paths introduced by
  the refactor.
- This file assumes a single-user sandbox deployment, not a shared SaaS app.
- Security scaffolding now exists in-repo, but full detection implementation is
  still pending.
