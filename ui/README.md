# ExTrace Web UI

`ui/` is now the primary analyst-facing frontend for ExTrace.

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

Key behavior:

- Report and simulation state are driven by URL search params.
- Provenance and rule authoring live in the right-side inspector.
- The SPA expects the backend API under `/api` by default.
- Docker runtime injects `window.__EXTRACE_CONFIG__` through `env.js`.

Local development:

```bash
cd ui
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000` by default.

Production/container flow:

- `npm run build` creates the static bundle.
- `ui/Dockerfile` builds the app with Node and serves it with Nginx.
- `ui/nginx/default.conf.template` provides SPA fallback and `/api` reverse proxying.
- `ui/docker/40-write-env.sh` writes runtime config into `env.js`.

Tests:

```bash
cd ui
npm run test
```
