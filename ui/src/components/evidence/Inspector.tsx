import type { DetectionReportView, EvidenceInspectorView, RuleDraftView } from "../../lib/types/view-models";
import { Panel as V3Panel, Tabs, V3, type TabSpec } from "../v3";
import {
  ProvenanceTab,
  RelationsTab,
  RuleHitsTab,
  RulesTab,
  SelectedEventHero,
} from "./InspectorSections";

type InspectorTab = "provenance" | "relations" | "rules" | "rule-hits";

const INSPECTOR_TABS: TabSpec<InspectorTab>[] = [
  { value: "provenance", label: "Provenance" },
  { value: "relations", label: "Relations" },
  { value: "rules", label: "Rule Draft" },
  { value: "rule-hits", label: "Rules" },
];

export function Inspector({
  activeTab,
  onTabChange,
  inspector,
  ruleDraft,
  detection,
}: {
  activeTab: InspectorTab;
  onTabChange: (next: InspectorTab) => void;
  inspector: EvidenceInspectorView | null;
  ruleDraft: RuleDraftView | null;
  detection?: DetectionReportView | null;
}) {
  return (
    <V3Panel label="Inspector" bodyStyle={{ padding: 0 }}>
      <div style={{ padding: "12px 16px", borderBottom: `1px solid ${V3.rule}` }}>
        <Tabs<InspectorTab>
          ariaLabel="Inspector tabs"
          tabs={INSPECTOR_TABS}
          value={activeTab}
          onChange={onTabChange}
        />
      </div>
      <div style={{ padding: "16px", display: "flex", flexDirection: "column", gap: 18 }}>
        {inspector ? (
          <>
            <SelectedEventHero inspector={inspector} />
            {activeTab === "provenance" ? <ProvenanceTab inspector={inspector} /> : null}
            {activeTab === "relations" ? <RelationsTab inspector={inspector} /> : null}
            {activeTab === "rules" ? <RulesTab ruleDraft={ruleDraft} /> : null}
            {activeTab === "rule-hits" ? <RuleHitsTab detection={detection || null} inspector={inspector} /> : null}
          </>
        ) : (
          <div style={{ fontSize: 13, color: V3.ink3, lineHeight: 1.6 }}>
            Select an event from the timeline or table to inspect provenance, relations, and rules.
          </div>
        )}
      </div>
    </V3Panel>
  );
}
