import { EmptyState } from "../../components/ui/EmptyState";
import type { DetectionReportView } from "../../lib/types/view-models";
import { FindingCard } from "./FindingCard";
import { verdictColors } from "./verdictColors";

function emptyStateCopy(verdict: DetectionReportView["verdict"]) {
  if (verdict === "clean") return "No rules fired. Verdict: clean.";
  if (verdict === "clean_with_notes") return "Only informational findings were recorded.";
  if (verdict === "inconclusive") return "No rules fired, but analysis remained inconclusive.";
  return "No findings were attached to this verdict.";
}

export function DetectionPanel({
  detection,
  onShowEvidence,
}: {
  detection: DetectionReportView | null;
  onShowEvidence: (eventId: string) => void;
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

  const tone = verdictColors[detection.verdict];

  return (
    <div className="space-y-5">
      <section
        aria-live="polite"
        className={`rounded-[22px] border px-6 py-6 ${tone.banner}`}
      >
        <div className="eyebrow">Detection</div>
        <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
          <div className="space-y-3">
            <h2 className="text-[34px] font-semibold tracking-[-0.05em]">
              {detection.verdictLabel}
            </h2>
            <p className="max-w-3xl text-sm leading-7">{detection.verdictRationale}</p>
          </div>
          <div className={`rounded-full px-4 py-2 text-sm font-medium ${tone.badge}`}>
            {detection.findings.length} finding{detection.findings.length === 1 ? "" : "s"}
          </div>
        </div>
      </section>

      {!detection.findings.length ? (
        <EmptyState
          eyebrow="Findings"
          body={emptyStateCopy(detection.verdict)}
          title="No fired rules"
        />
      ) : (
        <section className="space-y-4">
          {detection.findings.map((finding) => (
            <FindingCard
              finding={finding}
              key={finding.id}
              onShowEvidence={onShowEvidence}
            />
          ))}
        </section>
      )}
    </div>
  );
}
