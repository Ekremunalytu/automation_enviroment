export function StatBlock({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "accent" | "cyan" | "lime" | "amber" | "rose" | "success" | "warning" | "danger";
}) {
  const toneMap = {
    default: "bg-lineStrong text-inkSoft",
    accent: "bg-accent text-accentSoft",
    cyan: "bg-accent text-accentSoft",
    lime: "bg-success text-success",
    amber: "bg-warning text-warning",
    rose: "bg-danger text-danger",
    success: "bg-success text-success",
    warning: "bg-warning text-warning",
    danger: "bg-danger text-danger",
  };
  return (
    <div className="metric-tile">
      <div className="flex items-center justify-between gap-3">
        <div className="micro-label">{label}</div>
        <span className={`inline-flex h-8 min-w-8 items-center justify-center rounded-full px-2 text-xs font-semibold ${toneMap[tone]}`}>
          ●
        </span>
      </div>
      <div className="mt-4 font-display text-[30px] font-semibold tracking-tight text-ink tabular-nums">{value}</div>
    </div>
  );
}
