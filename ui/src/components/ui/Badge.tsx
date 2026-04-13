import type { PropsWithChildren } from "react";

type Tone =
  | "default"
  | "accent"
  | "cyan"
  | "lime"
  | "amber"
  | "rose"
  | "success"
  | "warning"
  | "danger";

const tones: Record<Tone, string> = {
  default: "border-line bg-panelAlt/80 text-inkSoft",
  accent: "border-accent/25 bg-accent/12 text-accentSoft",
  cyan: "border-accent/25 bg-accent/12 text-accentSoft",
  lime: "border-success/25 bg-success/12 text-success",
  amber: "border-warning/25 bg-warning/12 text-warning",
  rose: "border-danger/25 bg-danger/12 text-danger",
  success: "border-success/25 bg-success/12 text-success",
  warning: "border-warning/25 bg-warning/12 text-warning",
  danger: "border-danger/25 bg-danger/12 text-danger",
};

export function Badge({
  children,
  tone = "default",
}: PropsWithChildren<{ tone?: Tone }>) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium tracking-[0.01em] ${tones[tone]}`}>
      {children}
    </span>
  );
}
