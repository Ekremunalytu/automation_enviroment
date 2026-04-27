"use strict";

const fs = require("fs/promises");
const http = require("http");
const path = require("path");
const vscode = require("vscode");

const OUTPUT_NAME = "ExTrace Demo Canary";
const LOCALHOST = "127.0.0.1";
const LOCAL_PORT = 8787;

let output;

function logEvent(event) {
  const payload = {
    source: "extrace.t1-demo-runnable-canary",
    timestamp: new Date().toISOString(),
    ...event,
  };
  output.appendLine(`EXTRACE_DEMO_EVENT ${JSON.stringify(payload)}`);
}

async function prepareCanaryFile(workspaceRoot) {
  const demoDir = path.join(workspaceRoot, ".extrace-demo");
  const canaryPath = path.join(demoDir, "secrets.env");
  await fs.mkdir(demoDir, { recursive: true });
  await fs.writeFile(
    canaryPath,
    "EXTRACE_DEMO_TOKEN=not-a-real-secret\n",
    { flag: "wx" },
  ).catch((error) => {
    if (error && error.code === "EEXIST") {
      return;
    }
    throw error;
  });
  return canaryPath;
}

function postToLocalhost(body) {
  return new Promise((resolve) => {
    const request = http.request(
      {
        host: LOCALHOST,
        port: LOCAL_PORT,
        path: "/extrace-demo",
        method: "POST",
        timeout: 500,
        headers: {
          "content-type": "application/json",
          "content-length": Buffer.byteLength(body),
        },
      },
      (response) => {
        response.resume();
        resolve({ status: "completed", statusCode: response.statusCode });
      },
    );

    request.on("timeout", () => {
      request.destroy(new Error("localhost timeout"));
    });
    request.on("error", (error) => {
      resolve({ status: "failed", reason: error.message });
    });
    request.end(body);
  });
}

async function runSafeSimulation() {
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    logEvent({
      event_type: "simulation_skipped",
      reason: "no_workspace",
    });
    await vscode.window.showWarningMessage(
      "ExTrace demo simulation needs an open workspace.",
    );
    return;
  }

  logEvent({
    event_type: "activated",
    summary: "Safe runnable demo simulation started",
  });

  await vscode.window.showWarningMessage(
    "ExTrace demo: simulated credential prompt. Do not enter real secrets.",
  );
  logEvent({
    event_type: "ui_prompt",
    message: "showWarningMessage simulated credential prompt",
  });

  const canaryPath = await prepareCanaryFile(workspaceFolder.uri.fsPath);
  const canaryValue = await fs.readFile(canaryPath, "utf8");
  logEvent({
    event_type: "file_read",
    operation: "read",
    path: canaryPath,
    summary: "Read declawed workspace canary file",
  });

  const body = JSON.stringify({
    demo: "extrace-safe-canary",
    bytes: Buffer.byteLength(canaryValue),
  });
  const result = await postToLocalhost(body);
  logEvent({
    event_type: "http_request",
    method: "POST",
    host: LOCALHOST,
    port: LOCAL_PORT,
    path: "/extrace-demo",
    status: result.status,
    reason: result.reason,
    summary: "Attempted controlled localhost-only POST",
  });

  await vscode.window.showInformationMessage(
    "ExTrace demo simulation completed.",
  );
}

function activate(context) {
  output = vscode.window.createOutputChannel(OUTPUT_NAME);
  logEvent({
    event_type: "extension_loaded",
    summary: "Extension loaded without running the simulation",
  });
  context.subscriptions.push(output);
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "extraceDemo.runSafeSimulation",
      runSafeSimulation,
    ),
  );
}

function deactivate() {
  if (output) {
    logEvent({
      event_type: "deactivated",
      summary: "Extension deactivated",
    });
  }
}

module.exports = {
  activate,
  deactivate,
};
