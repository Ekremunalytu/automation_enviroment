import type { CSSProperties, ReactNode } from "react";

import { Eyebrow } from "./Typography";
import { BADGE_TONE, FONT_DISPLAY, FONT_MONO, V3, type V3Tone } from "./tokens";

type MetricCellProps = {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  tone?: V3Tone;
  align?: "left" | "right" | "center";
  style?: CSSProperties;
};

export function MetricCell({ label, value, sub, tone = "neutral", align = "left", style }: MetricCellProps) {
  const t = BADGE_TONE[tone];
  const numberColor = tone === "neutral" ? V3.ink : tone === "danger" ? V3.coral : t.fg;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, textAlign: align, ...style }}>
      <Eyebrow>{label}</Eyebrow>
      <div
        style={{
          fontFamily: FONT_DISPLAY,
          fontSize: 48,
          fontWeight: 800,
          letterSpacing: 0,
          lineHeight: 0.95,
          color: numberColor,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {value}
      </div>
      {sub ? (
        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: V3.ink3,
            letterSpacing: "0.04em",
          }}
        >
          {sub}
        </div>
      ) : null}
    </div>
  );
}
