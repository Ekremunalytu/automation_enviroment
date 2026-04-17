import type { ReactNode } from "react";
import type { EvidenceInspectorView, RuleDraftView } from "../../lib/types/view-models";
import { Panel, PanelHeader } from "../ui/Panel";
import { SegmentedTabs } from "../ui/SegmentedTabs";
import {
  ProvenanceTab,
  RelationsTab,
  RulesTab,
  SelectedEventHero,
} from "./InspectorSections";

type InspectorTab = "provenance" | "relations" | "rules";

export function Inspector({
  activeTab,
  onTabChange,
  inspector,
  ruleDraft,
}: {
  activeTab: InspectorTab;
  onTabChange: (next: InspectorTab) => void;
  inspector: EvidenceInspectorView | null;
  ruleDraft: RuleDraftView | null;
}) {
  const tabs = (
    <SegmentedTabs
      onChange={(next) => onTabChange(next as InspectorTab)}
      options={[
        { value: "provenance", label: "Provenance" },
        { value: "relations", label: "Relations" },
        { value: "rules", label: "Rules" },
      ]}
      value={activeTab}
    />
  );

  return (
    <InspectorShell tabs={tabs}>
      {inspector ? (
        <>
          <SelectedEventHero inspector={inspector} />
          {activeTab === "relations" ? <RelationsTab inspector={inspector} /> : null}
          {activeTab === "rules" ? <RulesTab ruleDraft={ruleDraft} /> : null}
          {activeTab === "provenance" ? <ProvenanceTab inspector={inspector} /> : null}
        </>
      ) : (
        <div className="text-sm leading-6 text-mute">
          Select an event from the timeline or table to inspect provenance, relation graph, and rules in this workspace.
        </div>
      )}
    </InspectorShell>
  );
}

function InspectorShell({
  tabs,
  children,
}: {
  tabs: ReactNode;
  children: ReactNode;
}) {
  return (
    <Panel className="overflow-hidden p-0">
      <div className="border-b border-line px-5 py-5">
        <PanelHeader
          description="Review event provenance, evidence relations, and portable rules from a dedicated analysis surface."
          right={tabs}
          title="Analysis workspace"
        />
      </div>
      <div className="space-y-6 px-5 py-5">{children}</div>
    </Panel>
  );
}
