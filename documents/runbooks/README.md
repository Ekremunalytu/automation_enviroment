# Runbooks

`Last Updated: 2026-04-24`

Operational runbooks for recovering ExTrace from the most common failure
modes. These are **single-operator sandbox appliance** runbooks — they
assume the backend, UI, PostgreSQL, and executor run on the same host and
there is no SRE-grade escalation path.

Each runbook follows the same shape:

1. **Symptom** — what the operator actually sees
2. **Immediate triage** — 2-3 cheap checks before any mutation
3. **Diagnose** — where to read (files, DB, logs) with concrete commands
4. **Recover** — exact recovery commands, with irreversibility warnings
5. **Root-cause classes** — known underlying conditions
6. **Code references** — modules that own the failure mode

## Index

- [Analysis job stuck or failed unexpectedly](analysis-job-stuck.md)
  — `analysis_jobs.status = running` for too long, no progress on steps
- [Fatal UI crash during scan](fatal-ui-crash.md)
  — `failure_reason_code = "fatal_ui_crash"`, `automation_health = inconclusive`,
    scenarios aborted
- [Scan-between VS Code restart failure](scan-between-restart-failure.md)
  — second scan fails `code --install-extension` with rc=1 (stale Chromium
    SingletonLock / dead IPC socket)
- [Live capture regression](live-capture-regression.md)
  — `make test-security` green, `make test-security-live` red; missing
    `tls_client_hello` events break A2/A4 TLS rules

## When to Update

- A failure mode recurs **twice** with the same root cause → write or
  update a runbook.
- A recovery command changes → update the relevant runbook *immediately*;
  stale recovery steps are worse than missing ones.
- A failure mode becomes fully automated (code detects + recovers without
  operator intervention) → move the runbook to `documents/runbooks/archive/`
  with a brief note explaining what replaced it.

## Conventions

- All container commands assume the canonical name `automation_executor`
  (see `docker-compose.yml`). If you renamed the stack, substitute.
- Absolute paths in diagnosis steps are **in-container** paths unless
  marked `host:`.
- SQL examples use the PostgreSQL CLI (`psql`), but any client that hits
  the `analysis_jobs` / `extensions` / `activation_reports` tables works.
