import type { CSSProperties } from "react";

import { V3 } from "./tokens";

type LogoMarkProps = {
  size?: number;
  style?: CSSProperties;
};

export function LogoMark({ size = 28, style }: LogoMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 28 28"
      fill="none"
      style={style}
      aria-hidden
    >
      <path
        d="M3 6 L11 14 L3 22"
        stroke={V3.coral}
        strokeWidth={2.5}
        strokeLinecap="square"
        strokeLinejoin="miter"
        fill="none"
      />
      <path
        d="M14 6 L22 14 L14 22"
        stroke={V3.ink}
        strokeWidth={2.5}
        strokeLinecap="square"
        strokeLinejoin="miter"
        fill="none"
      />
    </svg>
  );
}
