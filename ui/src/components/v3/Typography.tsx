import type { CSSProperties, PropsWithChildren } from "react";

import { FONT_DISPLAY, FONT_MONO, V3 } from "./tokens";

type WithStyle = { style?: CSSProperties };

export function Eyebrow({ children, style }: PropsWithChildren<WithStyle>) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 10,
        fontFamily: FONT_MONO,
        fontSize: 10,
        fontWeight: 500,
        letterSpacing: "0.18em",
        textTransform: "uppercase",
        color: V3.ink3,
        ...style,
      }}
    >
      <span>{children}</span>
    </div>
  );
}

export function PageTitle({ children, style }: PropsWithChildren<WithStyle>) {
  return (
    <h1
      style={{
        fontFamily: FONT_DISPLAY,
        fontSize: 88,
        fontWeight: 800,
        letterSpacing: "-0.045em",
        lineHeight: 0.92,
        color: V3.ink,
        textWrap: "balance",
        margin: 0,
        ...style,
      }}
    >
      {children}
    </h1>
  );
}

export function SectionTitle({ children, style }: PropsWithChildren<WithStyle>) {
  return (
    <h2
      style={{
        fontFamily: FONT_DISPLAY,
        fontSize: 28,
        fontWeight: 700,
        letterSpacing: "-0.025em",
        lineHeight: 1.05,
        color: V3.ink,
        margin: 0,
        ...style,
      }}
    >
      {children}
    </h2>
  );
}
