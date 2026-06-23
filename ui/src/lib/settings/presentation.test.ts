import {
  DEFAULT_DENSITY,
  DEFAULT_TIME_ZONE,
  getDensity,
  getTimeZone,
  initPresentation,
  loadPresentation,
  resolveTimeZone,
  setDensity,
  setTimeZone,
} from "./presentation";

describe("presentation store", () => {
  beforeEach(() => {
    // Reset the module singleton + painted attribute + storage.
    setDensity(DEFAULT_DENSITY);
    setTimeZone(DEFAULT_TIME_ZONE);
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-density");
  });

  it("defaults to comfortable density and the browser-local zone", () => {
    expect(loadPresentation()).toEqual({ density: "comfortable", timeZone: "local" });
  });

  it("setDensity persists, paints data-density, and updates getDensity", () => {
    setDensity("compact");
    expect(getDensity()).toBe("compact");
    expect(document.documentElement.dataset.density).toBe("compact");
    expect(loadPresentation().density).toBe("compact");
  });

  it("setTimeZone persists and updates getTimeZone", () => {
    setTimeZone("Europe/Istanbul");
    expect(getTimeZone()).toBe("Europe/Istanbul");
    expect(loadPresentation().timeZone).toBe("Europe/Istanbul");
  });

  it("rejects an unknown density / zone on load (falls back to defaults)", () => {
    window.localStorage.setItem(
      "extrace-v3-presentation",
      JSON.stringify({ density: "huge", timeZone: "Mars/Phobos" }),
    );
    expect(loadPresentation()).toEqual({
      density: DEFAULT_DENSITY,
      timeZone: DEFAULT_TIME_ZONE,
    });
  });

  it("resolveTimeZone maps local -> undefined and a real IANA zone -> itself", () => {
    expect(resolveTimeZone("local")).toBeUndefined();
    expect(resolveTimeZone("UTC")).toBe("UTC");
    expect(resolveTimeZone("Europe/Istanbul")).toBe("Europe/Istanbul");
  });

  it("initPresentation paints the persisted density and adopts the persisted zone", () => {
    window.localStorage.setItem(
      "extrace-v3-presentation",
      JSON.stringify({ density: "spacious", timeZone: "UTC" }),
    );
    initPresentation();
    expect(getDensity()).toBe("spacious");
    expect(getTimeZone()).toBe("UTC");
    expect(document.documentElement.dataset.density).toBe("spacious");
  });
});
