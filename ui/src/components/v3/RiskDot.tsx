import type { CSSProperties } from "react";

import { RISK_COLOR, type Risk } from "./tokens";

type RiskDotProps = {
  risk: Risk;
  size?: number;
  style?: CSSProperties;
};

export function RiskDot({ risk, size = 10, style }: RiskDotProps) {
  return (
    <span
      aria-hidden
      style={{
        width: size,
        height: size,
        borderRadius: 0,
        background: RISK_COLOR[risk],
        display: "inline-block",
        flexShrink: 0,
        ...style,
      }}
    />
  );
}
