import { useState, type ButtonHTMLAttributes, type CSSProperties, type PropsWithChildren } from "react";

import { FONT_DISPLAY, FONT_MONO, V3 } from "./tokens";

type ButtonProps = PropsWithChildren<{
  onClick?: ButtonHTMLAttributes<HTMLButtonElement>["onClick"];
  disabled?: boolean;
  type?: ButtonHTMLAttributes<HTMLButtonElement>["type"];
  style?: CSSProperties;
  ariaLabel?: string;
  title?: string;
  "data-feature-stub"?: string;
}>;

export function SolidButton({ children, onClick, disabled, type = "button", style, ariaLabel }: ButtonProps) {
  const [hover, setHover] = useState(false);
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        background: disabled ? V3.rule : hover ? V3.coralDeep : V3.coral,
        color: V3.paper,
        border: "none",
        padding: "12px 18px",
        fontFamily: FONT_DISPLAY,
        fontSize: 12,
        fontWeight: 700,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
        cursor: disabled ? "not-allowed" : "pointer",
        transition: "background 140ms",
        borderRadius: 0,
        ...style,
      }}
    >
      {children}
    </button>
  );
}

export function GhostButton({
  children,
  onClick,
  disabled,
  type = "button",
  style,
  ariaLabel,
  title,
  "data-feature-stub": dataFeatureStub,
}: ButtonProps) {
  const [hover, setHover] = useState(false);
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      title={title}
      data-feature-stub={dataFeatureStub}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        background: hover ? V3.paper3 : "transparent",
        color: hover ? V3.coral : V3.ink,
        border: `1px solid ${hover ? V3.coral : V3.rule2}`,
        padding: "11px 16px",
        fontFamily: FONT_MONO,
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        cursor: disabled ? "not-allowed" : "pointer",
        transition: "all 140ms",
        borderRadius: 0,
        opacity: disabled ? 0.5 : 1,
        ...style,
      }}
    >
      {children}
    </button>
  );
}

export function LinkButton({ children, onClick, disabled, type = "button", style, ariaLabel }: ButtonProps) {
  const [hover, setHover] = useState(false);
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: "transparent",
        border: "none",
        padding: 0,
        color: hover ? V3.coralDeep : V3.coral,
        fontFamily: FONT_MONO,
        fontSize: 12,
        fontWeight: 600,
        cursor: disabled ? "not-allowed" : "pointer",
        textDecoration: hover ? "underline" : "none",
        textUnderlineOffset: "3px",
        letterSpacing: "0.02em",
        opacity: disabled ? 0.5 : 1,
        ...style,
      }}
    >
      {children}
    </button>
  );
}
