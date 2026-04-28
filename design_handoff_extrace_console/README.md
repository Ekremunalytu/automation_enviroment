# Handoff: ExTrace Analyst Console

## Overview

ExTrace is an analyst-facing console for reviewing **activation reports**, running **simulations** in a sandbox, browsing an **extension marketplace**, configuring **system / executor** preferences, and managing **console settings**. The visual language is industrial / OT-security inspired — bold display typography, a coral signature accent on a near-black canvas, monospaced micro-labels, and dashed/animated SVG infographics (network graphs, radar plots, timelines).

## About the Design Files

The files in `design_files/` are **design references created in HTML + React (via Babel-in-browser)**. They are prototypes that show the intended look, structure, animations and interactions — they are **not production code to ship as-is**.

Your task is to **recreate these designs in the target codebase's existing environment** (React, Next.js, Vue, SwiftUI, native, etc.) using its established patterns, component library, routing, and state management. If no environment exists yet, choose the most appropriate framework — **React + Vite + TypeScript** is a natural fit because the prototype is already React-shaped.

Do **not**:

- Copy the inline `style={{ ... }}` blocks 1:1 into production. Translate them into your codebase's styling solution (CSS Modules, Tailwind, vanilla-extract, styled-components, etc.).
- Ship the `unpkg.com` Babel-standalone runtime — it's there only to make the prototype self-contained.
- Treat the in-file mock data (reports, services, devices) as a real schema. It's representative shape, not a contract.

Do:

- Lift exact colors, type scale, spacing, and animation timings from the prototype.
- Preserve layout structure (left rail + main canvas, panel composition, grid breakdowns).
- Preserve interaction behavior (sidebar collapse, tabs, page transitions, hover states).

## Fidelity

**High-fidelity (hifi).** Final colors, typography, spacing, and animations are intentional. Recreate pixel-perfectly using the codebase's existing libraries and patterns. Any deviation should be a deliberate adaptation to the target system's design tokens — not a guess.

---

## Application Structure

### Top-level shell

- **Persistent left rail** (sidebar) — always visible. Two states: expanded (280px) or collapsed (72px). Collapsed state persisted to `localStorage` under key `extrace-v3-rail`.
- **Main canvas** — a single-column page area, padding `48px 56px 96px`.
- **Five top-level pages**, switched by the rail. Active page persisted to `localStorage` under key `extrace-v3-page`.

### Pages

1. **Reports** (default) — list + detail view of activation reports
2. **Simulation** — sandbox scenario runner with live event stream
3. **Marketplace** — extension intake / catalog
4. **Settings** — console preferences (notifications, appearance, account)
5. **System** — executor + telemetry configuration

Page transitions use a 280ms `pageReveal` animation (4px slide-up + fade-in).

---

## Design Tokens

### Colors (exact hex)

```css
/* Surfaces — dark canvas */
--paper:      #0a0a0a   /* primary canvas / app background */
--paper-2:    #141414   /* raised surfaces (panels, inputs) */
--paper-3:    #1c1c1c   /* wells, panel headers, hover bg */
--card:       #0f0f0f   /* cards on paper */

/* Bone — light grey accent panels (used on light variants) */
--bone:       #d6d4d0
--bone-2:     #c5c2bd

/* Coral — signature accent */
--coral:      #ff5c42   /* primary accent, active states, danger */
--coral-deep: #e84a31   /* hover state on coral elements */
--coral-soft: #ffe4dd   /* accent backgrounds on light surfaces */

/* Ink — text on dark */
--ink:        #f4f1ea   /* primary text */
--ink-2:      #cfcbc2   /* secondary text */
--ink-3:      #8a8780   /* tertiary / micro labels */
--ink-4:      #5a5750   /* quaternary / disabled */

/* Rules — dividers */
--rule:       #2b2b2b   /* hairline on dark */
--rule-2:     #3a3a3a   /* slightly stronger hairline */

/* Status */
--ok:         #7ab088   /* success */
--ok-bg:      #13231a
--warn:       #d4a85a   /* warning */
--warn-bg:    #2a200f
--danger:     #ff5c42   /* same as coral — danger == accent */
--danger-bg:  #2a1612
```

