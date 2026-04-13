import type { EvidenceEventView } from "../../lib/types/view-models";
import { Badge } from "../ui/Badge";

function attributionTone(status: string) {
  if (status === "target_attributed") return "success";
  if (status === "near_target_activation" || status === "competing_candidate") return "warning";
  if (status === "automation_noise") return "danger";
  if (status === "corroboration") return "accent";
  return "default";
}

export function EvidenceTable({
  events,
  selectedEventId,
  onSelect,
}: {
  events: EvidenceEventView[];
  selectedEventId?: string;
  onSelect: (eventId: string) => void;
}) {
  return (
    <div className="overflow-hidden rounded-[24px] border border-line bg-canvas/50">
      <div className="max-h-[520px] overflow-auto scroll-thin">
        <table className="min-w-full divide-y divide-line text-left text-sm">
          <thead className="sticky top-0 z-10 bg-panel/95 backdrop-blur">
            <tr className="text-xs uppercase tracking-data text-mute">
              <th className="px-4 py-3 font-medium">Time</th>
              <th className="px-4 py-3 font-medium">Kind</th>
              <th className="px-4 py-3 font-medium">Artifact</th>
              <th className="px-4 py-3 font-medium">Context</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {events.map((event) => {
              const selected = event.eventId === selectedEventId;
              return (
                <tr
                  aria-selected={selected}
                  key={event.eventId}
                  className={`cursor-pointer align-top transition hover:bg-surface/45 focus-within:bg-surface/45 ${
                    selected ? "bg-accent/12" : ""
                  }`}
                  onClick={() => onSelect(event.eventId)}
                  onKeyDown={(keyboardEvent) => {
                    if (keyboardEvent.key === "Enter" || keyboardEvent.key === " ") {
                      keyboardEvent.preventDefault();
                      onSelect(event.eventId);
                    }
                  }}
                  tabIndex={0}
                >
                  <td className={`px-4 py-3 font-mono text-xs tabular-nums ${selected ? "text-accentSoft" : "text-mute"}`}>
                    {event.timestampDisplay}
                  </td>
                  <td className="px-4 py-3">
                    <Badge tone={event.sensitive ? "rose" : event.kind === "network" ? "lime" : event.kind === "activation" ? "accent" : event.kind === "scenario" ? "amber" : "cyan"}>
                      {event.kindLabel}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-ink">{event.artifactShort}</div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <Badge tone={attributionTone(event.attributionStatus)}>{event.attributionStatusLabel}</Badge>
                      {event.attributionConfidencePct ? (
                        <Badge tone={event.attributionConfidencePct >= 80 ? "success" : event.attributionConfidencePct >= 50 ? "warning" : "default"}>
                          {event.attributionConfidencePct}%
                        </Badge>
                      ) : null}
                      {event.artifactClass ? <Badge tone="amber">{event.artifactClass.replaceAll("_", " ")}</Badge> : null}
                    </div>
                    <div className="mt-2 text-xs text-mute">{event.detail}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm leading-6 text-ink">{event.summaryDisplay}</div>
                    <div className="mt-2 text-xs text-mute">
                      {event.collectorLabel} / {event.actorLabel}
                      {event.scenarioName ? ` · ${event.scenarioName}` : ""}
                    </div>
                    {event.attributionStatus !== "target_attributed" && (event.kind === "file" || event.kind === "network") ? (
                      <div className="mt-2 text-xs text-warning">
                        {event.attributionStatus === "near_target_activation" || event.attributionStatus === "competing_candidate"
                          ? "Correlated only: ownership is not confirmed."
                          : event.noiseReason || "Ownership is not confirmed for this event."}
                      </div>
                    ) : null}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
