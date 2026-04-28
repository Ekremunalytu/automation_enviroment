import type { AnalyzeJobStatusDto } from "../../lib/types/contracts";
import type { SimulationViewModel } from "../../lib/types/view-models";
import { Badge, ProgressBar, V3, type V3Tone } from "../v3";

function statusTone(status: string): V3Tone {
  if (status === "completed") return "ok";
  if (status === "failed" || status === "cancelled") return "danger";
  if (status === "running") return "accent";
  return "neutral";
}

export function RunActivityRail({
  job,
  model,
}: {
  job: AnalyzeJobStatusDto;
  model: SimulationViewModel;
}) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 260px), 1fr))",
        gap: 18,
        alignItems: "stretch",
      }}
    >
      <div
        style={{
          border: `1px solid ${V3.rule}`,
          background: V3.card,
          padding: "16px 18px",
          minHeight: 180,
        }}
      >
        <div className="v3-eyebrow">Run Activity</div>
        <div
          style={{
            marginTop: 14,
            fontFamily: "'Manrope', sans-serif",
            fontSize: 42,
            fontWeight: 800,
            letterSpacing: 0,
            color: V3.ink,
            lineHeight: 1,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {model.progressPct}%
        </div>
        <div style={{ marginTop: 14 }}>
          <ProgressBar pct={model.progressPct} />
        </div>
        <div style={{ marginTop: 12, fontSize: 13, color: V3.ink2 }}>{model.progressLabel}</div>
        <p style={{ marginTop: 12, fontSize: 13, lineHeight: 1.6, color: V3.ink3 }}>
          {model.warmupCopy}
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", border: `1px solid ${V3.rule}`, background: V3.card }}>
        {(job.steps ?? []).map((step, index) => {
          const tone = statusTone(step.status);
          return (
            <div
              key={step.name}
              style={{
                display: "grid",
                gridTemplateColumns: "36px minmax(0, 1fr) auto",
                gap: 14,
                alignItems: "center",
                padding: "14px 16px",
                minHeight: 76,
                borderBottom: index < (job.steps?.length ?? 0) - 1 ? `1px solid ${V3.rule}` : "none",
                background: step.status === "running" ? V3.paper2 : "transparent",
              }}
            >
              <div
                style={{
                  width: 24,
                  height: 24,
                  border: `1px solid ${tone === "accent" ? V3.coral : V3.rule2}`,
                  color: tone === "accent" ? V3.coral : V3.ink3,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 10,
                  fontWeight: 600,
                }}
              >
                {index + 1}
              </div>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: V3.ink }}>
                  {step.name.replaceAll("_", " ")}
                </div>
                <div
                  style={{
                    marginTop: 4,
                    color: V3.ink3,
                    fontSize: 13,
                    lineHeight: 1.5,
                    overflowWrap: "anywhere",
                  }}
                >
                  {step.message}
                </div>
              </div>
              <Badge tone={tone}>{step.status}</Badge>
            </div>
          );
        })}
      </div>
    </div>
  );
}
