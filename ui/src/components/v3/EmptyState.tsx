import type { CSSProperties, ReactNode } from "react";

import { Eyebrow } from "./Typography";
import { FONT_DISPLAY, V3 } from "./tokens";

type EmptyStateProps = {
  eyebrow?: string;
  title: string;
  body?: ReactNode;
  action?: ReactNode;
  style?: CSSProperties;
};

export function EmptyState({ eyebrow, title, body, action, style }: EmptyStateProps) {
  return (
    <div
      style={{
        padding: "56px 24px",
        textAlign: "center",
        border: `1px dashed ${V3.rule2}`,
        borderRadius: 0,
        background: V3.paper2,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
        ...style,
      }}
    >
      {eyebrow ? <Eyebrow>{eyebrow}</Eyebrow> : null}
      <div
        style={{
          fontFamily: FONT_DISPLAY,
          fontSize: 32,
          fontWeight: 700,
          color: V3.ink,
          letterSpacing: "-0.03em",
          lineHeight: 1,
        }}
      >
        {title}
      </div>
      {body ? (
        <div
          style={{
            fontSize: 13,
            color: V3.ink3,
            maxWidth: 380,
            lineHeight: 1.6,
          }}
        >
          {body}
        </div>
      ) : null}
      {action}
    </div>
  );
}
