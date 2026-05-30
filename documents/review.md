# Repository Review Snapshot

`Last Updated: 2026-05-28 — W22 closed synthetically on week22 and merged to main via PR #31 week22 -> main 1399f82; W21 closed and merged via PR #30 5dc18aa.`

Use this as the shortest review-order hint, not as the architecture source of
truth.

## Review Order

1. `workflows/marketplace/`
2. `executor/`
3. `tests/architecture/` + `tests/security/`
4. `appcore/`
5. `ui/`
6. remaining workflow slices

## Why This Order

- the highest-risk path is still intake -> trigger planning -> sandbox
  execution -> report consumption
- executor timing and reload behavior remain the biggest source of product risk
- import boundaries and security scaffolds now carry real architectural weight
- report and coverage semantics can drift if backend and UI evolve separately
