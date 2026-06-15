export type Tone = "ok" | "neutral" | "accent" | "warn" | "danger";

// The API card on SystemPage polls the local `/api/health` endpoint. The
// backend emits `HEALTH_STATUS = "OK"` (uppercase — `appcore/api/config.py`),
// so the tone comparison MUST be case-insensitive. A literal `=== "ok"`
// rendered a healthy API as amber `warn` on every real boot — the W24 H2
// regression this helper pins. Extracted as a pure function so the
// case-insensitivity is unit-tested, not asserted only through a render.
export function apiHealthTone(args: { isError: boolean; status?: string | null }): Tone {
  if (args.isError) return "danger";
  return (args.status ?? "").toLowerCase() === "ok" ? "ok" : "warn";
}
