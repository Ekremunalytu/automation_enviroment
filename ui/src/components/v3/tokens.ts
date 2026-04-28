export const V3 = {
  paper: "#0a0a0a",
  paper2: "#141414",
  paper3: "#1c1c1c",
  card: "#0f0f0f",
  bone: "#d6d4d0",
  bone2: "#c5c2bd",
  coral: "#ff5c42",
  coralDeep: "#e84a31",
  coralSoft: "#ffe4dd",
  ink: "#f4f1ea",
  ink2: "#cfcbc2",
  ink3: "#8a8780",
  ink4: "#5a5750",
  rule: "#2b2b2b",
  rule2: "#3a3a3a",
  accent: "#ff5c42",
  accentInk: "#0a0a0a",
  accentBg: "#1c1c1c",
  danger: "#ff5c42",
  dangerBg: "#2a1612",
  warn: "#d4a85a",
  warnBg: "#2a200f",
  ok: "#7ab088",
  okBg: "#13231a",
} as const;

export type V3Tone = "neutral" | "accent" | "ok" | "warn" | "danger";

export const BADGE_TONE: Record<V3Tone, { bg: string; fg: string; bd: string }> = {
  neutral: { bg: V3.paper3, fg: V3.ink2, bd: V3.rule2 },
  accent: { bg: V3.coralSoft, fg: V3.coralDeep, bd: V3.coral },
  ok: { bg: V3.okBg, fg: V3.ok, bd: "#2a4a36" },
  warn: { bg: V3.warnBg, fg: V3.warn, bd: "#5c4a22" },
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
