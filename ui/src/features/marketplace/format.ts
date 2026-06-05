import type { VsixThresholdBreachDetail } from "../../lib/types/contracts";

export type ArtifactKey = { publisher: string; name: string; version: string };

export function artifactKey({ publisher, name, version }: ArtifactKey) {
  return `${publisher}.${name}@${version}`;
}

export function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GiB`;
  }
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MiB`;
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(1)} KiB`;
  }
  return `${bytes} B`;
}

export function formatBreachLabel(
  kind: VsixThresholdBreachDetail["breach_kind"],
): string {
  switch (kind) {
    case "entry_count":
      return "File count";
    case "uncompressed_size":
      return "Uncompressed size";
    case "compression_ratio":
      return "Compression ratio";
  }
}

export function formatBreachValue(
  kind: VsixThresholdBreachDetail["breach_kind"],
  value: number,
): string {
  if (kind === "uncompressed_size") return formatBytes(value);
  if (kind === "compression_ratio") return `${value.toFixed(1)}:1`;
  return value.toLocaleString();
}

export function isThresholdBreach(
  detail: unknown,
): detail is VsixThresholdBreachDetail {
  if (!detail || typeof detail !== "object") return false;
  const obj = detail as Record<string, unknown>;
  return obj.error === "vsix_threshold_breach" && typeof obj.breach_kind === "string";
}
