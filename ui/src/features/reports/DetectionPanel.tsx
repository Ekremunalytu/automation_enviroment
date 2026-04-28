import { Badge, EmptyState, V3, type V3Tone } from "../../components/v3";
import type { DetectionReportView } from "../../lib/types/view-models";
import { FindingCard } from "./FindingCard";

function emptyStateCopy(verdict: DetectionReportView["verdict"]) {
  if (verdict === "clean") return "No rules fired. Verdict: clean.";
  if (verdict === "clean_with_notes") return "Only informational findings were recorded.";
  if (verdict === "inconclusive") return "No rules fired, but analysis remained inconclusive.";
  return "No findings were attached to this verdict.";
}

export function DetectionPanel({
  detection,
}: {
  detection: DetectionReportView | null;
}) {
  if (!detection) {
    return (
      <EmptyState
        eyebrow="Detection"
        body="This report did not include a detection bundle."
        title="Detection data unavailable"
      />
    );
  }

  const tone = verdictTone(detection.verdict);
  const isClean = detection.verdict === "clean" || detection.verdict === "clean_with_notes";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <section
        aria-live="polite"
        style={{
          border: `1px solid ${tone.border}`,
          background: isClean ? V3.paper2 : tone.bg,
          padding: "18px 20px",
        }}
      >
        <div className="v3-eyebrow">Detection</div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 1fr) auto",
            gap: 18,
            alignItems: "end",
            marginTop: 10,
          }}
        >
          <div style={{ minWidth: 0 }}>
            <h2
              style={{
                margin: 0,
                fontSize: isClean ? 24 : 30,
                fontWeight: 700,
                letterSpacing: 0,
                color: tone.fg,
                lineHeight: 1.05,
              }}
            >
              {detection.verdictLabel}
            </h2>
            <p style={{ marginTop: 8, maxWidth: 760, fontSize: 13.5, lineHeight: 1.6, color: V3.ink3 }}>
              {detection.verdictRationale}
            </p>
          </div>
          <Badge tone={tone.badgeTone}>
            {detection.findings.length} finding{detection.findings.length === 1 ? "" : "s"}
          </Badge>
        </div>
      </section>

      {!detection.findings.length ? (
        <EmptyState
          eyebrow="Findings"
          body={emptyStateCopy(detection.verdict)}
          title="No fired rules"
        />
      ) : (
        <section style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {detection.findings.map((finding) => (
            <FindingCard finding={finding} key={finding.id} />
          ))}
        </section>
      )}
    </div>
  );
}

function verdictTone(verdict: DetectionReportView["verdict"]): {
  border: string;
  bg: string;
  fg: string;
  badgeTone: V3Tone;
} {
  if (verdict === "malicious") {
    return { border: V3.coral, bg: V3.dangerBg, fg: V3.coral, badgeTone: "danger" };
  }
  if (verdict === "suspicious") {
    return { border: "#5c4a22", bg: V3.warnBg, fg: V3.warn, badgeTone: "warn" };
  }
  if (verdict === "inconclusive") {
    return { border: V3.rule2, bg: V3.paper3, fg: V3.ink2, badgeTone: "neutral" };
  }
  if (verdict === "clean_with_notes") {
    return { border: "#2a4a36", bg: V3.okBg, fg: V3.ok, badgeTone: "ok" };
  }
  return { border: "#2a4a36", bg: V3.okBg, fg: V3.ok, badgeTone: "ok" };
}
