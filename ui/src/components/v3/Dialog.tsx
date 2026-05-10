import { useEffect, type CSSProperties, type ReactNode } from "react";
import { createPortal } from "react-dom";

import { GhostButton } from "./Button";
import { Eyebrow } from "./Typography";
import { V3 } from "./tokens";

type DialogProps = {
  open: boolean;
  onClose: () => void;
  /** Top-of-dialog eyebrow tag, e.g. "Threshold breach". */
  eyebrow?: string;
  /** Bold dialog headline; renders inside a stacked layout under the eyebrow. */
  title: ReactNode;
  /** Optional supporting copy / structured content rendered under the title. */
  children?: ReactNode;
  /** Right-aligned action row. Defaults to a single "Close" ghost button. */
  actions?: ReactNode;
  /** Risk tone for the side accent rail; default `accent`. */
  tone?: "accent" | "warn" | "danger";
  /** Optional override on the panel width (default 520). */
  width?: number;
  style?: CSSProperties;
};

const TONE_RAIL: Record<NonNullable<DialogProps["tone"]>, string> = {
  accent: V3.coral,
  warn: V3.warn,
  danger: V3.danger,
};

/**
 * Generic v3-styled modal — used today for the VSIX threshold-breach
 * popup on the Marketplace download flow. Portal-mounted to the document
 * body so the backdrop sits above the rest of the app shell.
 *
 * Accessibility: the backdrop captures click-to-close; ESC closes too.
 * `aria-modal` is set on the inner panel so screen readers trap focus
 * inside it. Caller is responsible for the initial focus target —
 * leave the default and the dialog focuses its panel.
 */
export function Dialog({
  open,
  onClose,
  eyebrow,
  title,
  children,
  actions,
  tone = "accent",
  width = 520,
  style,
}: DialogProps) {
  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  const dialog = (
    <div
      role="presentation"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0, 0, 0, 0.65)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        backdropFilter: "blur(2px)",
        padding: 24,
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === "string" ? title : undefined}
        tabIndex={-1}
        style={{
          background: V3.paper2,
          border: `1px solid ${V3.rule}`,
          borderLeft: `4px solid ${TONE_RAIL[tone]}`,
          width: "100%",
          maxWidth: width,
          maxHeight: "calc(100vh - 48px)",
          overflowY: "auto",
          padding: 28,
          display: "flex",
          flexDirection: "column",
          gap: 18,
          color: V3.ink,
          ...style,
        }}
      >
        {eyebrow ? <Eyebrow>{eyebrow}</Eyebrow> : null}
        <div
          style={{
            fontSize: 22,
            lineHeight: 1.25,
            fontWeight: 600,
            color: V3.ink,
          }}
        >
          {title}
        </div>
        {children ? (
          <div style={{ fontSize: 14, color: V3.ink2, lineHeight: 1.55 }}>
            {children}
          </div>
        ) : null}
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: 10,
            marginTop: 8,
          }}
        >
          {actions ?? <GhostButton onClick={onClose}>Close</GhostButton>}
        </div>
      </div>
    </div>
  );

  return createPortal(dialog, document.body);
}
