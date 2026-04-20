# packages/analysis_engine

`Last Updated: 2026-04-20`

This package is still a reserved extraction surface for trusted analysis logic
that should not remain buried inside sandbox-local executor modules.

As of `2026-04-20`, no production modules have been extracted here yet.

Expected future responsibilities:

- report normalization
- attribution helpers
- risk signal derivation
- trusted serialization and interpretation helpers

This package must remain framework-agnostic like the rest of `packages/`.
