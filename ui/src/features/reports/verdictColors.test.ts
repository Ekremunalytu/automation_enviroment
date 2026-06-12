// S4 / B4 — the verdict palette is the single source of truth that prevents an
// inconclusive (or clean-with-notes) run from rendering with the clean/green
// tone. These assertions pin that invariant at the data layer so it cannot
// regress regardless of how a surface consumes the palette.

import {
  CLEAN_TONE,
  VERDICT_LEGEND,
  VERDICT_STYLES,
  verdictAction,
  verdictTone,
  type Verdict,
} from "./verdictColors";

const ALL_VERDICTS: Verdict[] = [
  "malicious",
  "suspicious",
  "clean_with_notes",
  "clean",
  "inconclusive",
];

describe("verdict palette (S4 / B4)", () => {
  it("gives every one of the five verdicts a distinct tone", () => {
    const tones = ALL_VERDICTS.map((verdict) => verdictTone(verdict));
    expect(new Set(tones).size).toBe(ALL_VERDICTS.length);
  });

  it("reserves the clean (green) tone for the plain clean verdict only", () => {
    for (const verdict of ALL_VERDICTS) {
      if (verdict === "clean") {
        expect(verdictTone(verdict)).toBe(CLEAN_TONE);
      } else {
        expect(verdictTone(verdict)).not.toBe(CLEAN_TONE);
      }
    }
  });

  it("never renders inconclusive or clean_with_notes with the clean tone", () => {
    expect(verdictTone("inconclusive")).not.toBe(CLEAN_TONE);
    expect(verdictTone("clean_with_notes")).not.toBe(CLEAN_TONE);
  });

  it("treats inconclusive as a neutral/grey STOP, not green", () => {
    expect(verdictTone("inconclusive")).toBe("neutral");
  });

  it("maps the two adverse verdicts onto the alarm tones", () => {
    expect(verdictTone("malicious")).toBe("danger");
    expect(verdictTone("suspicious")).toBe("warn");
  });

  it("falls back to neutral (never green) for unknown or missing verdicts", () => {
    expect(verdictTone(undefined)).toBe("neutral");
    expect(verdictTone(null)).toBe("neutral");
    expect(verdictTone("")).toBe("neutral");
    expect(verdictTone("totally-bogus")).toBe("neutral");
  });

  it("provides non-empty recommended-action copy for every verdict", () => {
    for (const verdict of ALL_VERDICTS) {
      expect(verdictAction(verdict).length).toBeGreaterThan(0);
    }
  });

  it("makes the inconclusive action explicitly say it is not a clean result", () => {
    expect(verdictAction("inconclusive").toLowerCase()).toContain("not a clean");
  });

  it("marks only clean and clean_with_notes as clean-family verdicts", () => {
    expect(VERDICT_STYLES.clean.isClean).toBe(true);
    expect(VERDICT_STYLES.clean_with_notes.isClean).toBe(true);
    expect(VERDICT_STYLES.malicious.isClean).toBe(false);
    expect(VERDICT_STYLES.suspicious.isClean).toBe(false);
    expect(VERDICT_STYLES.inconclusive.isClean).toBe(false);
  });

  it("exposes all five states, in worst→best order, in the compact legend", () => {
    expect(VERDICT_LEGEND.map((entry) => entry.verdict)).toEqual(ALL_VERDICTS);
    // The legend swatches must use the same tones as the live verdict tone map.
    for (const entry of VERDICT_LEGEND) {
      expect(entry.tone).toBe(verdictTone(entry.verdict));
    }
  });
});
