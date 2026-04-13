import type { PropsWithChildren, ReactNode } from "react";

export function Panel({
  children,
  className = "",
}: PropsWithChildren<{ className?: string }>) {
  return <section className={`panel ${className}`}>{children}</section>;
}

export function PanelHeader({
  title,
  description,
  right,
}: {
  title: string;
  description?: string;
  right?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
      <div className="min-w-0 space-y-2">
        <h2 className="text-balance font-display text-xl font-semibold tracking-tight text-ink">{title}</h2>
        {description ? <p className="max-w-2xl text-sm leading-6 text-mute sm:text-[15px]">{description}</p> : null}
      </div>
      {right ? <div className="shrink-0">{right}</div> : null}
    </div>
  );
}
