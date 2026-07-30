import { afterEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "./client";

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("apiClient URL discipline (W15-5 I2)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("getHealth() targets /api/health, not /health (nginx /api/* proxy)", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ status: "ok", service: "test" }));

    await apiClient.getHealth();

    expect(fetchSpy).toHaveBeenCalledOnce();
    const [calledUrl] = fetchSpy.mock.calls[0];
    const urlString = String(calledUrl);
    expect(urlString).toMatch(/\/api\/health$/);
    expect(urlString.endsWith("/health") && !urlString.includes("/api/health")).toBe(false);
  });

  it("getHealth() emits the bare /api/health path under the default (empty) base URL", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ status: "ok", service: "test" }));

    await apiClient.getHealth();

    const [calledUrl] = fetchSpy.mock.calls[0];
    expect(String(calledUrl)).toBe("/api/health");
  });

  it("reads the measured appliance snapshot through the system health API", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        jsonResponse({ observed_at: "", services: [], inventory: [] }),
      );

    await apiClient.getSystemHealth();

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/system/health",
      expect.objectContaining({ signal: undefined }),
    );
  });

  it("reads and updates the executor preference through the settings API", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async () =>
        jsonResponse({ dynamic_analysis_enabled: false }),
      );

    await apiClient.getExecutorPreferences();
    await apiClient.updateExecutorPreferences({
      dynamic_analysis_enabled: true,
    });

    expect(fetchSpy).toHaveBeenNthCalledWith(
      1,
      "/api/settings/executor/preferences",
      expect.objectContaining({ signal: undefined }),
    );
    expect(fetchSpy).toHaveBeenNthCalledWith(
      2,
      "/api/settings/executor/preferences",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ dynamic_analysis_enabled: true }),
      }),
    );
  });

  it("reads the latest static-only artifact through the reports API", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        jsonResponse({ filename: "static_report_demo.json", modified: 1 }),
      );

    await apiClient.getLatestStaticReport();

    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/activations/static/latest",
      expect.objectContaining({ signal: undefined }),
    );
  });
});
