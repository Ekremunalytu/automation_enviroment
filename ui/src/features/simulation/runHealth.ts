import type { V3Tone } from "../../components/v3";
import type { ReportSummaryView } from "../../lib/types/view-models";

// S4 / B4 run-health analogue of the verdict palette. Only a fully `healthy`
// run earns the green (ok) tone. A `degraded` run warns; an `inconclusive` run
// is a neutral/grey STOP, never green — the harness could not vouch for the
// run, so it must not read clean. Kept in its own module (not inline in the
// page) so the safety property is unit-testable without tripping the
// react-refresh "components-only export" rule on the page file.
export function automationHealthTone(
  status: ReportSummaryView["automationHealthStatus"],
): V3Tone {
  if (status === "healthy") return "ok";
  if (status === "degraded") return "warn";
  return "neutral";
}
