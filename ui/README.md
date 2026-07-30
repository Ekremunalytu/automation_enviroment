# ExTrace Web UI

`Last Updated: 2026-07-28`

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

- `/reports?report=latest&tab=overview` — report selector, evidence search,
  summary rail, Risk Radar, verdict decision band, and finding breakdowns
- `/reports?report=latest&tab=matrix` — dynamic/static rule activation matrix;
  static tool status is shown with the static band
- `/simulation?job=<jobId>&tab=live`
- `/marketplace?q=<query>` and `/marketplace?mode=offline` — online/offline
  intake; download/ingest stays available while dynamic analysis is off
- `/rules` — registry, rule-draft preview, and blacklist management (draft
  save endpoint pending; see `[BACKLOG ui-v3-13]`)
- `/settings` — appearance preferences are browser-local; security thresholds
  and the dynamic-analysis executor preference are API-backed
- `/system` — measured API, catalog, sandbox, and static-analyzer health plus
  local runtime inventory from `GET /api/system/health`

Key behavior:

- report and simulation state are driven by URL search params
- dynamic analysis defaults off and is operator-controlled through
  `GET|PUT /api/settings/executor/preferences`; when disabled, synchronous and
  background marketplace analysis still run the static pre-check and explicitly
  skip the five dynamic sandbox stages
- Marketplace download/ingest starts the applicable analysis pipeline; ready
  packages expose `Run static scan` while dynamic analysis is off and `Analyze`
  when both static and dynamic stages are available
- System data is read-only and measured from the API process, PostgreSQL
  catalog summary, and bounded Docker container inspection; the UI does not
  synthesize mock service values
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

- 2026-07-29: dynamic-analysis off no longer blocks marketplace analysis.
  Static pre-checks run to completion, dynamic sandbox steps are marked skipped,
  and the simulation view reports a truthful static-only completion.
- 2026-07-28: operator-console general fixes added a persisted, default-off
  dynamic-analysis preference; enforced the off-state in UI and both analysis
  APIs; replaced System mock cards with aggregate measured health; added a
  local readiness healthcheck for the static analyzer; and simplified the
  Marketplace, Rules, Reports, Settings, and System layouts. Reports now keeps
  verdict/action/scale inside Overview and places static tool statuses in the
  Rule Matrix static-band header.
- 2026-04-29: v3 redesign minimal-completion landed on
  `feat/ui-v3-design-extrace-console`. Inspector drawer + Rule Draft
  preview, Run health + Coverage summary panels, Ledger Scenario
  tab. Pending backend contracts are tracked in
  [`documents/POST_POC_BACKLOG.md`](../documents/POST_POC_BACKLOG.md)
  under `[BACKLOG ui-v3-1]` … `[BACKLOG ui-v3-13]`.
