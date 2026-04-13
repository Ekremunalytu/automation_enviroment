import type { EvidenceInspectorView, RuleDraftView } from "../../lib/types/view-models";
import { toRuleJson, toRuleYaml } from "../../lib/rules/draft";
import { Badge } from "../ui/Badge";
import { Panel, PanelHeader } from "../ui/Panel";
import { SegmentedTabs } from "../ui/SegmentedTabs";

export function Inspector({
  activeTab,
  onTabChange,
  inspector,
  ruleDraft,
}: {
  activeTab: "provenance" | "rule";
  onTabChange: (next: "provenance" | "rule") => void;
  inspector: EvidenceInspectorView | null;
  ruleDraft: RuleDraftView | null;
}) {
  return (
    <div className="xl:sticky xl:top-24">
      {activeTab === "provenance" ? (
        <Panel className="overflow-hidden p-0">
          <div className="border-b border-line px-5 py-5">
            <PanelHeader
              description="Focused event context, attribution metadata, and explicit evidence links."
              right={
                <SegmentedTabs
                  onChange={(next) => onTabChange(next as "provenance" | "rule")}
                  options={[
                    { value: "provenance", label: "Provenance" },
                    { value: "rule", label: "Rule Draft" },
                  ]}
                  value={activeTab}
                />
              }
              title="Provenance"
            />
          </div>

          {inspector ? (
            <div className="space-y-5 px-5 py-5">
              <section className="panel-alt p-4">
                <div className="micro-label">Event Summary</div>
                <div className="mt-3 text-2xl font-semibold tracking-tight text-ink">{inspector.event.artifactShort}</div>
                <p className="mt-3 text-sm leading-6 text-mute">{inspector.event.summaryDisplay}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Badge tone="accent">{inspector.event.kindLabel}</Badge>
                  <Badge tone="cyan">{inspector.event.collectorLabel}</Badge>
                  <Badge tone="lime">{inspector.event.actorLabel}</Badge>
                  {inspector.event.sensitive ? <Badge tone="rose">Sensitive</Badge> : null}
                </div>
              </section>

              <section>
                <div className="micro-label">Attribution Metadata</div>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <Meta label="Timestamp" value={inspector.event.timestampDisplay} />
                  <Meta label="Scenario" value={inspector.event.scenarioLabel} />
                  <Meta label="Extension" value={inspector.event.extensionId || "(unattributed)"} />
                  <Meta label="Host / Path" value={inspector.event.host || inspector.event.path || "(n/a)"} />
                  <Meta
                    label="Destination"
                    value={
                      inspector.event.destinationIp
                        ? `${inspector.event.destinationIp}${inspector.event.destinationPort ? `:${inspector.event.destinationPort}` : ""}`
                        : "(n/a)"
                    }
                  />
                  <Meta label="Operation" value={inspector.event.detail || "(n/a)"} />
                </div>
              </section>

              <section>
                <div className="micro-label">Reason Chain</div>
                <div className="mt-3 space-y-3">
                  {inspector.related.length ? (
                    inspector.related.slice(0, 8).map((link) => (
                      <div key={`${link.direction}-${link.linkType}-${link.peerEvent?.eventId || "none"}`} className="panel-alt p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="space-y-1">
                            <div className="text-sm font-medium text-ink">
                              {link.linkLabel} → {link.peerEvent?.kindLabel || "Unknown"}
                            </div>
                            <div className="text-xs leading-5 text-mute">{link.peerEvent?.summaryDisplay || "No peer summary"}</div>
                          </div>
                          <Badge tone={link.confidence >= 0.8 ? "success" : link.confidence >= 0.5 ? "warning" : "danger"}>
                            {link.confidencePct}%
                          </Badge>
                        </div>
                        <p className="mt-3 text-sm leading-6 text-mute">{link.reason}</p>
                      </div>
                    ))
                  ) : (
                    <div className="rounded-[22px] border border-dashed border-lineStrong px-4 py-5 text-sm text-mute">
                      No explicit evidence links available for this event.
                    </div>
                  )}
                </div>
              </section>
            </div>
          ) : (
            <div className="px-5 py-6 text-sm text-mute">Select an event from the table or timeline to populate the inspector.</div>
          )}
        </Panel>
      ) : (
        <Panel className="overflow-hidden p-0">
          <div className="border-b border-line px-5 py-5">
            <PanelHeader
              description="Portable rule output derived from the current evidence selection."
              right={
                <SegmentedTabs
                  onChange={(next) => onTabChange(next as "provenance" | "rule")}
                  options={[
                    { value: "provenance", label: "Provenance" },
                    { value: "rule", label: "Rule Draft" },
                  ]}
                  value={activeTab}
                />
              }
              title="Rule Draft"
            />
          </div>

          {ruleDraft ? (
            <div className="space-y-5 px-5 py-5">
              <div className="grid gap-3 sm:grid-cols-2">
                <Meta label="Title" value={ruleDraft.title} />
                <Meta label="Severity" value={ruleDraft.severity.toUpperCase()} />
                <Meta label="Confidence" value={`${Math.round(ruleDraft.confidence * 100)}%`} />
                <Meta label="Conditions" value={String(ruleDraft.conditions.length)} />
              </div>

              <section className="panel-alt p-4">
                <div className="micro-label">Rule Export</div>
                <p className="mt-3 text-sm leading-6 text-mute">{ruleDraft.rationale}</p>
              </section>

              <section>
                <div className="micro-label">Labels</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {ruleDraft.labels.map((label) => (
                    <Badge key={label} tone="accent">
                      {label}
                    </Badge>
                  ))}
                </div>
              </section>

              <section>
                <div className="micro-label">Conditions</div>
                <div className="mt-3 space-y-2">
                  {ruleDraft.conditions.map((condition) => (
                    <div key={`${condition.field}-${condition.operator}-${String(condition.value)}`} className="panel-alt px-3 py-3 text-sm text-ink">
                      <span className="font-mono text-accentSoft">{condition.field}</span>
                      <span className="mx-2 text-mute">{condition.operator}</span>
                      <span className="font-mono text-ink">{JSON.stringify(condition.value)}</span>
                    </div>
                  ))}
                </div>
              </section>

              <DualCodeBlock json={toRuleJson(ruleDraft)} yaml={toRuleYaml(ruleDraft)} />
            </div>
          ) : (
            <div className="px-5 py-6 text-sm text-mute">Select an event to generate a rule draft.</div>
          )}
        </Panel>
      )}
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-tile">
      <div className="micro-label">{label}</div>
      <div className="mt-3 break-words text-sm leading-6 text-ink">{value}</div>
    </div>
  );
}

function DualCodeBlock({ json, yaml }: { json: string; yaml: string }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-[22px] border border-line bg-canvas/70 p-4">
        <div className="micro-label">JSON</div>
        <pre className="mt-3 max-h-[320px] overflow-auto whitespace-pre-wrap break-all font-mono text-xs leading-6 text-accentSoft scroll-thin">
          {json}
        </pre>
      </div>
      <div className="rounded-[22px] border border-line bg-canvas/70 p-4">
        <div className="micro-label">YAML</div>
        <pre className="mt-3 max-h-[320px] overflow-auto whitespace-pre-wrap break-all font-mono text-xs leading-6 text-ink scroll-thin">
          {yaml}
        </pre>
      </div>
    </div>
  );
}
