import type { KeyboardEvent } from "react";

import { Badge, GhostButton, V3, type V3Tone } from "../v3";
import type { EvidenceEventView } from "../../lib/types/view-models";

function kindTone(event: EvidenceEventView): V3Tone {
  if (event.sensitive) return "danger";
  if (event.kind === "network") return "warn";
  if (event.kind === "activation") return "accent";
  if (event.kind === "scenario") return "ok";
  return "neutral";
}

function attributionTone(status: string): V3Tone {
  if (status === "target_attributed") return "ok";
  if (status === "near_target_activation" || status === "competing_candidate") return "warn";
  if (status === "automation_noise") return "danger";
  if (status === "corroboration") return "accent";
  return "neutral";
}

function eventRisk(event: EvidenceEventView): { label: string; tone: V3Tone; color: string } {
  if (event.sensitive) return { label: "high", tone: "danger", color: V3.coral };
  if (event.kind === "network") return { label: "medium", tone: "warn", color: V3.warn };
  return { label: "low", tone: "ok", color: V3.ok };
}

function onKeyboardSelect(event: KeyboardEvent<HTMLElement>, callback: () => void) {
  if (event.key !== "Enter" && event.key !== " ") return;
  event.preventDefault();
  callback();
}

export function EvidenceLedger({
  events,
  selectedEventId,
  onSelect,
  expandSelected = true,
  maxHeight = 560,
}: {
  events: EvidenceEventView[];
  selectedEventId?: string;
  onSelect: (eventId: string) => void;
  expandSelected?: boolean;
  maxHeight?: number;
}) {
  if (!events.length) {
    return (
      <div
        style={{
          border: `1px dashed ${V3.rule2}`,
          background: V3.paper2,
          padding: "48px 20px",
          textAlign: "center",
          color: V3.ink3,
          fontSize: 13,
        }}
      >
        No events match this slice.
      </div>
    );
  }

  return (
    <div className="v3-scrollbar" style={{ border: `1px solid ${V3.rule}`, background: V3.card, minWidth: 0, overflowX: "auto" }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "56px minmax(120px, 160px) minmax(0, 1fr) 100px 90px 28px",
          gap: 12,
          padding: "10px 16px",
          borderBottom: `1px solid ${V3.rule}`,
          background: V3.paper2,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          color: V3.ink3,
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          minWidth: 800,
        }}
      >
        <span>#</span>
        <span>kind</span>
        <span>evidence</span>
        <span>risk</span>
        <span style={{ textAlign: "right" }}>time</span>
        <span />
      </div>

      <div className="v3-scrollbar" style={{ maxHeight, overflow: "auto" }}>
        {events.map((event, index) => {
          const selected = event.eventId === selectedEventId;
          const risk = eventRisk(event);
          const primary = event.summaryDisplay || event.artifactShort || event.summary;
          const secondaryCandidate = [event.artifactShort, event.detail, event.collectorLabel]
            .find((value) => Boolean(value) && value !== primary);
          return (
            <div key={event.eventId}>
              <div
                role="button"
                tabIndex={0}
                aria-selected={selected}
                onClick={() => onSelect(event.eventId)}
                onKeyDown={(keyboardEvent) => onKeyboardSelect(keyboardEvent, () => onSelect(event.eventId))}
                style={{
                  display: "grid",
                  gridTemplateColumns: "56px minmax(120px, 160px) minmax(0, 1fr) 100px 90px 28px",
                  gap: 12,
                  padding: "12px 16px",
                  alignItems: "center",
                  borderBottom: index < events.length - 1 || (selected && expandSelected) ? `1px solid ${V3.rule}` : "none",
                  borderLeft: selected ? `3px solid ${V3.coral}` : "3px solid transparent",
                  background: selected ? V3.paper2 : "transparent",
                  cursor: "pointer",
                  minWidth: 800,
                  transition: "background 140ms",
                }}
              >
                <span
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 10.5,
                    color: V3.ink4,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {String(index + 1).padStart(3, "0")}
                </span>
                <span
                  style={{
                    minWidth: 0,
                    maxWidth: "100%",
                    overflow: "hidden",
                    display: "inline-flex",
                  }}
                >
                  <Badge
                    tone={kindTone(event)}
                    style={{ minWidth: 0, maxWidth: "100%", overflow: "hidden" }}
                  >
                    <span
                      style={{
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        minWidth: 0,
                        maxWidth: "100%",
                        display: "inline-block",
                      }}
                    >
                      {event.kindLabel}
                    </span>
                  </Badge>
                </span>
                <div style={{ minWidth: 0 }}>
                  <div
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 12.5,
                      color: selected ? V3.ink : V3.ink2,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {primary}
                  </div>
                  {secondaryCandidate ? (
                    <div
                      style={{
                        marginTop: 5,
                        fontSize: 11,
                        color: V3.ink3,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {secondaryCandidate}
                    </div>
                  ) : null}
                </div>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 7 }}>
                  <span aria-hidden style={{ width: 9, height: 9, background: risk.color, display: "inline-block" }} />
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 11,
                      color: V3.ink3,
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                    }}
                  >
                    {risk.label}
                  </span>
                </span>
                <span
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 11,
                    color: V3.ink3,
                    textAlign: "right",
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {event.timestampDisplay}
                </span>
                <span
                  aria-hidden
                  style={{
                    color: V3.ink4,
                    textAlign: "center",
                    transform: selected ? "rotate(90deg)" : "rotate(0deg)",
                    transition: "transform 160ms",
                  }}
                >
                  ›
                </span>
              </div>

              {selected && expandSelected ? <ExpandedEvent event={event} risk={risk} /> : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ExpandedEvent({
  event,
  risk,
}: {
  event: EvidenceEventView;
  risk: { label: string; tone: V3Tone; color: string };
}) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 1.4fr) minmax(220px, 0.9fr) minmax(210px, 0.8fr)",
        gap: 18,
        padding: "16px 16px 20px 13px",
        borderLeft: `3px solid ${V3.coral}`,
        borderBottom: `1px solid ${V3.rule}`,
        background: V3.paper2,
        minWidth: 760,
      }}
    >
      <section style={{ minWidth: 0 }}>
        <div className="v3-eyebrow" style={{ marginBottom: 8 }}>Evidence</div>
        <div
          style={{
            border: `1px solid ${V3.rule}`,
            borderLeft: `2px solid ${risk.color}`,
            background: V3.paper,
            padding: "10px 12px",
            color: V3.ink,
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            lineHeight: 1.6,
            wordBreak: "break-word",
          }}
        >
          {event.summaryDisplay || event.summary}
        </div>
        <div className="v3-eyebrow" style={{ marginTop: 12, marginBottom: 6 }}>Attribution</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          <Badge tone={attributionTone(event.attributionStatus)}>{event.attributionStatusLabel}</Badge>
          {event.attributionConfidencePct ? <Badge tone={event.attributionConfidencePct >= 80 ? "ok" : "warn"}>{event.attributionConfidencePct}%</Badge> : null}
          <Badge tone="neutral">{event.actorLabel}</Badge>
        </div>
      </section>

      <section>
        <div className="v3-eyebrow" style={{ marginBottom: 8 }}>Metadata</div>
        <div style={{ border: `1px solid ${V3.rule}`, background: V3.paper, padding: "10px 12px" }}>
          <InlineKV k="id" v={event.eventId} />
          <InlineKV k="kind" v={event.kindLabel} />
          <InlineKV k="risk" v={risk.label} dot={risk.color} />
          <InlineKV k="scenario" v={event.scenarioLabel} />
          <InlineKV k="target" v={event.extensionId || "(unattributed)"} />
        </div>
      </section>

      <section>
        <div className="v3-eyebrow" style={{ marginBottom: 8 }}>Actions</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <GhostButton ariaLabel="Copy event JSON">Copy event JSON</GhostButton>
          <GhostButton ariaLabel="Add to watchlist">Add to watchlist</GhostButton>
          <GhostButton ariaLabel="Filter by this kind">Filter by this kind</GhostButton>
        </div>
        <div style={{ marginTop: 12 }}>
          <div className="v3-eyebrow" style={{ marginBottom: 6 }}>Signature</div>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: V3.ink3,
              border: `1px dashed ${V3.rule2}`,
              background: V3.paper,
              padding: "8px 10px",
              wordBreak: "break-all",
            }}
          >
            sha256:{event.eventId.slice(-12)}…
          </div>
        </div>
      </section>
    </div>
  );
}

function InlineKV({ k, v, dot }: { k: string; v: string; dot?: string }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "86px minmax(0, 1fr)",
        gap: 10,
        padding: "5px 0",
        alignItems: "baseline",
      }}
    >
      <span
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          color: V3.ink3,
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}
      >
        {k}
      </span>
      <span
        style={{
          display: "inline-flex",
          minWidth: 0,
          alignItems: "center",
          gap: 6,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 11.5,
          color: V3.ink,
          wordBreak: "break-word",
        }}
      >
        {dot ? <span aria-hidden style={{ width: 7, height: 7, background: dot }} /> : null}
        {v || "(n/a)"}
      </span>
    </div>
  );
}
