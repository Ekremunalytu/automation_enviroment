export function getExpectedTelemetry(status?: string, hasEvidence?: boolean) {
  if (hasEvidence) return "Evidence is streaming into the event table and inspector.";
  if (status === "queued") return "Sandbox reset and installation logs should appear next.";
  if (status === "running") return "Activation events should land once the extension host finishes warming up.";
  return "Report output will populate when the executor finalizes the run.";
}
