import type { DetectionReportView, EvidenceInspectorView } from "../../lib/types/view-models";
import { KVRow, Panel as V3Panel, RISK_COLOR, Tabs, V3, type Risk, type TabSpec } from "../v3";
import { ProvenanceTab, RelationsTab } from "./InspectorSections";

export type InspectorTab = "provenance" | "relations";

const INSPECTOR_TABS: TabSpec<InspectorTab>[] = [
  { value: "provenance", label: "Provenance" },
  { value: "relations", label: "Relations" },
];

function eventRisk(inspector: EvidenceInspectorView): Risk {
  if (inspector.event.sensitive) return "high";
  if (inspector.event.kind === "network") return "medium";
  return "low";
}

export function Inspector({
  activeTab,
  onTabChange,
  inspector,
  detection,
}: {
  activeTab: InspectorTab;
  onTabChange: (next: InspectorTab) => void;
  inspector: EvidenceInspectorView | null;
  detection?: DetectionReportView | null;
}) {
  const selectedRisk = inspector ? eventRisk(inspector) : "low";

  return (
    <V3Panel label="Inspector" bodyStyle={{ padding: 0 }}>
      {inspector ? (
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,300px)_minmax(0,1fr)]">
          <div
            className="border-b border-line lg:border-b-0 lg:border-r"
            style={{ padding: "14px 16px" }}
          >
            <div className="v3-eyebrow" style={{ marginBottom: 8 }}>Evidence</div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12.5,
                color: V3.ink,
                lineHeight: 1.55,
                padding: "10px 12px",
                background: V3.paper,
                border: `1px solid ${V3.rule}`,
                borderLeft: `2px solid ${RISK_COLOR[selectedRisk]}`,
                wordBreak: "break-all",
              }}
            >
              {inspector.event.summaryDisplay || inspector.event.summary}
            </div>
            <div style={{ marginTop: 12 }}>
              <KVRow k="id" v={inspector.event.eventId} />
              <KVRow k="kind" v={inspector.event.kindLabel} />
              <KVRow k="risk" v={selectedRisk} dot={RISK_COLOR[selectedRisk]} />
              <KVRow k="timestamp" v={inspector.event.timestampDisplay} />
              <KVRow k="offset" v={inspector.event.relTimeS != null ? `+${inspector.event.relTimeS}s` : "(n/a)"} />
            </div>
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ padding: "12px 16px", borderBottom: `1px solid ${V3.rule}` }}>
              <Tabs<InspectorTab>
                ariaLabel="Inspector tabs"
                tabs={INSPECTOR_TABS}
                value={activeTab}
                onChange={onTabChange}
              />
            </div>
            <div style={{ padding: "16px" }}>
              {activeTab === "provenance" ? <ProvenanceTab inspector={inspector} detection={detection ?? null} /> : null}
              {activeTab === "relations" ? <RelationsTab inspector={inspector} /> : null}
            </div>
          </div>
        </div>
      ) : (
        <div style={{ padding: 16, fontSize: 13, color: V3.ink3, lineHeight: 1.6 }}>
          Select an event from the timeline or table to inspect provenance and relations.
        </div>
      )}
    </V3Panel>
  );
}
