import { V3 } from "../../../components/v3";
import { DISPLAY_CAPS, applyDisplayCap } from "../../../lib/displayCaps";

export type DensityEvent = {
  id: string;
  label?: string;
  relTimeS?: number | null;
  kind?: string;
  risk?: "low" | "medium" | "high";
};

type EventDensityStripProps = {
  events: ReadonlyArray<DensityEvent>;
  selectedId?: string;
  onSelect: (eventId: string) => void;
};

export function EventDensityStrip({ events, selectedId, onSelect }: EventDensityStripProps) {
  const capped = applyDisplayCap(events, DISPLAY_CAPS.EVENT_DENSITY_EVENTS);
  const visible = capped.visible;
  const maxT = visible.reduce((acc, event) => Math.max(acc, event.relTimeS ?? 0), 0) + 1;
  const bucketCount = Math.max(1, Math.ceil(maxT) + 1);
  const buckets: DensityEvent[][] = Array.from({ length: bucketCount }, () => []);
  visible.forEach((event) => {
    if (typeof event.relTimeS === "number") {
      const idx = Math.min(Math.floor(event.relTimeS), bucketCount - 1);
      if (idx >= 0) buckets[idx].push(event);
    }
  });
  const maxCount = Math.max(1, ...buckets.map((bucket) => bucket.length));
  return (
    <div style={{ padding: "14px 16px" }}>
      <div
        data-testid="density-bucket-row"
        style={{ display: "flex", alignItems: "flex-end", gap: 2, height: 84 }}
      >
        {buckets.map((bucket, index) => {
          const hasSelected = bucket.some((event) => event.id === selectedId);
          const topRisk = bucket.reduce<{ rank: number; color: string }>(
            (acc, event) => {
              const risk = event.risk ?? "low";
              const rank = risk === "high" ? 3 : risk === "medium" ? 2 : 1;
              if (rank <= acc.rank) return acc;
              return {
                rank,
                color: risk === "high" ? V3.coral : risk === "medium" ? V3.warn : V3.ok,
              };
            },
            { rank: 0, color: V3.rule2 },
          );
          const heightPx = bucket.length === 0 ? 2 : (bucket.length / maxCount) * 64 + 6;
          const target = bucket[0];
          return (
            <button
              key={index}
              type="button"
              disabled={!target}
              onClick={() => target && onSelect(target.id)}
              aria-label={`Bucket ${index}s · ${bucket.length} events`}
              title={`${index}s · ${bucket.length} events`}
              data-testid="density-bucket"
              style={{
                flex: 1,
                height: heightPx,
                background: bucket.length ? topRisk.color : V3.rule,
                opacity: bucket.length ? (hasSelected ? 1 : 0.85) : 0.4,
                borderTop: hasSelected ? `2px solid ${V3.ink}` : "none",
                border: 0,
                padding: 0,
                cursor: bucket.length ? "pointer" : "default",
                transition: "all 180ms",
              }}
            />
          );
        })}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            color: V3.ink4,
            letterSpacing: "0.08em",
          }}
        >
          0s
        </span>
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            color: V3.ink4,
            letterSpacing: "0.08em",
          }}
        >
          {Math.ceil(maxT)}s
        </span>
      </div>
      {capped.truncated ? (
        <div
          data-testid="density-truncation-indicator"
          style={{
            marginTop: 6,
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            color: V3.ink3,
            letterSpacing: "0.06em",
            textTransform: "lowercase",
          }}
        >
          +{capped.overflowCount.toLocaleString()} events truncated · density reflects first {visible.length.toLocaleString()} of {capped.totalCount.toLocaleString()}
        </div>
      ) : null}
    </div>
  );
}
