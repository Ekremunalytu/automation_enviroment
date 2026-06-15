# W24 — operator-console-honesty (UI-only honesty stream, sequenced ahead of Stream 2)

`Last Updated: 2026-06-15`

`Branch: week24 (single branch — all development lands here; no per-item feature branches). Based on main @ 8250db0. NOT yet merged. Named stream — last_merged_weekly stays W22; phase.json active_stream = operator-console-honesty.`

`Owner: ekrem`

`Status: IN PROGRESS — branch opened 2026-06-15 off main 8250db0. H0 (doc-reconcile + active-stream flip) underway. Non-bar stream: closes no v1.0 bar; it removes operator-trust defects (decorative/dead console controls implying a backend effect that does not exist).`

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
| **H0** doc-reconcile + active-stream flip | — | 🔄 in progress | `phase.json` `active_stream` flipped `reliability-self-defense` → `operator-console-honesty` (tracker → this file); `last_merged_weekly` stays W22. `Active stream:` banner + `Last Updated` refreshed across canonical preambles. Doc-preamble parity/consistency/manifest/readme-pointer gates must stay green. No DB. |
| **H1** honest Settings | — | ⬜ todo | `SettingsPage.tsx`: backend-enforcement controls → `disabled` + "Not yet enforced" (generalize the `DangerRow` disabled pattern; add `disabled` to `ToggleRow`/`Segmented`/`Field` path); poolSize → read-only "Single active · serial"; fix intro copy; remove the general Save/Discard footer; fix the pre-existing `:472` `react-hooks/set-state-in-effect` lint error. Update `SettingsPage.test.tsx`. |
| **H2** honest System + health case-bug | — | ⬜ todo | `SystemPage.tsx`: render `isStub` MOCK markers on stub tiles/panels; rename `executor` card → `API` (update `data-testid` + test); fix tone case-bug (`status.toLowerCase() === "ok"`), update test to mock the real `"OK"`; mark INVENTORY mock; soften the headline. Update `SystemPage.test.tsx`. |
| **H3** real Dark/Light theme | — | ⬜ todo | `components/v3/tokens.ts`: convert `V3` hex → `var(--v3-*)` refs (40 consumers unchanged); theme stylesheet (`data-theme`: shift5 dark / parchment light / terminal) + provider from the persisted `theme` setting; re-enable the theme control. Audit + variable-ize hardcoded non-V3 colors (`SystemPage:297` `#000`, inline `rgba`). Provider + token unit tests. |
| **H1b** wire timeZone + density | — | ⬜ todo | New `lib/format/timestamp.ts` `formatTimestamp(value,{timeZone})` reading the operator timeZone; route the ~6–8 ad-hoc render sites; re-enable timeZone control. Thread density into real table/ledger row-heights; re-enable density control. Helper unit tests. **Optional trim point.** |
| **H4** close-out PR | — | ⬜ todo | Tracker freeze; pre-close checklist resolved/waived. **PR `week24 -> main` only on explicit user go-ahead.** |

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
| Pre-existing `SettingsPage.tsx:472` `react-hooks/set-state-in-effect` ESLint error (`SecuritySection` draft-reset effect) | Low (not in `make check-all`; W24 close-out gate requires `eslint` green) | **Fix in H1** — we edit this file anyway; verify the threshold form still resets on load / post-save echo |
| H1b is the widest-touch / highest-regression sub-item | — | sequenced last; trim candidate if the week runs long |

## Verification (running)

- Close-out gate: `cd ui && npm run test` (Settings/System tests updated) ·
  `npm run build` (`tsc -b && vite build`, real typecheck) · `npm run lint`
  (incl. the `:472` fix) · `make ui-boundaries` · `make ui-types-check` (DTOs
  unchanged) · `make check-all` (doc-preamble/canonical-preamble/
  README-phase-pointer/phase-manifest arch tests green after H0) ·
  `markdownlint` + `markdown-link-check` on changed docs.
- Browser-verify via the `ui-dev` vite preview on :5173 (automation_ui is an
  nginx static build, no HMR) with the API up on :8000.

## Operational notes

- `last_merged_weekly` stays **W22**; `active_stream = operator-console-honesty`.
  Named stream — W24 is a stream label, not a weekly close-out.
- No backend rebuild needed — UI-only; the `automation_ui` static build serves
  the changes (browser-verify via the `ui-dev` vite preview, not the :3000
  container).