The light-variant tokens (`--bone`, `--paper: #ededeb`, `--ink: #0a0a0a`) appear in `index.html`'s `<style>` block as `:root` defaults — they're the "light theme" baseline. The actual app overrides to dark via the `V2` JS object inside `Components.jsx`. Treat the dark palette as canonical for the analyst console.

### Typography

Two typefaces, loaded from Google Fonts:

- **Manrope** (sans, weights 400/500/600/700/800) — display, body, UI
- **JetBrains Mono** (mono, weights 400/500/600) — micro-labels, badges, code, KV pairs

Type scale:

| Role | Font | Size | Weight | Letter-spacing | Line-height | Notes |
|---|---|---|---|---|---|---|
| Page title | Manrope | 88px | 800 | -0.045em | 0.92 | `text-wrap: balance` |
| Section title | Manrope | 28px | 700 | -0.025em | 1.05 | |
| Display (large stat) | Manrope | 48px | 800 | -0.04em | 0.95 | tabular-nums |
| Nav item label | Manrope | 18px | 700 | -0.025em | — | uppercase |
| Body | Manrope | 13–14px | 400/500 | — | 1.5–1.6 | |
| Eyebrow / micro-label | JetBrains Mono | 10px | 500 | 0.18em | — | uppercase |
| Mono inline | JetBrains Mono | 11–12.5px | 400/500 | 0.04–0.08em | — | KV values, badges |
| Tab label | JetBrains Mono | 11px | 500/700 | 0.1em | — | uppercase |
| Button label | Manrope | 11–12px | 600/700 | 0.04–0.06em | — | uppercase |

Font feature: mono uses `font-feature-settings: "zero"` (slashed zero).

### Spacing & Layout

- All borders are **square** (`border-radius: 0`). No rounded corners anywhere except small dot indicators.
- Panel padding: `16px` interior, `14px 16px` headers.
- Page padding: `48px 56px 96px`.
- Sidebar widths: `280px` expanded, `72px` collapsed. Transition: `200ms ease`.
- Hairline borders: `1px solid var(--rule)` (`#2b2b2b`).
- Dashed borders use `border: 1px dashed var(--rule-2)`.

### Shadows

None. The aesthetic is flat — depth comes from surface tone steps (`paper` → `paper-2` → `paper-3`) and hairlines.

### Focus & selection

- `::selection { background: var(--coral); color: var(--ink); }`
- `:focus-visible { outline: 2px solid var(--coral); outline-offset: 2px; }`

### Scrollbar

Custom dark scrollbar, 10px wide, `#2a2a2a` thumb that turns coral on hover.

### Reduced motion

`@media (prefers-reduced-motion: reduce)` collapses all animation/transition durations to `0.01ms`.

---

## Animations

Defined as keyframes in `index.html`:

| Name | Duration | Easing | Properties | Used on |
|---|---|---|---|---|
| `pageReveal` | 280ms | ease-out | opacity 0→1, translateY 4px→0 | Page container on route change |
| `flowDash` | 2.4s (slow) / 1.4s (fast) | linear infinite | `stroke-dashoffset` -24 | Animated dashed flow lines on network graphs |
| `nodePulse` | 2.2s | ease-in-out infinite | SVG `r` 4→5.5, opacity 1→0.75 | Active graph nodes |
| `haloPulse` | 2.2s | ease-out infinite | SVG `r` 6→16, opacity 0.6→0 | Halo rings around nodes |
| `radarSweep` | 8s | linear infinite | rotate 0→360deg | Radar plot sweep arm |
| `radarBreath` | 4s | ease-in-out infinite | opacity 0.55→0.85 | Radar polygon fill |
| `tlPulse` | 2.4s | ease-out infinite | SVG `r` 4.5→16, opacity 0.9→0 | Timeline event dots |
| `laneSlide` | 500ms | cubic-bezier(.2,.8,.2,1) | translateX -8px→0, opacity 0→1 | Timeline lane on mount |

All `transform-origin: center` and (for SVG) `transform-box: fill-box` where rotation/scaling on SVG elements is involved.

---

## Left Rail (AppShell)

### Behavior

- Click the **logo / chevron mark** in the masthead → toggles collapsed/expanded.
- State persists to `localStorage['extrace-v3-rail']` (`'1'` or `'0'`).
- No separate toggle button — the masthead is the entire toggle target.

### Expanded state (280px)

