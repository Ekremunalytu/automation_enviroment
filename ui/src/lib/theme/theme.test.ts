import {
  DEFAULT_THEME,
  applyTheme,
  getTheme,
  initTheme,
  isThemeId,
  loadTheme,
  setTheme,
} from "./theme";

describe("theme store", () => {
  beforeEach(() => {
    // Reset the module singleton + the painted attribute + storage so each
    // test starts from the default, unpainted state.
    setTheme(DEFAULT_THEME);
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-palette");
  });

  it("isThemeId validates the three known palettes only", () => {
    expect(isThemeId("shift5")).toBe(true);
    expect(isThemeId("parchment")).toBe(true);
    expect(isThemeId("terminal")).toBe(true);
    expect(isThemeId("neon")).toBe(false);
    expect(isThemeId(null)).toBe(false);
  });

  it("loadTheme falls back to the default for missing / unknown values", () => {
    expect(loadTheme()).toBe(DEFAULT_THEME);
    window.localStorage.setItem("extrace-v3-theme", "bogus");
    expect(loadTheme()).toBe(DEFAULT_THEME);
    window.localStorage.setItem("extrace-v3-theme", "parchment");
    expect(loadTheme()).toBe("parchment");
  });

  it("setTheme persists, paints <html data-palette>, and updates getTheme", () => {
    setTheme("parchment");
    expect(getTheme()).toBe("parchment");
    expect(window.localStorage.getItem("extrace-v3-theme")).toBe("parchment");
    expect(document.documentElement.dataset.palette).toBe("parchment");
  });

  it("initTheme paints the persisted theme onto <html>", () => {
    window.localStorage.setItem("extrace-v3-theme", "terminal");
    expect(initTheme()).toBe("terminal");
    expect(getTheme()).toBe("terminal");
    expect(document.documentElement.dataset.palette).toBe("terminal");
  });

  it("applyTheme paints without persisting", () => {
    applyTheme("parchment");
    expect(document.documentElement.dataset.palette).toBe("parchment");
    expect(window.localStorage.getItem("extrace-v3-theme")).toBeNull();
  });
});
