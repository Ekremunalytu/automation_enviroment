import type { V3Tone } from "../../components/v3";

// S4 / B4 — canonical 5-state verdict styling.
//
// The detection verdict has exactly five states (see
// `DetectionReportView["verdict"]`). Earlier the report header derived its tone
// by funnelling the verdict through a severity helper with a `"low"` fallback,
// which collapsed `clean`, `clean_with_notes`, AND `inconclusive` onto the
// single green ("ok") tone — so an analysis that never finished read exactly
// like a clean pass. This module is the single source of truth that gives each
// verdict a distinct, honest tone and an analyst-facing recommended action.
//
// Safety invariant (B4): only `clean` may use `CLEAN_TONE`. `inconclusive` and
// `clean_with_notes` must never render the clean tone — an unfinished or
// caveated run cannot read green. The live report/simulation surfaces are built
// on the v3 `V3Tone` palette (`neutral | accent | ok | warn | danger`), so the
// five verdicts map onto the five tones as a bijection; there is no blue/info
// tone in v3, so `clean_with_notes` takes the soft-highlight `accent` slot
// rather than the green `ok` slot.

export type Verdict =
  | "malicious"
  | "suspicious"
  | "clean_with_notes"
  | "clean"
  | "inconclusive";

export interface VerdictStyle {
  /** v3 tone for Badge / MetricCell rendering. */
  tone: V3Tone;
  /** Short human label (already title-cased for legends/menus). */
  label: string;
  /** Analyst-facing recommended action shown beneath the verdict badge. */
  action: string;
  /** True only for genuinely-clean verdicts (clean, clean_with_notes). */
  isClean: boolean;
}

/**
 * The tone reserved for a genuinely-clean pass. The B4 invariant is that no
 * other verdict — and in particular neither `inconclusive` nor
 * `clean_with_notes` — may resolve to this tone.
 */
export const CLEAN_TONE: V3Tone = "ok";

export const VERDICT_STYLES: Record<Verdict, VerdictStyle> = {
  malicious: {
    tone: "danger",
    label: "Malicious",
    action:
      "Do not install. Malicious behavior was confirmed — quarantine the extension and rotate any exposed secrets.",
    isClean: false,
  },
  suspicious: {
    tone: "warn",
    label: "Suspicious",
    action:
      "Hold. Suspicious behavior was observed — review the findings before trusting this extension.",
    isClean: false,
  },
  clean_with_notes: {
    // Non-green on purpose: a caveated pass must look different from a clean one.
    tone: "accent",
    label: "Clean with notes",
    action:
      "Likely safe, with caveats — review the flagged observations before installing.",
    isClean: true,
  },
  clean: {
    tone: CLEAN_TONE,
    label: "Clean",
    action: "No malicious behavior was observed in this run.",
    isClean: true,
  },
  inconclusive: {
    // Neutral/grey STOP: the run could not produce a trustworthy verdict.
    tone: "neutral",
    label: "Inconclusive",
    action:
      "Inconclusive — analysis did not complete. Re-run before trusting; this is not a clean result.",
    isClean: false,
  },
};

const FALLBACK: VerdictStyle = {
  tone: "neutral",
  label: "Unknown",
  action: "No verdict was produced for this run.",
  isClean: false,
};

function styleFor(verdict?: string | null): VerdictStyle {
  if (verdict && verdict in VERDICT_STYLES) {
    return VERDICT_STYLES[verdict as Verdict];
  }
  return FALLBACK;
}

/** Canonical verdict → v3 tone. Unknown/missing verdicts are neutral, never green. */
export function verdictTone(verdict?: string | null): V3Tone {
  return styleFor(verdict).tone;
}

/** Recommended-action copy for the given verdict. */
export function verdictAction(verdict?: string | null): string {
  return styleFor(verdict).action;
}

/** Ordered worst→best legend for the compact verdict key on the report header. */
export const VERDICT_LEGEND: ReadonlyArray<{
  verdict: Verdict;
  tone: V3Tone;
  label: string;
}> = (
  ["malicious", "suspicious", "clean_with_notes", "clean", "inconclusive"] as const
).map((verdict) => ({
  verdict,
  tone: VERDICT_STYLES[verdict].tone,
  label: VERDICT_STYLES[verdict].label,
}));
