import { BADGE_TONE, RISK_COLOR, V3 } from "./tokens";

const CSS_VAR = /^var\(--[a-z0-9-]+\)$/;

describe("V3 palette tokens", () => {
  it("every palette token is a CSS-variable reference (so data-palette themes apply)", () => {
    for (const [key, value] of Object.entries(V3)) {
      expect(value, `V3.${key} must be a var(--…) reference, not a raw hex`).toMatch(CSS_VAR);
    }
  });

  it("badge tones resolve every channel through the palette", () => {
    for (const [tone, channels] of Object.entries(BADGE_TONE)) {
      for (const [channel, value] of Object.entries(channels)) {
        expect(value, `BADGE_TONE.${tone}.${channel}`).toMatch(CSS_VAR);
      }
    }
  });

  it("risk colors resolve through the palette", () => {
    for (const [risk, value] of Object.entries(RISK_COLOR)) {
      expect(value, `RISK_COLOR.${risk}`).toMatch(CSS_VAR);
    }
  });
});
