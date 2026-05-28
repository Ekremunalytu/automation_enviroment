const path = require("node:path");
const vscode = require("vscode");

const { BUILTIN_VIEW_CONTAINER_COMMANDS } = require("./constants");
const { emitHarnessEvent } = require("./markers");

async function dispatchStimulus(payload) {
  const attempt = payload.attempt || {};
  const family = String(attempt.event_family || "");
  const value = String(attempt.event_value || "");
  const activationEvent = String(attempt.activation_event || "");
  const providerId = payload.auth_provider_ids?.[0] || value || "extrace.local";

  if (family === "onAuthenticationRequest") {
    await vscode.authentication.getSession(providerId, ["default"], {
      createIfNone: true,
      silent: false,
    });
    return;
  }
  if (family === "onFileSystem") {
    const scheme = value || "extrace-fs";
    const document = await vscode.workspace.openTextDocument(
      vscode.Uri.parse(`${scheme}:/trigger.txt`)
    );
    await vscode.window.showTextDocument(document, { preview: false });
    return;
  }
  if (family === "onIssueReporterOpened") {
    await tryCommands([
      "workbench.action.openIssueReporter",
      "help.openIssueReporter",
    ]);
    return;
  }
  if (family === "onOpenExternalUri") {
    await vscode.env.openExternal(vscode.Uri.parse("http://127.0.0.1:39111/extrace"));
    return;
  }
  if (family === "onUri") {
    const uri = payload.uri_trigger || "vscode://extrace.harness/ping";
    await vscode.env.openExternal(vscode.Uri.parse(uri));
    return;
  }
  if (family === "onWalkthrough") {
    await tryCommands([
      "workbench.action.openWalkthrough",
      "workbench.action.openWalkthroughs",
    ]);
    return;
  }
  if (family === "onChatParticipant" || family === "onLanguageModelTool") {
    await tryCommands([
      "workbench.action.chat.open",
      "workbench.panel.chat.view.copilot.focus",
    ]);
    await vscode.commands.executeCommand("type", {
      text: value ? `@${value} harness` : "harness",
    });
    return;
  }
  if (family === "onEditSession") {
    await tryCommands([
      "workbench.editSessions.actions.storeCurrent",
      "workbench.editSessions.actions.resumeLatest",
    ]);
    return;
  }
  if (family === "onRenderer" || family === "onNotebook") {
    const notebook = new vscode.NotebookData([
      new vscode.NotebookCellData(
        vscode.NotebookCellKind.Code,
        "print('extrace')",
        "python"
      ),
    ]);
    notebook.cells[0].outputs = [
      new vscode.NotebookCellOutput([
        new vscode.NotebookCellOutputItem(Buffer.from("extrace"), "text/plain"),
      ]),
    ];
    const document = await vscode.workspace.openNotebookDocument(
      "jupyter-notebook",
      notebook
    );
    await vscode.window.showNotebookDocument(document);
    return;
  }
  if (
    family === "onTerminal" ||
    family === "onTerminalProfile" ||
    family === "onTerminalShellIntegration"
  ) {
    const terminal = vscode.window.createTerminal({
      name: "ExTrace Harness Terminal",
      shellPath: "/bin/bash",
    });
    terminal.show();
    terminal.sendText("echo extrace");
    return;
  }
  if (family === "onWebviewPanel") {
    const panel = vscode.window.createWebviewPanel(
      value || "extraceHarnessView",
      "ExTrace Harness Panel",
      vscode.ViewColumn.One,
      {}
    );
    panel.webview.html = "<html><body>extrace</body></html>";
    return;
  }
  if (family === "onView") {
    await revealContributedView(payload, value);
    return;
  }
  if (family.startsWith("onDebug")) {
    await tryCommands([
      "workbench.action.debug.selectandstart",
      "workbench.action.debug.configure",
    ]);
    return;
  }
  if (family === "onTaskType") {
    await tryCommands(["workbench.action.tasks.runTask"]);
    return;
  }
  if (family === "onSearch") {
    await tryCommands(["workbench.action.findInFiles"]);
    return;
  }
  if (family === "onCommand" && activationEvent) {
    await tryCommands([activationEvent.replace(/^onCommand:/, "")]);
    return;
  }
  if (family === "onStartupFinished" || family === "*") {
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

async function ensureCommentThread(commentController) {
  // W21-2: Comment thread lifecycle observability. Emit `thread_created`
  // immediately after createCommentThread; `thread_disposed` immediately
  // after dispose. Routes through emitHarnessEvent so payloads are
  // HMAC-signed (W19-X Bug B paterni — reserved "ExTrace Harness"
  // OutputChannel). Ephemeral thread default (W19-X HMAC reactivation
  // race lesson): thread is created + disposed within this call so
  // a stale handle from a previous activation cannot mask a regression.
  const readme = vscode.Uri.file(path.join("/workspace", "README.md"));
  const range = new vscode.Range(0, 0, 0, 0);
  const thread = commentController.createCommentThread(readme, range, []);
  thread.label = "ExTrace Harness Thread";
  const threadId = `${commentController.id || "comments"}:${readme.fsPath}:${range.start.line}`;
  emitHarnessEvent({
    kind: "comment_thread_state",
    phase: "thread_created",
    thread_id: threadId,
    ts: Date.now(),
    collector: "harness_extension",
  });
  thread.dispose();
  emitHarnessEvent({
    kind: "comment_thread_state",
    phase: "thread_disposed",
    thread_id: threadId,
    ts: Date.now(),
    collector: "harness_extension",
  });
}

async function revealContributedView(payload, viewId) {
  if (!viewId) {
    throw new Error("onView stimulus requires a contributed view id");
  }

  const viewTargets =
    payload.view_targets && typeof payload.view_targets === "object"
      ? payload.view_targets
      : {};
  const rawTarget = viewTargets[viewId];
  const target = rawTarget && typeof rawTarget === "object" ? rawTarget : {};
  const containerId =
    typeof target.container_id === "string" ? target.container_id : "";

  const containerCommands = containerCommandCandidates(containerId);
  if (containerCommands.length) {
    await tryCommands(containerCommands);
  }

  const exactFocusCommands = [
    `${viewId}.focus`,
    `workbench.actions.treeView.${viewId}.focus`,
  ];
  if (await tryCommands(exactFocusCommands)) {
    return;
  }

  const allCommands = await vscode.commands.getCommands(true);
  const dynamicFocusCommands = allCommands.filter(
    (commandId) =>
      commandId === `${viewId}.focus` ||
      commandId === `workbench.actions.treeView.${viewId}.focus` ||
      (commandId.endsWith(".focus") && commandId.includes(viewId))
  );
  if (await tryCommands(dynamicFocusCommands)) {
    return;
  }

  throw new Error(
    `Unable to reveal contributed view '${viewId}' via the local harness`
  );
}

function containerCommandCandidates(containerId) {
  const normalized = String(containerId || "").trim();
  if (!normalized) {
    return [];
  }
  if (BUILTIN_VIEW_CONTAINER_COMMANDS[normalized]) {
    return BUILTIN_VIEW_CONTAINER_COMMANDS[normalized];
  }
  return [`workbench.view.extension.${normalized}`];
}

async function tryCommands(commandIds) {
  for (const commandId of commandIds) {
    try {
      await vscode.commands.executeCommand(commandId);
      return true;
    } catch {
      // Continue through the fallback command list.
    }
  }
  return false;
}

module.exports = {
  dispatchStimulus,
  ensureCommentThread,
};
