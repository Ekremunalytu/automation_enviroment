import type { CSSProperties, PropsWithChildren } from "react";

import { BADGE_TONE, FONT_MONO, type V3Tone } from "./tokens";

type BadgeProps = PropsWithChildren<{
  tone?: V3Tone;
  style?: CSSProperties;
}>;

export function Badge({ children, tone = "neutral", style }: BadgeProps) {
  const t = BADGE_TONE[tone];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        background: t.bg,
        color: t.fg,
        border: `1px solid ${t.bd}`,
        padding: "3px 8px",
        fontFamily: FONT_MONO,
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        borderRadius: 0,
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {children}
    </span>
  );
}
