# Repository Review Snapshot

`Last Updated: 2026-04-15`

Use this as the shortest review-order hint, not as the architecture source of
truth.

## Review Order

1. `workflows/marketplace/`
2. `executor/`
3. `appcore/`
4. `ui/`
5. remaining workflow slices

## Why This Order

- the highest-risk path is still intake -> trigger planning -> sandbox
  execution -> report consumption
- executor timing and reload behavior remain the biggest source of product risk
- report and coverage semantics can drift if backend and UI evolve separately
