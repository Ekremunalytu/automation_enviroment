import type { CSSProperties } from "react";

import { FONT_MONO, V3 } from "./tokens";

export type TabSpec<V extends string = string> = {
  value: V;
  label: string;
};

type TabsProps<V extends string> = {
  tabs: TabSpec<V>[];
  value: V;
  onChange: (value: V) => void;
  style?: CSSProperties;
  ariaLabel?: string;
};

export function Tabs<V extends string>({ tabs, value, onChange, style, ariaLabel }: TabsProps<V>) {
  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      style={{
        display: "flex",
        gap: 0,
        borderBottom: `1px solid ${V3.rule2}`,
        ...style,
      }}
    >
      {tabs.map((tab) => {
        const active = tab.value === value;
        return (
          <button
            key={tab.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(tab.value)}
            style={{
              background: "none",
              border: "none",
              padding: "12px 18px 13px",
              fontFamily: FONT_MONO,
              fontSize: 11,
              fontWeight: active ? 700 : 500,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: active ? V3.ink : V3.ink3,
              cursor: "pointer",
              position: "relative",
              transition: "color 140ms",
            }}
          >
            {tab.label}
            {active ? (
              <span
                aria-hidden
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  bottom: -1,
                  height: 3,
                  background: V3.coral,
                }}
              />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
