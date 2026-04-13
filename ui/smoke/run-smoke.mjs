import { spawn } from "node:child_process";
import { createServer } from "node:net";
import { fileURLToPath } from "node:url";
import { setTimeout as delay } from "node:timers/promises";
import { chromium } from "playwright";
import { runReportsAndSimulationSmoke } from "./reports-simulation.scenario.mjs";

const cwd = fileURLToPath(new URL("..", import.meta.url));
let port = process.env.SMOKE_PORT || "4173";
let baseUrl = `http://127.0.0.1:${port}`;

const reportFixture = {
  report_version: 2,
  _metadata: { filename: "activation_report_demo.json" },
  summary: {
    total_activated: 1,
    scenarios_run: ["credential probe"],
    monitoring_duration_s: 14,
    network_events: 1,
    file_events: 1,
    sensitive_file_events: 1,
  },
  evidence_events: [
    {
      event_id: "activation-1",
      kind: "activation",
      timestamp: "2026-04-13T10:00:00Z",
      rel_time_s: 1,
      collector: "log",
      actor: "extension",
      extension_id: "publisher.tool",
      activation_event: "onStartupFinished",
      summary: "Extension activated",
    },
    {
      event_id: "network-1",
      kind: "network",
      timestamp: "2026-04-13T10:00:05Z",
      rel_time_s: 5,
      collector: "tshark",
      actor: "extension",
      host: "api.example.com",
      path: "/collect",
      summary: "Outbound request",
    },
  ],
  evidence_links: [],
};

const jobFixture = {
  job_id: "job-1",
  status: "completed",
  publisher: "publisher",
  name: "tool",
  version: "1.0.0",
  message: "completed",
  steps: [
    { name: "reset_sandbox", status: "completed", message: "Sandbox reset" },
    { name: "run_monitoring", status: "completed", message: "Telemetry captured" },
  ],
  created_at: 1713002400,
  updated_at: 1713002410,
  report_path: "activation_report_demo.json",
};

const reportsFixture = [
  {
    filename: "activation_report_demo.json",
    size_bytes: 2048,
    modified: 1713002410,
  },
];

function routeApi(page) {
  return page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (!url.pathname.startsWith("/api/")) {
      await route.continue();
      return;
    }
    console.log(`Stubbed ${route.request().method()} ${url.pathname}`);

    if (url.pathname === "/api/activations") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(reportsFixture) });
      return;
    }

    if (url.pathname === "/api/activations/latest" || url.pathname === "/api/activations/activation_report_demo.json") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(reportFixture) });
      return;
    }

    if (url.pathname === "/api/marketplace/analyze/job-1") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(jobFixture) });
      return;
    }

    await route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ detail: "Unhandled smoke route" }) });
  });
}

async function waitForServer() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const response = await fetch(baseUrl);
      if (response.ok) return;
    } catch {
      // Server is still starting.
    }
    await delay(500);
  }

  throw new Error(`Timed out waiting for Vite dev server at ${baseUrl}`);
}

async function resolvePort() {
  if (process.env.SMOKE_PORT) return process.env.SMOKE_PORT;

  return await new Promise((resolve, reject) => {
    const server = createServer();
    server.unref();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const resolved = typeof address === "object" && address ? String(address.port) : "4173";
      server.close(() => resolve(resolved));
    });
  });
}

function startServer() {
  const child = spawn("npm", ["run", "dev", "--", "--host", "127.0.0.1", "--port", port, "--strictPort"], {
    cwd,
    env: process.env,
    stdio: ["ignore", "pipe", "pipe"],
  });

  child.stdout.on("data", (chunk) => process.stdout.write(chunk));
  child.stderr.on("data", (chunk) => process.stderr.write(chunk));
  return child;
}

async function main() {
  port = await resolvePort();
  baseUrl = `http://127.0.0.1:${port}`;
  const server = startServer();
  let browser;

  try {
    await waitForServer();
    console.log(`Dev server ready at ${baseUrl}`);
    browser = await chromium.launch();
    console.log("Chromium launched.");
    const page = await browser.newPage();
    page.setDefaultTimeout(10_000);
    page.on("console", (message) => console.log(`[browser:${message.type()}] ${message.text()}`));
    page.on("pageerror", (error) => console.error("[pageerror]", error));
    await routeApi(page);
    console.log("API routes stubbed.");
    await runReportsAndSimulationSmoke(page, baseUrl);
    console.log("Smoke test passed.");
  } finally {
    if (browser) {
      await browser.close();
    }
    server.kill("SIGTERM");
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
