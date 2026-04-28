export interface SegmentOption {
  value: string;
  label: string;
}

export function SegmentedTabs({
  options,
  value,
  onChange,
  ariaLabel = "Section tabs",
}: {
  options: SegmentOption[];
  value: string;
  onChange: (next: string) => void;
  ariaLabel?: string;
}) {
  return (
    <div
      aria-label={ariaLabel}
      className="inline-flex items-center gap-0 rounded-none border border-line bg-canvas/70 p-0"
      role="tablist"
    >
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <button
            aria-selected={selected}
            key={option.value}
            className={`rounded-none border-r border-line px-3 py-2 text-sm font-medium transition last:border-r-0 ${
              selected
                ? "bg-surface text-ink"
                : "text-mute hover:bg-panelAlt hover:text-ink"
            }`}
            onClick={() => onChange(option.value)}
            role="tab"
            tabIndex={selected ? 0 : -1}
            type="button"
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
