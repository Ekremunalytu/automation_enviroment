# W24 — operator-console-honesty (UI-only honesty stream, sequenced ahead of Stream 2)

`Last Updated: 2026-07-29`

`Branch: week24 (single branch — all development landed here; no per-item feature branches). Based on main @ 8250db0. MERGED to main via PR #36 (week24 -> main, 1e3fba6) on 2026-06-23. Named stream — last_merged_weekly stays W22.`

`Owner: ekrem`

`Status: MERGED — all sub-items H0–H1b landed on week24 (272e9f8 H0 · 111bf6b H1 · fc57c59 H2 · 844df3d H3 · 200933c H1b), then PR #36 merged to main as 1e3fba6 on 2026-06-23. UI suite 155 green (+2 time-zone adapter integration tests added at close-out, see Verification); tsc/eslint/ui-boundaries/ui-types-check clean; doc-preamble parity/consistency/manifest/readme-pointer arch gates green; browser-verified via the ui-dev Vite preview against the live API (Settings honesty + live theme/density/time-zone, light↔dark switch with no dark islands, System API card real "OK" healthy tone + MOCK markers). Non-bar stream: closes no v1.0 bar; it removes operator-trust defects (decorative/dead console controls implying a backend effect that does not exist). phase.json.active_stream named operator-console-honesty while this stream was open and later returned to null after W26; the current pointer names static-analysis-artifact-precision.`

> Scope locked to **UI + docs only** (per the 2026-06-15 planning session):
> **NO backend / DB / detection / executor. No Alembic migration. No
> contract/DTO change.** Canonical plan:
> [`v1-roadmap.md`](v1-roadmap.md) §5 "Next-Stream Plan (2026-06-15)".
> Stable IDs: `POST_POC_BACKLOG.md` —
> `[CLEANUP settings-decorative-controls-honesty]`,
> `[CLEANUP system-mock-status-honesty]`, `[GOAL light-dark-theme]`.

## Goal

Make every analyst-facing control on Settings + System either **honest-and-real**
or **honestly disabled** — nothing implies an effect it does not have. Verified
defects against `main @ 8250db0`:

- **Settings** — `general` (operatorName, timeZone, theme, density), `executor`
  (autoAnalyze, strictNet, **poolSize**, jobTimeout), `telemetry` (verboseLogs,
  retainArtifacts, retention, buffer) all write **`localStorage` only**; only
  `SecuritySection` is backend-wired. `poolSize` contradicts the single-active
  serial queue (Non-Goal §8 / B3). DANGER rows already honestly `disabled`.
- **System** — `isStub` is set on catalog/sandbox/telemetry cards but **never
  rendered**; mock `synced`/`live` + fabricated metrics read as real; INVENTORY
  hardcoded; "All systems operational." headline contradicts 3/4 mock cards.
- **Real bug** — `SystemPage.tsx:116` compares `status === "ok"` but the backend
  emits `HEALTH_STATUS = "OK"` (`appcore/api/config.py:87`); the one real card
  renders amber `warn` even when healthy. The existing test masks it by mocking
  lowercase `"ok"`.

**Scope chosen (2026-06-15, user):** fullest option — honesty (H0–H2) **+ real
theme (H3) + H1b** (timeZone → timestamps, density → row-height).

**Guiding split:** presentation-only controls (theme, density, timeZone) are made
**REAL** client-side (persisted in the existing `extrace-v3-settings`
`localStorage`); backend-enforcement controls stay **disabled "Not yet
enforced"** — making them "work" client-side would be a new lie.

## Sub-item status