- **Masthead** (top): logo mark + "EXTRACE" wordmark, padded `26px 22px 22px`, bottom hairline border.
- **Eyebrow row**: 14px coral horizontal line + "INDEX" eyebrow text, padded `18px 22px 8px`.
- **Nav list**: 5 items, each `14px 14px` padding, full-width buttons. Each item shows:
  - Item label (Manrope 18/700, uppercase, `-0.025em` letter-spacing)
  - Hint text below (mono 10px, ink-4 color) — e.g. "Activation reports & artifacts"
  - Right chevron `›` (14px)
- **Active state**: full coral background (`#ff5c42`), label + chevron go to `#0a0a0a`, hint goes to `rgba(0,0,0,0.6)`.
- **Hover state** (non-active): `paper-3` background, chevron turns coral.

### Collapsed state (72px)

- **Masthead**: logo mark only, centered, `24px 0 22px` padding.
- **Nav**: 5 buttons, each `14px 0`, centered. Each shows a 6px dot:
  - Active: `#0a0a0a` dot on coral background
  - Hover: coral dot on `paper-3` background
  - Idle: `ink-3` dot, transparent background
- Tooltip shows item label on hover (`title` attribute).

### Background

Rail is pure black `#000`, not `--paper`. Right-edge hairline `1px solid var(--rule)`.

---

## Shared Components

All defined in `design_files/Components.jsx` and exported to `window` for cross-script use. In the target codebase, these become real importable components.

### `<PageTitle>`

Manrope 88/800, `-0.045em`, `line-height: 0.92`, `text-wrap: balance`. Used once per page as the H1.

### `<SectionTitle>`

Manrope 28/700, `-0.025em`, `line-height: 1.05`. Section headers within a page.

### `<Eyebrow>`

Mono 10/500, `0.18em` letter-spacing, uppercase, `--ink-3` color. Used to label panels, fields, KV rows.

### `<SolidButton>`

