import type { CSSProperties, ReactNode } from "react";

import { FONT_MONO, V3 } from "./tokens";

type KVRowProps = {
  k: ReactNode;
  v: ReactNode;
  mono?: boolean;
  style?: CSSProperties;
};

export function KVRow({ k, v, mono = true, style }: KVRowProps) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "120px 1fr",
        gap: 12,
        padding: "10px 0",
        borderBottom: `1px dashed ${V3.rule2}`,
        alignItems: "baseline",
        ...style,
      }}
    >
      <div
        style={{
          fontFamily: FONT_MONO,
          fontSize: 10,
          fontWeight: 500,
          letterSpacing: "0.18em",
          textTransform: "uppercase",
          color: V3.ink3,
        }}
      >
        {k}
      </div>
      <div
        style={{
          fontFamily: mono ? FONT_MONO : "'Manrope', sans-serif",
          fontSize: mono ? 12.5 : 13,
          color: V3.ink2,
          wordBreak: "break-all",
        }}
      >
        {v}
      </div>
    </div>
  );
}
