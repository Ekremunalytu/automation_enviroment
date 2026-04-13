import { useDeferredValue } from "react";

export interface EvidenceFilterState {
  kinds: string[];
  actors: string[];
  collectors: string[];
  scenarios: string[];
  sensitiveOnly: boolean;
  search: string;
}

export function FilterRail({
  filters,
  options,
  onChange,
  title,
  description,
  showSearch = true,
}: {
  filters: EvidenceFilterState;
  options: {
    kinds: string[];
    actors: string[];
    collectors: string[];
    scenarios: string[];
  };
  onChange: (next: EvidenceFilterState) => void;
  title?: string;
  description?: string;
  showSearch?: boolean;
}) {
  const deferredSearch = useDeferredValue(filters.search);
  const updateList = (key: keyof Pick<EvidenceFilterState, "kinds" | "actors" | "collectors" | "scenarios">, raw: string) => {
    onChange({
      ...filters,
      [key]: raw ? [raw] : [],
    });
  };
  const hasFilters =
    filters.kinds.length ||
    filters.actors.length ||
    filters.collectors.length ||
    filters.scenarios.length ||
    filters.sensitiveOnly ||
    Boolean(filters.search);

  return (
    <div className="space-y-6">
      {title || description ? (
        <div className="space-y-2">
          {title ? <div className="font-display text-lg font-semibold tracking-tight text-ink">{title}</div> : null}
          {description ? <p className="text-sm leading-6 text-mute sm:text-[15px]">{description}</p> : null}
        </div>
      ) : null}

      {hasFilters ? (
        <button
          className="ghost-button w-full"
          onClick={() =>
            onChange({
              kinds: [],
              actors: [],
              collectors: [],
              scenarios: [],
              sensitiveOnly: false,
              search: "",
            })
          }
          type="button"
        >
          Reset filters
        </button>
      ) : null}

      <div className="space-y-4">
        <label className="block space-y-2">
          <span className="micro-label">Kind</span>
          <select
            onChange={(event) => updateList("kinds", event.target.value)}
            className="field-control"
            value={filters.kinds[0] || ""}
          >
            <option value="">All kinds</option>
            {options.kinds.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="block space-y-2">
          <span className="micro-label">Actor</span>
          <select
            onChange={(event) => updateList("actors", event.target.value)}
            className="field-control"
            value={filters.actors[0] || ""}
          >
            <option value="">All actors</option>
            {options.actors.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="block space-y-2">
          <span className="micro-label">Collector</span>
          <select
            onChange={(event) => updateList("collectors", event.target.value)}
            className="field-control"
            value={filters.collectors[0] || ""}
          >
            <option value="">All collectors</option>
            {options.collectors.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="block space-y-2">
          <span className="micro-label">Scenario</span>
          <select
            onChange={(event) => updateList("scenarios", event.target.value)}
            className="field-control"
            value={filters.scenarios[0] || ""}
          >
            <option value="">All scenarios</option>
            {options.scenarios.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        {showSearch ? (
          <label className="block space-y-2">
            <span className="micro-label">Search</span>
            <input
              className="field-control"
              onChange={(event) => onChange({ ...filters, search: event.target.value })}
              placeholder="host, path, extension, summary…"
              value={deferredSearch}
            />
          </label>
        ) : null}

        <label className="flex items-center gap-3 rounded-[18px] border border-line bg-canvas/55 px-4 py-3 text-sm text-ink">
          <input
            checked={filters.sensitiveOnly}
            className="h-4 w-4 rounded border-line bg-transparent accent-accent"
            onChange={(event) => onChange({ ...filters, sensitiveOnly: event.target.checked })}
            type="checkbox"
          />
          Sensitive artifacts only
        </label>
      </div>
    </div>
  );
}
