import { EvidenceLedger } from "../../components/evidence/EvidenceLedger";
import { Inspector } from "../../components/evidence/Inspector";
import { EmptyState, Eyebrow, Panel as V3Panel, SectionTitle, V3 } from "../../components/v3";
import type {
  ActivationReportView,
  EvidenceInspectorView,
  SimulationViewModel,
} from "../../lib/types/view-models";
import type { InspectorTab } from "../evidence";

export function LiveEvidenceWorkspace({
  filteredEvents,
  eventId,
  inspector,
  inspectorTab,
  model,
  staticOnly,
  detection,
  onInspectorTabChange,
  onSelectEvent,
}: {
  filteredEvents: ActivationReportView["evidence"];
  eventId?: string;
  inspector: EvidenceInspectorView | null;
  inspectorTab: InspectorTab;
  detection: ActivationReportView["detection"];
  model: SimulationViewModel | null;
  staticOnly: boolean;
  onInspectorTabChange: (next: InspectorTab) => void;
  onSelectEvent: (eventId: string) => void;
}) {
  if (!filteredEvents.length) {
    return (
      <EmptyState
        eyebrow={staticOnly ? "Static only" : "Warmup"}
        title={staticOnly ? "Dynamic sandbox skipped" : "Run is warming up"}
        body={model?.warmupCopy || "Waiting for the sandbox run to emit telemetry."}
      />
    );
  }

  return (
    <section style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div>
        <Eyebrow>Live</Eyebrow>
        <SectionTitle style={{ marginTop: 10, fontSize: 22 }}>Live event ledger</SectionTitle>
        <p style={{ marginTop: 10, maxWidth: 720, color: V3.ink3, fontSize: 13.5, lineHeight: 1.6 }}>
          Inspect the raw stream and selected-event provenance in the same surface.
        </p>
      </div>
      <V3Panel label="Event stream" bodyStyle={{ padding: 0 }}>
        <EvidenceLedger
          events={filteredEvents}
          onSelect={onSelectEvent}
          selectedEventId={eventId}
          expandSelected={false}
        />
      </V3Panel>
      <Inspector
        activeTab={inspectorTab}
        detection={detection}
        inspector={inspector}
        onTabChange={onInspectorTabChange}
      />
    </section>
  );
}
