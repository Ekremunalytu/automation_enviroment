# UI Lane

`Last Updated: 2026-04-27`

Use this lane for the React/Vite analyst console, frontend contracts, route
behavior, report views, simulation UI, and UI tests.

## Start Here

- `ui/src/app/`
- `ui/src/features/marketplace/`
- `ui/src/features/reports/`
- `ui/src/features/simulation/`
- `ui/src/components/`
- `ui/src/lib/api/`
- `ui/src/lib/types/`
- colocated `*.test.ts(x)` files

## Invariants

- `ui/` is the active Vite + React + Tailwind console.
- Preserve route and URL-param contracts unless explicitly changing them.
- Generated contract types come from `scripts/generate_ui_contracts.py`; do not
  hand-edit generated TS contracts as the source of truth.
- Detection verdict is authoritative on `DetectionReport`; activation-layer
  `signal_summary` is a behavioral heuristic.
- Keep dense operator workflows usable; avoid marketing-style pages.

## Tests And Checks

- `make ui-types-check`
- `make ui-boundaries`
- `cd ui && npm run test`
- `cd ui && npm run lint`
- `make check-all` for broad UI/API contract work.

## Avoid

- Reintroducing `legacy_ui` or Streamlit-era docs as current behavior.
- Hiding degraded or inconclusive scan health behind clean visual states.
- Breaking `Provenance` or `Rule Draft` inspector surfaces during redesigns.
