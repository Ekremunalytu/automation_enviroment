import type { CSSProperties } from "react";

import { BADGE_TONE, V3, type V3Tone } from "./tokens";

type ProgressBarProps = {
  pct?: number;
  tone?: V3Tone | "ink";
  style?: CSSProperties;
};

export function ProgressBar({ pct = 0, tone = "ink", style }: ProgressBarProps) {
  const fillColor = tone === "ink" ? V3.coral : BADGE_TONE[tone].fg;
  const clamped = Math.max(0, Math.min(100, pct));
  return (
    <div
      style={{
        height: 6,
        background: V3.paper3,
        borderRadius: 0,
        position: "relative",
        overflow: "hidden",
        border: `1px solid ${V3.rule}`,
        ...style,
      }}
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: `${clamped}%`,
          background: fillColor,
          transition: "width 600ms ease",
        }}
      />
    </div>
  );
}
