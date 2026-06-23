// The V3 palette, as CSS-variable references. The concrete hex values live in
// `src/index.css`: `:root` holds the default "shift5" (dark) palette, and the
// `:root[data-palette="parchment"|"terminal"]` blocks override it. A single
// `data-palette` attribute on <html> (set by `lib/theme/theme.ts` from the
// operator's Settings → Appearance → Theme choice) therefore re-themes every
// inline `style={{ ... }}` consumer (40+ files) without touching them.
//
// NOTE: canvas-rendered charts (ECharts) cannot resolve `var(--…)`, so a few
// chart configs keep resolved hex and stay on the dark palette — see the W24
// H3 caveat in the tracker.
export const V3 = {
  paper: "var(--paper)",
  paper2: "var(--paper-2)",
  paper3: "var(--paper-3)",
  card: "var(--card)",
  bone: "var(--bone)",
  bone2: "var(--bone-2)",
  coral: "var(--coral)",
  coralDeep: "var(--coral-deep)",
  coralSoft: "var(--coral-soft)",
  ink: "var(--ink)",
  ink2: "var(--ink-2)",
  ink3: "var(--ink-3)",
  ink4: "var(--ink-4)",
  rule: "var(--rule)",
  rule2: "var(--rule-2)",
  accent: "var(--coral)",
  accentInk: "var(--paper)",
  accentBg: "var(--paper-3)",
  danger: "var(--danger)",
  dangerBg: "var(--danger-bg)",
  warn: "var(--warn)",
  warnBg: "var(--warn-bg)",
  ok: "var(--ok)",
  okBg: "var(--ok-bg)",
} as const;

export type V3Tone = "neutral" | "accent" | "ok" | "warn" | "danger";

export const BADGE_TONE: Record<V3Tone, { bg: string; fg: string; bd: string }> = {
  neutral: { bg: V3.paper3, fg: V3.ink2, bd: V3.rule2 },
  accent: { bg: V3.coralSoft, fg: V3.coralDeep, bd: V3.coral },
  ok: { bg: V3.okBg, fg: V3.ok, bd: "var(--ok-bd)" },
  warn: { bg: V3.warnBg, fg: V3.warn, bd: "var(--warn-bd)" },
  danger: { bg: V3.coral, fg: V3.paper, bd: V3.coral },
};

export type Risk = "low" | "medium" | "high";

export const RISK_COLOR: Record<Risk, string> = {
  low: V3.ok,
  medium: V3.warn,
  high: V3.coral,
};

export const FONT_DISPLAY = "'Manrope', sans-serif";
export const FONT_MONO = "'JetBrains Mono', monospace";
