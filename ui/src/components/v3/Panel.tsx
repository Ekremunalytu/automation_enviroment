import type { CSSProperties, PropsWithChildren, ReactNode } from "react";

import { Eyebrow } from "./Typography";
import { V3 } from "./tokens";

type PanelProps = PropsWithChildren<{
  label?: string;
  right?: ReactNode;
  padded?: boolean;
  style?: CSSProperties;
  bodyStyle?: CSSProperties;
}>;

export function Panel({ children, label, right, padded = true, style, bodyStyle }: PanelProps) {
  const hasHeader = Boolean(label) || Boolean(right);
  return (
    <section
      style={{
        background: V3.paper2,
        border: `1px solid ${V3.rule}`,
        borderRadius: 0,
        position: "relative",
        ...style,
      }}
    >
      {hasHeader ? (
        <header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "14px 16px",
            borderBottom: `1px solid ${V3.rule}`,
            gap: 12,
            background: V3.paper3,
          }}
        >
          {label ? <Eyebrow>{label}</Eyebrow> : <span />}
          {right ? <div>{right}</div> : null}
        </header>
      ) : null}
      <div style={padded ? { padding: 16, ...bodyStyle } : bodyStyle}>{children}</div>
    </section>
  );
}