| Sub-item | Closes | Status | Note |
|---|---|---|---|
| **H0** doc-reconcile + active-stream flip | — | ✅ done (272e9f8) | `phase.json` `active_stream` flipped `reliability-self-defense` → `operator-console-honesty` (tracker → this file); `last_merged_weekly` stays W22. `Active stream:` banner + `Last Updated` refreshed across all canonical preambles. Doc-preamble parity/consistency/manifest/readme-pointer + token-budget + cross-doc arch gates green (87 tests). No DB. |
| **H1** honest Settings | — | ✅ done (111bf6b) | `SettingsPage.tsx`: backend-enforcement controls → `disabled` + "Not yet enforced" `Badge` (`ToggleRow`/`Segmented`/`Field` gained `disabled`/`note`); poolSize → read-only "Single active · serial" `ReadonlyRow`; honest intro; general Save/Discard footer + the whole `localStorage` machinery removed; the pre-existing `:472` `react-hooks/set-state-in-effect` fixed via render-time draft sync. `SettingsPage.test.tsx` updated. |
| **H2** honest System + health case-bug | — | ✅ done (fc57c59) | `SystemPage.tsx`: `MOCK` markers on stub tiles + a "Mock data — not measured" panel note + mock log dot; `executor` card renamed `API` (`data-testid` `service-tile-api`); INVENTORY badged Mock; headline → "Appliance status.". Case-bug fixed via a pure, unit-tested `apiHealthTone` helper (`systemHealth.ts`) — `status.toLowerCase() === "ok"`; the test now mocks the real `"OK"`. Browser-verified: live API card shows "OK" healthy. |
| **H3** real Dark/Light theme | — | ✅ done (844df3d) | `tokens.ts`: `V3` now references the **existing** `index.css` CSS vars (`var(--paper)` …) — repointed, not a new namespace — so 40 consumers are untouched. `index.css` gains `:root[data-palette="parchment"\|"terminal"]` blocks (default shift5 = bare `:root`, so dark is pixel-identical). `lib/theme/theme.ts` (`useSyncExternalStore`) persists + paints `<html data-palette>`; `main.tsx` `initTheme()`. Theme control live. Two `#000` islands (AppShell, System log) → `var(--paper)`. **Caveat:** ECharts canvas configs keep hex (cannot read CSS vars) — dark; deferred. Theme + token unit tests. Browser-verified light↔dark. |
| **H1b** wire timeZone + density | — | ✅ done (200933c) | `lib/settings/presentation.ts` (store + `useDensity`/`useTimeZone` + `resolveTimeZone`); `main.tsx` `initPresentation()`. **timeZone:** `resolveTimeZone()` ("local" → undefined, so the default is identical to prior behavior) injected into all 4 timestamp formatters (`adapters/report.ts`, `adapters/job.ts`, `ReportsPage` modified-stamp, System log); control re-enabled as a curated IANA `<select>`. **density:** a `--v3-row-pad-y` CSS var driven by `<html data-density>` sets the `EvidenceLedger` row height; control re-enabled. Descriptions narrowed to exactly what is wired. Presentation-store unit tests. |
| **H4** close-out PR | — | ✅ merged via PR #36 (`1e3fba6`) | Close-out gate green (UI **155** tests · tsc · eslint · ui-boundaries · ui-types-check · doc-preamble arch gates · markdownlint); browser-verified. At close-out, 2 time-zone adapter integration tests were added (`job.test.ts`/`report.test.ts`) to guard the `resolveTimeZone()` wiring that the per-store unit tests left uncovered. |

## Out of scope / deferred

- Backend-enforcement controls stay **disabled** — no client-side fakes.
- **Server-persisting** operator settings → Stream 9 (`operator-settings-ops`,
  post-v1.0). W24 keeps `localStorage`.
- DANGER destructive actions stay disabled → Stream 9 (factory-reset
  hard-blocked until B10 backup/restore).
- Non-UI audit cleanups (`[BUG report-field-redaction-completeness]`,
  `[CLEANUP pragma-ratchet-docstring]`,
  `[CLEANUP event-attempt-validate-assignment]`) are Python/backend → **not** on
  this UI-only stream.

## Pre-close checklist

Bucketed, evidence-cited, blocking flags noted. Resolve/waive before close-out.

