# UI Lane

**Last Updated:** 2026-05-17 (W15 close — W15-4 closed 2026-05-16 via 89e13e3: UI bounds bundle (U1/U2/U3 + U6) — `EventTimeline` / `EventDensityStrip` / `InteractionsSection` render caps with truncation indicators to prevent unbounded SVG rendering and DOM growth on adversarial event volumes; W15-5 closed 2026-05-17 via 43d6438: UI `/health` proxy (I2) — `ui/src/lib/api/client.ts` retains `api/` prefix for executor `/health` endpoint via Vite proxy passthrough, +14 behavioral cases in `ui/src/lib/api/client.test.ts`; W15-5 also pairs with I4 (lifecycle marker regex) on the executor side.)

Use this lane for the React/Vite analyst console, frontend contracts, route
behavior, report views, simulation UI, rules / settings / system surfaces,
shared v3 primitives, and UI tests.

## Start Here

- `ui/src/app/`
- `ui/src/features/evidence/` — evidence filter/query helpers
- `ui/src/features/marketplace/`
- `ui/src/features/reports/`
- `ui/src/features/reports/charts/` — bespoke SVG (`EventTimeline`,
  `InteractionGraph`)
- `ui/src/features/simulation/`
- `ui/src/features/simulation/charts/` — bespoke SVG (`ActivityBars`)
- `ui/src/features/rules/` — rule library + draft preview
- `ui/src/features/settings/` — operator preferences (general sections
  localStorage-backed; Security thresholds API-backed)
- `ui/src/features/system/` — service health (executor `/health` only)
- `ui/src/components/v3/` — shared primitive kitaplığı + design tokens
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
- v3 design tokens (`ui/src/components/v3/tokens.ts` and
  `ui/tailwind.config.js`) are the single source of truth for color,
  spacing, and typography; do not reintroduce ad-hoc inline tokens.
- Backend-pending surfaces must remain visibly marked (`Backend pending`
  badge or `data-feature-stub` attribute) until the matching backlog entry
  (`[BACKLOG ui-v3-1..8]`, `[BACKLOG ui-v3-13]`) lands.

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
