import type { CSSProperties } from "react";

import { V3 } from "./tokens";

type CrosshairProps = {
  size?: number;
  color?: string;
  style?: CSSProperties;
};

export function Crosshair({ size = 8, color = V3.ink, style }: CrosshairProps) {
  const total = size * 2;
  return (
    <svg width={total} height={total} style={style} aria-hidden>
      <line x1={0} y1={size} x2={total} y2={size} stroke={color} strokeWidth={1} />
      <line x1={size} y1={0} x2={size} y2={total} stroke={color} strokeWidth={1} />
    </svg>
  );
}
