import type { DetectionFindingView } from "../../lib/types/view-models";
import { verdictColors } from "./verdictColors";

export function FindingCard({
  finding,
  onShowEvidence,
}: {
  finding: DetectionFindingView;
  onShowEvidence: (eventId: string) => void;
}) {
  const firstEvidenceId = finding.evidence[0]?.eventId;
  const severityTone =
    finding.severity === "critical" || finding.severity === "high"
      ? verdictColors.malicious.badge
      : finding.severity === "medium"
        ? verdictColors.suspicious.badge
        : verdictColors.clean_with_notes.badge;

  return (
    <article className="space-y-4 rounded-[18px] border border-line bg-panel px-5 py-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="micro-label">{finding.ruleId}</div>
          <h3 className="text-xl font-semibold tracking-[-0.03em] text-ink">
            {finding.title}
          </h3>
        </div>
        <div className="flex flex-wrap gap-2 text-xs font-medium">
          <span className={`rounded-full px-3 py-1 ${severityTone}`}>
            Severity: {finding.severityLabel}
          </span>
          <span className="rounded-full bg-panelAlt px-3 py-1 text-inkSoft">
            Confidence: {finding.confidenceLabel}
          </span>
          <span className="rounded-full bg-panelAlt px-3 py-1 text-inkSoft">
            {finding.adversaryClass}
          </span>
        </div>
      </div>

      <p className="text-sm leading-7 text-mute">{finding.description}</p>

      {finding.categories.length ? (
        <div className="flex flex-wrap gap-2 text-xs text-inkSoft">
          {finding.categories.map((category) => (
            <span className="rounded-full border border-line px-3 py-1" key={category}>
              {category}
            </span>
          ))}
        </div>
      ) : null}

      {finding.mitigationHint ? (
        <div className="rounded-[14px] border border-lineSoft bg-panelAlt px-4 py-3 text-sm text-mute">
          {finding.mitigationHint}
        </div>
      ) : null}

      <div className="flex items-center justify-between gap-3">
        <div className="text-sm text-mute">
          {finding.evidence.length
            ? finding.evidence.map((item) => item.summary).join(" • ")
            : "No evidence references recorded."}
        </div>
        <button
          className="ghost-button"
          disabled={!firstEvidenceId}
          onClick={() => firstEvidenceId && onShowEvidence(firstEvidenceId)}
          type="button"
        >
          {finding.evidence.length} evidence
        </button>
      </div>
    </article>
  );
}