- Coral background, ink-paper text (#0a0a0a)
- Padding: `12px 18px`
- Mono 12/700, `0.04em`, uppercase
- Square corners, no shadow
- Hover: background → `--coral-deep`
- Disabled: background → `--rule`, cursor `not-allowed`
- Transition: `background 140ms`

### `<GhostButton>`

- Transparent bg, ink text, `1px solid --rule-2` border
- Padding: `11px 16px`
- Mono 11/600, `0.06em`, uppercase
- Hover: `paper-3` bg, coral text + coral border
- Square corners

### `<LinkButton>`

- No bg, no border, no padding
- Mono 12/600, coral text
- Hover: `--coral-deep`, underline (offset 3px)

### `<Badge>` (5 tones)

- Inline-flex, mono 10/600, `0.08em`, uppercase
- Padding: `3px 8px`
- Square corners, 1px border
- Tones: `neutral` (paper-3 bg), `accent` (coral-soft / coral-deep), `ok`, `warn`, `danger` (solid coral fill)

### `<RiskDot>`

- Square block (NOT a circle — `border-radius: 0`), default 10×10
- Colors: `low` → ok green, `medium` → warn gold, `high` → coral

### `<Field>` (text input)

- Label above (eyebrow style), input below
- Input: `paper-2` bg, ink text, `1px solid --rule` border, `12px 14px` padding, 14px font
- Focus: border → coral. Hover (unfocused): border → `--rule-2`
- Optional `mono` prop swaps font to JetBrains Mono
- Square corners

### `<Panel>` / Card

- Background: `paper-2`
- Border: `1px solid --rule`
- Optional header: `paper-3` bg, `14px 16px` padding, bottom hairline
- Header contents: left = `<Eyebrow>` label, right = optional action slot
- Body: `16px` padding by default (controllable via `padded` prop)

### `<Tabs>`

- Horizontal flex, bottom `1px solid --rule-2` divider
- Each tab: mono 11px, uppercase, `0.1em` letter-spacing
- Inactive: `--ink-3`, weight 500
- Active: `--ink`, weight 700, **3px coral underline** flush with the bottom hairline
- Padding: `12px 18px 13px`

### `<MetricCell>`

- Eyebrow label on top
- Big number: Manrope 48/800, `-0.04em`, `tabular-nums`
- Optional sub-label below (mono 11, ink-3)
- Tone variants colorize the number (default ink, danger uses coral, etc.)

### `<KVRow>` (key-value)

- Two-column grid: 120px label + flex value
- Eyebrow-styled key, mono 12.5px value (or 13px sans if `mono={false}`)
- Bottom: `1px dashed --rule-2`
- Padding: `10px 0`

### `<EmptyState>`

- Dashed border container (`paper-2` bg)
- Padding: `56px 24px`
- Centered: eyebrow → 32px display title → 13px body → action button

### `<ProgressBar>`

- 6px tall, `paper-3` track with `1px solid --rule` border
- Coral fill (or tone color)
- Width transitions over 600ms ease

### `<Crosshair>`

- Tiny SVG crosshair (default 16×16) used as a precision marker on graphs / labels

### `<LogoMark>`

- 28×28 SVG showing two stacked chevrons:
  - Left chevron: `#ff5c42` (coral), `stroke-width: 2.5`, square caps, miter joins
  - Right chevron: `#f4f1ea` (ink/paper), same stroke
- Path: `M3 6 L11 14 L3 22` and `M14 6 L22 14 L14 22`

---

## Pages

### 1. Reports (default landing)

**File:** `design_files/ReportsPage.jsx` (~1500 lines — the largest page)

**Purpose:** Browse and inspect activation reports — security/operational events surfaced from monitored systems.

**Two views, toggled by selection state:**

- **List view** — table/grid of all reports with eyebrow filters, status badges, risk dots, timestamps.
- **Detail view** — opened when the user picks a report. Includes:
  - Report header with title, KV metadata block (timestamp, system, executor, severity)
  - **Network graph** — SVG with animated dashed flow lines (`flowDash`) and pulsing nodes (`nodePulse` + `haloPulse`)
  - **Risk radar** — polygon plot with sweep arm (`radarSweep`), breathing fill (`radarBreath`)
  - **Timeline** — horizontal lanes with pulsing event dots (`tlPulse`), each lane animates in (`laneSlide`)
  - Tabs to switch between sub-sections (overview / artifacts / raw / annotations)

**Key elements:**

- Heavy use of `<Panel>` with eyebrow labels — "BY KIND", "RISK MIX", "TIMELINE", etc. (NOT numbered — earlier iterations had `01 / 02 / 03` prefixes; the current canonical version removes them)
- `<MetricCell>` cluster at the top showing aggregate stats
- `<RiskDot>` and `<Badge>` to mark severity throughout

### 2. Simulation

**File:** `design_files/SimulationPage.jsx` (~330 lines)

**Purpose:** Run scenario simulations against the sandbox; watch live event stream.

**Layout:**

- Page title + scenario picker (left) and `<SolidButton>` "Run" / `<GhostButton>` "Reset" (right)
- Multi-panel grid:
  - Scenario configuration (left, `<Field>` inputs, scenario eyebrow)
  - Live event stream (right, mono-styled log lines, auto-scrolling)
  - Outcome metrics (`<MetricCell>` grid below)

### 3. Marketplace

**File:** `design_files/MarketplacePage.jsx` (~230 lines)

**Purpose:** Browse and intake extensions / integrations.

**Layout:**

- Page title + filter row (eyebrow categories like "ALL · DETECTORS · COLLECTORS · ENRICHERS")
- Grid of extension cards:
  - Eyebrow: extension category
  - Name (Manrope 24/700)
  - Vendor (mono 11)
  - Risk tone via `<Badge>`
  - "ANALYZE" CTA → calls `onAnalyze` prop, which navigates to Simulation

### 4. Settings

**File:** `design_files/SettingsPage.jsx` (~300 lines)

**Purpose:** Console preferences (not system/executor — that's its own page).

**Layout:**

- Left rail-within-page listing setting categories (notifications, appearance, account, …)
- Right detail panel with the active category's controls
- Categories no longer numbered (`01/02/03` removed in latest iteration)
- Form controls: `<Field>`, toggles, radio groups — all inheriting Panel + GhostButton styling

### 5. System

**File:** `design_files/SystemPage.jsx` (~200 lines)

**Purpose:** Executor & telemetry configuration; service health.

**Layout:**

- Service picker rail (cards with status dots — coral/warn/ok)
- Selected service detail: breadcrumb (`Service › <name>`, NO number prefix in canonical version), KV-style configuration block, telemetry sparkline / panel
- Status dots use the same color map as `<RiskDot>` but rendered as 8px circles in the rail

---

## Interactions & Behavior

### Navigation

- Click a rail nav item → `onNavigate(id)` → `setPage(id)` → `localStorage` write → page re-renders with `page-reveal` animation.
- Initial page read from `localStorage['extrace-v3-page']`, default `'reports'`.

### Sidebar collapse

- Click anywhere on the masthead (logo + wordmark area) → toggle.
- Width transition: `200ms ease` on the grid template columns.
- Persisted to `localStorage['extrace-v3-rail']`.

### Hover states (universal)

- Buttons: `140ms` background/border transition.
- Nav items: background fades to `paper-3`, chevron color fades to coral.
- Inputs: border `--rule` → `--rule-2` on hover, → coral on focus.

### Tab switching

- Pure local state; no URL sync in the prototype. **In production: sync to URL (e.g. `?tab=overview`)** for deep-linking.

### Marketplace → Simulation handoff

- `<MarketplacePage onAnalyze={() => navigate('simulation')} />` — the Analyze CTA on a card jumps to the Simulation page. Production should also pass which extension to pre-load.

### No real backend

The prototype uses inline mock arrays. Production must wire up real data sources for: report list, report detail, simulation event stream (likely SSE/WebSocket), marketplace catalog, system telemetry.

---

## State Management

What the prototype tracks via `useState` + `localStorage`:

- Active page (`'reports' | 'simulation' | 'marketplace' | 'settings' | 'system'`)
- Sidebar collapsed (boolean)
- Selected report (in Reports page)
- Active tab within a page
- Selected scenario / service (in Simulation / System)
- Form field values (Settings)

In production, consider:

- **Routing** for top-level page (React Router, TanStack Router, Next.js app router) — replace the `localStorage` page key with URL routes.
- **URL params** for selected report id, active tab, selected service.
- **Server state** for reports/marketplace/telemetry — TanStack Query or SWR fits naturally.
- **UI state** (sidebar collapsed, form drafts) — small zustand store or component-local state. Persist sidebar collapsed to `localStorage` as the prototype does.

---

## Assets

The prototype contains **no external images, icons, or fonts beyond Google Fonts**. All visuals are:

- SVG drawn inline (logo, network graphs, radar, timeline, crosshair)
- CSS keyframe animations
- Typography (Manrope + JetBrains Mono from Google Fonts)

If your codebase already has an icon system (Lucide, Heroicons, custom SVG sprite), use that. The prototype does not introduce a third-party icon library — match its restraint.

---

## Files in `design_files/`

```text
design_files/
├── index.html              # Entry: theme tokens (CSS), keyframes, root mount, page router
├── Components.jsx          # Shared components + V2 token object (~340 lines)
├── AppShell.jsx            # Left rail + main canvas + nav (~160 lines)
├── ReportsPage.jsx         # Reports list + detail view (~1500 lines)
├── SimulationPage.jsx      # Simulation page (~330 lines)
├── MarketplacePage.jsx     # Marketplace page (~230 lines)
├── SettingsPage.jsx        # Settings page (~300 lines)
└── SystemPage.jsx          # System / executor page (~200 lines)
```

To preview the prototype: open `design_files/index.html` in a browser. It loads React 18.3.1 + Babel-standalone from unpkg and renders the full app.

---

## Recommended Implementation Path

1. **Set up the design system layer first.** Create design tokens (colors, type, spacing, animations) as either CSS variables (matching the names above) or Tailwind theme extensions. Get the `Manrope` + `JetBrains Mono` fonts loading.

2. **Build the shared components** in `Components.jsx` order: typography primitives → buttons → badges → form fields → Panel → Tabs → MetricCell → KVRow → EmptyState → ProgressBar → LogoMark. These unblock every page.

3. **Build AppShell** with routing wired in. Get the collapse/expand and active-state styling exactly right — it's seen on every page.

4. **Pages, simplest first:** Marketplace → Settings → System → Simulation → Reports. Reports is the largest and uses the most graphics; doing it last lets the other pages stress-test the components.

5. **SVG graphics in Reports** (network graph, radar, timeline) are bespoke. Re-implement as React components that take data props — don't paste the prototype's hard-coded SVG.

6. **Wire real data sources** — the prototype's mock arrays are placeholders. Each page will need an API contract.

7. **Test reduced motion** — confirm the `prefers-reduced-motion` rule still neuters animations after refactor.
