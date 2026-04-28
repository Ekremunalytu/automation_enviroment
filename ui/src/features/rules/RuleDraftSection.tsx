import { useNavigate } from "react-router-dom";

import {
  EmptyState,
  GhostButton,
  KVRow,
  Panel,
  V3,
} from "../../components/v3";
import { getInspectorView } from "../../lib/adapters/report";
import { buildRuleDraft, toRuleJson, toRuleYaml } from "../../lib/rules/draft";
import type { ActivationReportView } from "../../lib/types/view-models";

export function RuleDraftSection({
  fromEventId,
  report,
}: {
  fromEventId: string | null;
  report: ActivationReportView | null;
}) {
  const navigate = useNavigate();

  if (!fromEventId) {
    return (
      <EmptyState
        eyebrow="Draft"
        title="No event selected"
        body="Open an event in Reports and choose 'Draft rule from event' to start a draft."
      />
    );
  }

  const inspector = report ? getInspectorView(report, fromEventId) : null;
  if (!inspector) {
    return (
      <EmptyState
        eyebrow="Draft"
        title="Event not found"
        body="The selected event isn't part of the latest report bundle anymore."
      />
    );
  }

  const rule = buildRuleDraft(inspector);
  if (!rule) {
    return (
      <EmptyState
        eyebrow="Draft"
        title="Draft unavailable"
        body="Could not derive a rule draft from this event."
      />
    );
  }

  const copy = (text: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text).catch(() => {
        // Clipboard write rejected (permissions, focus). The button click
        // still informs intent — silent failure is acceptable in this UI.
      });
    }
  };

  const yaml = toRuleYaml(rule);
  const json = toRuleJson(rule);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <Panel label="Draft summary">
        <KVRow k="title" v={rule.title} />
        <KVRow k="severity" v={rule.severity} />
        <KVRow k="confidence" v={rule.confidence.toFixed(2)} />
        {rule.suspiciousReasons.length ? (
          <KVRow k="reasons" v={rule.suspiciousReasons.join(" · ")} mono={false} />
        ) : null}
      </Panel>

      <Panel label="YAML preview" padded={false}>
        <pre
          style={{
            margin: 0,
            padding: 16,
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: V3.ink2,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {yaml}
        </pre>
      </Panel>

      <Panel label="JSON preview" padded={false}>
        <pre
          style={{
            margin: 0,
            padding: 16,
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: V3.ink2,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {json}
        </pre>
      </Panel>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <GhostButton ariaLabel="Copy YAML" onClick={() => copy(yaml)}>
          Copy YAML
        </GhostButton>
        <GhostButton ariaLabel="Copy JSON" onClick={() => copy(json)}>
          Copy JSON
        </GhostButton>
        <GhostButton
          ariaLabel="Save to file (backend pending)"
          disabled
          data-feature-stub="rule-save"
          title="Backend pending. Use Copy YAML and paste under rules/draft/."
        >
          Save to file
        </GhostButton>
        <GhostButton
          ariaLabel="Open event in Reports"
          onClick={() =>
            navigate(`/reports?tab=ledger&event=${encodeURIComponent(fromEventId)}`)
          }
        >
          Open event in Reports
        </GhostButton>
      </div>
    </div>
  );
}
