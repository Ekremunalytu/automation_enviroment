# `extensions/malicious`

This directory is reserved for ADR 0004 malicious fixtures.

- Treat every fixture here as intentionally hostile research material.
- Do not install anything from this tree with general-purpose helper scripts.
- Every fixture directory must ship a `LABEL.yaml` manifest.
- The current PoC gate is T1 canaries only.
- `make test-security` is allowed in CI.
- `make test-security-live` is local-only and refuses to run in CI.

Initial Week 5 canaries cover A1, A2, A4, and A6 through offline report
fixtures. `t1-demo-runnable-canary` is a declawed local-only demo extension
for operator demos; it does not contact external hosts or read real secrets.
