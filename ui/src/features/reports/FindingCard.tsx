import { useNavigate } from "react-router-dom";

import { Badge, RISK_COLOR, V3, type Risk, type V3Tone } from "../../components/v3";
import type { DetectionFindingView } from "../../lib/types/view-models";

function severityTone(severity: DetectionFindingView["severity"]): V3Tone {
  if (severity === "critical" || severity === "high") return "danger";
  if (severity === "medium") return "warn";
  if (severity === "low") return "ok";
  return "neutral";
}

function severityRisk(severity: DetectionFindingView["severity"]): Risk {
  if (severity === "critical" || severity === "high") return "high";
  if (severity === "medium") return "medium";
  return "low";
}

export function FindingCard({ finding }: { finding: DetectionFindingView }) {
  const navigate = useNavigate();
  const mappedRisk = severityRisk(finding.severity);

  return (
    <button
      type="button"
      onClick={() => navigate(`/rules?rule=${encodeURIComponent(finding.ruleId)}&from=reports`)}
      style={{
        display: "grid",
        gridTemplateColumns: "10px minmax(0, 1fr) auto auto auto",
        gap: 12,
        alignItems: "center",
        width: "100%",
        border: `1px solid ${V3.rule}`,
        borderLeft: `3px solid ${RISK_COLOR[mappedRisk]}`,
        background: V3.paper2,
        padding: "14px 16px",
        textAlign: "left",
        cursor: "pointer",
        color: "inherit",
      }}
    >
      <span aria-hidden style={{ width: 8, height: 8, background: RISK_COLOR[mappedRisk] }} />
      <div style={{ minWidth: 0 }}>
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: V3.ink,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {finding.title}
        </div>
        <div
          style={{
            marginTop: 4,
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11,
            color: V3.ink3,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {finding.ruleId}
        </div>
      </div>
      <Badge tone={severityTone(finding.severity)}>{finding.severityLabel}</Badge>
      <span
        style={{
          border: `1px solid ${V3.rule2}`,
          background: V3.paper,
          color: V3.ink3,
          padding: "3px 8px",
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          fontWeight: 600,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          whiteSpace: "nowrap",
        }}
      >
        {finding.evidence.length} hits
      </span>
      <span aria-hidden style={{ color: V3.ink4 }}>›</span>
    </button>
  );
}
