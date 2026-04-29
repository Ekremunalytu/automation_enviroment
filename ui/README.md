# ExTrace Web UI

`Last Updated: 2026-04-29`

`ui/` is the primary analyst-facing frontend for ExTrace.

The UI is part of the same single-user sandbox deployment as the API and
executor. It is not intended to behave like a multi-tenant remote dashboard.

Stack:

- React 18
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- Apache ECharts

Routes:

- `/reports?report=latest&tab=overview`
- `/simulation?job=<jobId>&tab=live`
- `/marketplace?q=<query>`
- `/rules` — rule library overview + draft preview (save endpoint pending,
  see `[BACKLOG ui-v3-13]`)
- `/settings` — operator preferences, persists to `localStorage` until the
  settings API lands (see `[BACKLOG ui-v3-5]`)
- `/system` — service health + telemetry tiles; only the executor `/health`
  endpoint is wired today (see `[BACKLOG ui-v3-6]`)

Key behavior:

- report and simulation state are driven by URL search params
- backend-owned TypeScript contracts are generated into
  `ui/src/lib/types/contracts.ts` via `scripts/generate_ui_contracts.py`
- request logic lives in `ui/src/lib/api/client.ts`; adapters live under
  `ui/src/lib/adapters/`
- Docker runtime injects `window.__EXTRACE_CONFIG__` through `env.js`
- the simulation surface assumes only one active background analysis at a time
- shared v3 primitives live in `ui/src/components/v3/` (Panel, Tabs, Buttons,
  MetricCell, Badge, EmptyState, ProgressBar, RiskDot, Field, KVRow, Crosshair,
  LogoMark, Typography); design tokens are in `ui/src/components/v3/tokens.ts`
  and `ui/tailwind.config.js`
- bespoke SVG visuals (keyframe-driven, ECharts-independent) live under
  `ui/src/features/reports/charts/` (`EventTimeline`, `InteractionGraph`) and
  `ui/src/features/simulation/charts/` (`ActivityBars`)
- `AppShell` renders a collapsible left rail; backend-pending surfaces show
  explicit `Backend pending` badges or `data-feature-stub` markers

Local development:

```bash
cd ui
npm install
npm run dev
npm run test
npm run lint
npm run lint:boundaries
```

The Vite dev server proxies `/api` to `http://localhost:8000` by default.

Container flow:

- `npm run build` creates the static bundle
- `ui/Dockerfile` builds the app with Node and serves it with Nginx
- `ui/nginx/default.conf.template` provides SPA fallback and `/api` reverse
  proxying
- `ui/docker/40-write-env.sh` writes runtime config into `env.js`

Helpful repo-level checks:

```bash
make ui-types-check
make ui-boundaries
```

## Recent Changes

- 2026-04-29: v3 redesign minimal-completion landed on
  `feat/ui-v3-design-extrace-console`. Inspector drawer + Rule Draft
  preview, Run health + Coverage summary panels, Ledger Scenario
  tab. Pending backend contracts are tracked in
  [`documents/POST_POC_BACKLOG.md`](../documents/POST_POC_BACKLOG.md)
  under `[BACKLOG ui-v3-1]` … `[BACKLOG ui-v3-13]`.
