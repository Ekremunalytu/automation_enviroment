import { V3 } from "../../components/v3";
import type { SeverityDto } from "../../lib/types/contracts";

export function severityColor(severity: SeverityDto): string {
  if (severity === "critical" || severity === "high") return V3.coral;
  if (severity === "medium") return V3.warn;
  if (severity === "low") return V3.ok;
  return V3.ink3;
}

export function severityTone(
  severity: SeverityDto,
): "danger" | "warn" | "ok" | "neutral" {
  if (severity === "critical" || severity === "high") return "danger";
  if (severity === "medium") return "warn";
  if (severity === "low") return "ok";
  return "neutral";
}