| Item | Severity | Disposition |
|---|---|---|
| Pre-existing `SettingsPage.tsx:472` `react-hooks/set-state-in-effect` ESLint error (`SecuritySection` draft-reset effect) | Low (not in `make check-all`; W24 close-out gate requires `eslint` green) | **RESOLVED — H1 (111bf6b)**: render-time draft sync replaces the effect; threshold form still resets on load / post-save echo (SecuritySection deep-link + error tests green) |
| H1b is the widest-touch / highest-regression sub-item | — | **RESOLVED — H1b (200933c)** delivered in a contained, honest form; default zone "local" keeps adapter tests unchanged; UI suite green (count in Verification) |

### Known limitations (honest carve-outs; not blocking)

- **Theme — ECharts charts stay dark.** Canvas configs (e.g.
  `InspectorSections` relations tree) cannot read CSS variables, so they keep
  resolved hex and render on the dark palette under any theme. Runtime chart
  re-theming is deferred (would need `getComputedStyle` resolution + redraw on
  theme change).
- **Density is scoped to the `EvidenceLedger`** (the primary ledger); the
  control description says exactly that. Extending `--v3-row-pad-y` to other
  tables is a later pass.
- **Time-zone reactivity is render-time.** Adapter-baked timestamps adopt the
  zone on the next data (re)load / poll; component-rendered stamps update on the
  next render. The control claims "Timestamps render in this zone", which holds.

## Verification (complete)

- **UI suite 155 green** (27 files; +24 over the pre-W24 131: Settings/System
  rewrites, `apiHealthTone`, theme store, token map, presentation store, and 2
  close-out time-zone integration tests).
- **Close-out integration coverage (added 2026-06-23).** The presentation store
  (`resolveTimeZone`/`setTimeZone`) and the adapter timestamp formatters were
  unit-tested in isolation, so the *seam* between them — that the store's zone
  actually reaches `formatDate`/`formatTimestamp` — was untested; dropping
  `timeZone: resolveTimeZone()` from an adapter would have passed silently. Added
  a differential test to `lib/adapters/job.test.ts` (`lastUpdatedLabel`) and
  `lib/adapters/report.test.ts` (`evidence[].timestampDisplay`): the same instant
  rendered under UTC vs `Asia/Tokyo` must differ (10:00 vs 19:00). Density's CSS
  var (`--v3-row-pad-y`) is not jsdom-resolvable; the store's `data-density`
  paint is already unit-tested and the live row-height is browser-verified —
  carried as an honest carve-out, not a gap.
- `tsc -b` clean · `eslint` clean (incl. the `:472` fix) · `make ui-boundaries`
  clean · `make ui-types-check` clean (no DTO change).
- Doc gates: doc-preamble parity/consistency, phase-manifest schema,
  README-phase-pointer, token-budget, cross-doc parity — all green;
  `markdownlint` + Markdown-Link-Check green (pre-commit) on the changed docs.
- **Browser-verified** via the `ui-dev` vite preview on :5173 against the live
  API (:8000, `/api/health` → `"OK"`): Settings shows disabled enforcement
  controls + "Not yet enforced", live theme/density/time-zone, no save footer;
  light (parchment) ↔ dark (shift5) switch persists with **no dark islands**
  (the formerly-`#000` sidebar themes); System shows the real **API** card with
  the **OK healthy** tone + `MOCK` markers on the three stub cards + INVENTORY.
  No console/server errors.
- **Not run** (UI-only stream, no backend change): the full `make check-all`
  Python suite / Docker. The doc-preamble arch gates that `check-all` includes
  were run directly and are green.

## Operational notes

- `last_merged_weekly` stays **W22**. While this stream was open,
  `active_stream = operator-console-honesty`; it later returned to `null`
  after W26, and the current pointer names
  `static-analysis-measurement-foundation`.
  Named stream — W24 is a stream label, not a weekly close-out.
- No backend rebuild needed — UI-only; the `automation_ui` static build serves
  the changes (browser-verify via the `ui-dev` vite preview, not the :3000
  container).
