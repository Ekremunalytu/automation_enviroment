import { apiHealthTone } from "./systemHealth";

describe("apiHealthTone", () => {
  it("treats the backend's uppercase 'OK' as healthy (case-insensitive)", () => {
    // Regression: the backend emits HEALTH_STATUS = "OK" (appcore/api/config.py).
    // A literal `=== "ok"` rendered a healthy API as amber `warn` on every boot.
    expect(apiHealthTone({ isError: false, status: "OK" })).toBe("ok");
  });

  it("also accepts a lowercase 'ok'", () => {
    expect(apiHealthTone({ isError: false, status: "ok" })).toBe("ok");
  });

  it("is warn for any non-ok / missing status", () => {
    expect(apiHealthTone({ isError: false, status: "degraded" })).toBe("warn");
    expect(apiHealthTone({ isError: false, status: undefined })).toBe("warn");
    expect(apiHealthTone({ isError: false, status: null })).toBe("warn");
  });

  it("is danger when the probe errored (regardless of last status)", () => {
    expect(apiHealthTone({ isError: true, status: "OK" })).toBe("danger");
  });
});
