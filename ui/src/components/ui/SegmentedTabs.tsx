export interface SegmentOption {
  value: string;
  label: string;
}

export function SegmentedTabs({
  options,
  value,
  onChange,
}: {
  options: SegmentOption[];
  value: string;
  onChange: (next: string) => void;
}) {
  return (
    <div className="inline-flex items-center gap-1 rounded-[18px] border border-line bg-canvas/70 p-1.5 shadow-inset">
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
              selected
                ? "border border-lineStrong bg-surface text-ink shadow-inset"
                : "border border-transparent text-mute hover:bg-panelAlt hover:text-ink"
            }`}
            onClick={() => onChange(option.value)}
            type="button"
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
