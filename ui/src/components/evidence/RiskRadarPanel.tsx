import { Badge, RISK_COLOR, V3, type V3Tone } from "../v3";
import type { ReportRiskRadar } from "../../lib/adapters/report";

type RiskRadarPanelProps = {
  scores: ReportRiskRadar;
  compositeScore: number;
  baselineDelta?: number;
};

const RISK_AXES_META = [
  { id: "exfil", key: "exfil", label: "Exfiltration", benchmark: 20, weight: "med", note: "outbound POSTs", trend: [4, 8, 18, 28, 36] },
  { id: "threat", key: "threat", label: "Threat surface", benchmark: 35, weight: "heavy", note: "sensitive event ratio", trend: [22, 31, 45, 58, 68] },
  { id: "persistence", key: "persistence", label: "Persistence", benchmark: 10, weight: "light", note: "autoload hooks", trend: [2, 4, 6, 9, 12] },
  { id: "privesc", key: "privesc", label: "Process spawn", benchmark: 25, weight: "light", note: "child / shell", trend: [8, 12, 14, 18, 22] },
  { id: "defense", key: "defense", label: "Defense gap", benchmark: 40, weight: "med", note: "coverage shortfall", trend: [18, 24, 30, 44, 54] },
  { id: "resource", key: "resource", label: "Filesystem scope", benchmark: 15, weight: "med", note: "file ops", trend: [6, 12, 22, 34, 41] },
] as const;

