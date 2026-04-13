import type { AnalyzeJobStatusDto } from "../../lib/types/contracts";
import type { SimulationViewModel } from "../../lib/types/view-models";
import { Badge } from "../ui/Badge";

export function RunActivityRail({
  job,
  model,
}: {
  job: AnalyzeJobStatusDto;
  model: SimulationViewModel;
}) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,240px)_1fr]">
        <div className="metric-tile">
          <div className="micro-label">Run Activity</div>
          <div className="mt-3 text-3xl font-display font-semibold text-ink tabular-nums">{model.progressPct}%</div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-canvas">
            <div className="h-full rounded-full bg-accent" style={{ width: `${model.progressPct}%` }} />
          </div>
          <div className="mt-3 text-sm text-mute">{model.progressLabel}</div>
          <p className="mt-3 text-sm leading-6 text-mute">{model.warmupCopy}</p>
        </div>

        <div className="space-y-3">
          {job.steps.map((step, index) => {
            const tone =
              step.status === "completed"
                ? "success"
                : step.status === "failed"
                  ? "danger"
                  : step.status === "running"
                    ? "accent"
                    : "default";
            return (
              <div key={step.name} className="metric-tile">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="text-sm font-medium text-ink">
                      {index + 1}. {step.name.replaceAll("_", " ")}
                    </div>
                    <div className="text-sm leading-6 text-mute">{step.message}</div>
                  </div>
                  <Badge tone={tone}>{step.status}</Badge>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
