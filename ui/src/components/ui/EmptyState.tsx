export function EmptyState({
  eyebrow,
  title,
  body,
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <div className="panel flex min-h-[220px] flex-col justify-center p-8 text-center sm:p-10">
      <div className="eyebrow">{eyebrow}</div>
      <h3 className="mt-4 text-balance font-display text-[40px] font-semibold tracking-[-0.04em] text-ink">{title}</h3>
      <p className="mx-auto mt-4 max-w-xl text-sm leading-6 text-mute sm:text-[15px]">{body}</p>
    </div>
  );
}