function clampScore(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

function scoreTone(score: number): { label: "low" | "medium" | "high"; color: string; tone: V3Tone } {
  if (score > 60) return { label: "high", color: RISK_COLOR.high, tone: "danger" };
  if (score > 35) return { label: "medium", color: RISK_COLOR.medium, tone: "warn" };
  return { label: "low", color: RISK_COLOR.low, tone: "ok" };
}

function sparkPath(trend: ReadonlyArray<number>) {
  const width = 48;
  const height = 16;
  const max = Math.max(1, ...trend);
  return trend
    .map((value, index) => {
      const x = (index / Math.max(1, trend.length - 1)) * width;
      const y = height - (value / max) * height;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
}

export function RiskRadarPanel({ scores, compositeScore, baselineDelta = 14 }: RiskRadarPanelProps) {
  const score = clampScore(compositeScore);
  const tier = scoreTone(score);
  const axes = RISK_AXES_META.map((axis) => ({
    ...axis,
    score: clampScore(scores[axis.key]),
  }));
  const tierCounts = [
    { label: "high", n: axes.filter((axis) => axis.score > 60).length, c: RISK_COLOR.high },
    { label: "medium", n: axes.filter((axis) => axis.score > 35 && axis.score <= 60).length, c: RISK_COLOR.medium },
    { label: "low", n: axes.filter((axis) => axis.score <= 35).length, c: RISK_COLOR.low },
  ];

  const cx = 100;
  const cy = 110;
  const radius = 90;
  const arcPoint = (t: number) => {
    const angle = Math.PI + Math.PI * t;
    return [cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius] as const;
  };
  const arc = (t0: number, t1: number) => {
    if (t1 <= t0) return "";
    const [x0, y0] = arcPoint(t0);
    const [x1, y1] = arcPoint(t1);
    const large = t1 - t0 > 0.5 ? 1 : 0;
    return `M ${x0} ${y0} A ${radius} ${radius} 0 ${large} 1 ${x1} ${y1}`;
  };
  const needleT = score / 100;
  const [needleX, needleY] = arcPoint(needleT);

  return (
    <section
      style={{
        border: `1px solid ${V3.rule}`,
        background: V3.paper,
        display: "grid",
        gridTemplateColumns: "260px 1fr",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          borderRight: `1px solid ${V3.rule}`,
          background: V3.paper2,
          padding: "20px 20px 18px",
          display: "flex",
          flexDirection: "column",
          gap: 14,
        }}
      >
        <div className="eyebrow">Composite score</div>
        <div style={{ display: "flex", justifyContent: "center" }}>
          <svg width="200" height="120" viewBox="0 0 200 120" style={{ overflow: "visible" }} aria-hidden>
            <path d={arc(0, 0.35)} stroke={RISK_COLOR.low} strokeWidth="10" fill="none" opacity="0.25" />
            <path d={arc(0.35, 0.6)} stroke={RISK_COLOR.medium} strokeWidth="10" fill="none" opacity="0.25" />
            <path d={arc(0.6, 1)} stroke={RISK_COLOR.high} strokeWidth="10" fill="none" opacity="0.25" />
            <path
              d={arc(0, needleT)}
              stroke={tier.color}
              strokeWidth="10"
              fill="none"
              strokeLinecap="butt"
              style={{ transition: "all 600ms ease" }}
            />
            {Array.from({ length: 11 }, (_, index) => index / 10).map((t, index) => {
              const [x0, y0] = arcPoint(t);
              const angle = Math.PI + Math.PI * t;
              const x1 = cx + Math.cos(angle) * (radius - 6);
              const y1 = cy + Math.sin(angle) * (radius - 6);
              return (
                <line
                  key={`tick-${index}`}
                  x1={x0}
                  y1={y0}
                  x2={x1}
                  y2={y1}
                  stroke={V3.paper}
                  strokeWidth={index % 5 === 0 ? 1.5 : 1}
                />
              );
            })}
            <line x1={cx} y1={cy} x2={needleX} y2={needleY} stroke={V3.ink} strokeWidth="2" strokeLinecap="round" />
            <circle cx={cx} cy={cy} r={5} fill={V3.ink} />
            <circle cx={cx} cy={cy} r={2} fill={V3.paper} />
          </svg>
        </div>

        <div style={{ textAlign: "center", marginTop: -6 }}>
          <div style={{ display: "flex", justifyContent: "center", alignItems: "baseline", gap: 6 }}>
            <span
              style={{
                fontFamily: "'Manrope', sans-serif",
                fontSize: 52,
                fontWeight: 600,
                color: V3.ink,
                letterSpacing: "-0.03em",
                lineHeight: 1,
              }}
            >
              {score}
            </span>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: V3.ink3 }}>/100</span>
          </div>
          <div style={{ marginTop: 8, display: "flex", justifyContent: "center", gap: 8, alignItems: "center" }}>
            <Badge tone={tier.tone}>{tier.label} risk</Badge>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: V3.ink3 }}>
              {baselineDelta >= 0 ? "+" : ""}
              {baselineDelta} vs baseline
            </span>
          </div>
        </div>

        <div style={{ height: 1, background: V3.rule, margin: "4px 0" }} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
          {tierCounts.map((count) => (
            <div key={count.label} style={{ textAlign: "center" }}>
              <div style={{ fontFamily: "'Manrope', sans-serif", fontSize: 22, fontWeight: 600, color: V3.ink, lineHeight: 1 }}>
                {count.n}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 5, justifyContent: "center", marginTop: 6 }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: count.c }} />
                <span
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 10,
                    color: V3.ink3,
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                  }}
                >
                  {count.label}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ padding: "20px 24px 18px", minWidth: 0 }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "160px 1fr 60px 70px 60px",
            columnGap: 16,
            alignItems: "center",
            paddingBottom: 8,
            marginBottom: 10,
            borderBottom: `1px solid ${V3.rule}`,
          }}
        >
          <span className="eyebrow">Axis</span>
          <span className="eyebrow">Score · vs benchmark</span>
          <span className="eyebrow" style={{ textAlign: "right" }}>Trend</span>
          <span className="eyebrow" style={{ textAlign: "right" }}>Weight</span>
          <span className="eyebrow" style={{ textAlign: "right" }}>Value</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          {axes.map((axis, index) => {
            const axisTier = scoreTone(axis.score);
            const delta = axis.score - axis.benchmark;
            const last = axis.trend[axis.trend.length - 1] ?? 0;
            const maxTrend = Math.max(1, ...axis.trend);
            const endY = 16 - (last / maxTrend) * 16;
            return (
              <div
                key={axis.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "160px 1fr 60px 70px 60px",
                  columnGap: 16,
                  alignItems: "center",
                  padding: "11px 0",
                  borderBottom: index < axes.length - 1 ? `1px dashed ${V3.rule}` : "none",
                }}
              >
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: V3.ink, lineHeight: 1.25 }}>
                    {axis.label}
                  </div>
                  <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: V3.ink3, marginTop: 3 }}>
                    {axis.note}
                  </div>
                </div>

                <div style={{ position: "relative", height: 20 }}>
                  <div style={{ position: "absolute", inset: "6px 0", background: V3.rule }} />
                  <div
                    style={{
                      position: "absolute",
                      left: 0,
                      top: 6,
                      bottom: 6,
                      width: `${axis.score}%`,
                      background: axisTier.color,
                      transition: "width 700ms ease",
                    }}
                  />
                  <div
                    style={{
                      position: "absolute",
                      left: `calc(${axis.benchmark}% - 1px)`,
                      top: 0,
                      bottom: 0,
                      width: 2,
                      background: V3.ink,
                      opacity: 0.55,
                    }}
                  />
                  <div style={{ position: "absolute", left: `${axis.benchmark}%`, top: -2, transform: "translateX(-50%)" }}>
                    <div
                      style={{
                        width: 0,
                        height: 0,
                        borderLeft: "3px solid transparent",
                        borderRight: "3px solid transparent",
                        borderTop: `4px solid ${V3.ink}`,
                        opacity: 0.7,
                      }}
                    />
                  </div>
                  {[25, 50, 75].map((tick) => (
                    <div
                      key={`${axis.id}-${tick}`}
                      style={{ position: "absolute", left: `${tick}%`, top: 4, bottom: 4, width: 1, background: V3.paper, opacity: 0.8 }}
                    />
                  ))}
                </div>

                <div style={{ textAlign: "right" }}>
                  <svg width="48" height="16" viewBox="0 0 48 16" style={{ overflow: "visible", display: "inline-block" }} aria-hidden>
                    <path d={sparkPath(axis.trend)} fill="none" stroke={axisTier.color} strokeWidth="1.25" strokeLinejoin="miter" strokeLinecap="butt" />
                    <circle cx={48} cy={endY} r={1.75} fill={axisTier.color} />
                  </svg>
                </div>

                <div style={{ textAlign: "right" }}>
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 10.5,
                      color: V3.ink3,
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      padding: "3px 6px",
                      border: `1px solid ${V3.rule2}`,
                      background: V3.paper,
                    }}
                  >
                    {axis.weight}
                  </span>
                </div>

                <div style={{ textAlign: "right" }}>
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 14,
                      fontWeight: 600,
                      color: V3.ink,
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {axis.score}
                  </span>
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 10,
                      color: delta > 0 ? V3.coral : V3.ink3,
                      marginLeft: 4,
                    }}
                  >
                    {delta > 0 ? "+" : ""}
                    {delta}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        <div
          style={{
            display: "flex",
            gap: 18,
            marginTop: 14,
            paddingTop: 12,
            borderTop: `1px solid ${V3.rule}`,
            flexWrap: "wrap",
          }}
        >
          <LegendSwatch color={RISK_COLOR.low} label="low · 0-35" />
          <LegendSwatch color={RISK_COLOR.medium} label="medium · 36-60" />
          <LegendSwatch color={RISK_COLOR.high} label="high · 61-100" />
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div
              style={{
                width: 0,
                height: 0,
                borderLeft: "3px solid transparent",
                borderRight: "3px solid transparent",
                borderTop: `5px solid ${V3.ink}`,
                opacity: 0.7,
              }}
            />
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 10.5,
                color: V3.ink3,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              population benchmark
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}

function LegendSwatch({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span style={{ width: 10, height: 3, background: color }} />
      <span
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10.5,
          color: V3.ink3,
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}
      >
        {label}
      </span>
    </div>
  );
}
