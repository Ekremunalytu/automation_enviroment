import { Badge, GhostButton, V3, type V3Tone } from "../../components/v3";
import type { DetectionFindingView } from "../../lib/types/view-models";

function severityTone(severity: DetectionFindingView["severity"]): V3Tone {
  if (severity === "critical" || severity === "high") return "danger";
  if (severity === "medium") return "warn";
  if (severity === "low") return "ok";
  return "neutral";
}

export function FindingCard({
  finding,
  onShowEvidence,
}: {
  finding: DetectionFindingView;
  onShowEvidence: (eventId: string) => void;
}) {
  const firstEvidenceId = finding.evidence[0]?.eventId;

  return (
    <article
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 14,
        border: `1px solid ${V3.rule}`,
        background: V3.paper2,
        padding: "18px 20px",
      }}
    >
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
        <div style={{ minWidth: 0, display: "flex", flexDirection: "column", gap: 6 }}>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              color: V3.ink3,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              wordBreak: "break-all",
            }}
          >
            {finding.ruleId}
          </span>
          <h3
            style={{
              margin: 0,
              fontFamily: "'Manrope', sans-serif",
              fontSize: 18,
              fontWeight: 700,
              color: V3.ink,
              lineHeight: 1.2,
            }}
          >
            {finding.title}
          </h3>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          <Badge tone={severityTone(finding.severity)}>Severity · {finding.severityLabel}</Badge>
          <Badge tone="neutral">Confidence · {finding.confidenceLabel}</Badge>
          <Badge tone="neutral">{finding.adversaryClass}</Badge>
        </div>
      </div>

      <p style={{ margin: 0, fontSize: 13, color: V3.ink3, lineHeight: 1.6 }}>{finding.description}</p>

      {finding.categories.length ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {finding.categories.map((category) => (
            <span
              key={category}
              style={{
                border: `1px solid ${V3.rule}`,
                padding: "3px 8px",
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 10,
                color: V3.ink3,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
              }}
            >
              {category}
            </span>
          ))}
        </div>
      ) : null}

      {finding.mitigationHint ? (
        <div
          style={{
            border: `1px solid ${V3.rule2}`,
            background: V3.paper3,
            padding: "10px 12px",
            fontSize: 13,
            lineHeight: 1.6,
            color: V3.ink3,
          }}
        >
          {finding.mitigationHint}
        </div>
      ) : null}

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div style={{ fontSize: 12.5, color: V3.ink3, lineHeight: 1.5, minWidth: 0 }}>
          {finding.evidence.length
            ? finding.evidence.map((item) => item.summary).join(" · ")
            : "No evidence references recorded."}
        </div>
        <GhostButton
          ariaLabel={`Show evidence for ${finding.title}`}
          disabled={!firstEvidenceId}
          onClick={() => firstEvidenceId && onShowEvidence(firstEvidenceId)}
        >
          {finding.evidence.length} evidence
        </GhostButton>
      </div>
    </article>
  );
}
