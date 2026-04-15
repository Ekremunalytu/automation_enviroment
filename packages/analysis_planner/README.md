# packages/analysis_planner

Week 3 planner extraction package for layered marketplace trigger selection.

Planner logic is split into small state-free modules:

- `registry.py`
  planner registries, capability maps, and pass constants
- `selection.py`
  trigger selection flow and mutable draft assembly
- `attempts.py`
  event-attempt, pass, prerequisite, and executor-action helpers
- `coverage.py`
  coverage accounting and final payload assembly
- `io.py`
  serialization, slug/label helpers, and payload file writing

This package must stay independent from web, DB, and executor modules. It may
depend on `packages.analysis_contracts` plus the Python standard library.
