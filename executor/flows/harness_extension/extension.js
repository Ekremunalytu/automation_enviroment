const fs = require("node:fs/promises");
const path = require("node:path");
const vscode = require("vscode");

const CONTEXT_PATH = "/workspace/.extrace-harness/context.json";
const BUILTIN_VIEW_CONTAINER_COMMANDS = {
  debug: ["workbench.view.debug"],
  explorer: ["workbench.view.explorer"],
  extensions: ["workbench.view.extensions"],
  scm: ["workbench.view.scm"],
  search: ["workbench.view.search"],
  test: ["workbench.view.testing"],
};

function activate(context) {
  const localAuthProvider = new LocalAuthProvider();
  const authDisposable = vscode.authentication.registerAuthenticationProvider(
    "extrace.local",
    "ExTrace Local",
    localAuthProvider,
    { supportsMultipleAccounts: false }
  );
  const fsDisposable = vscode.workspace.registerFileSystemProvider(
    "extrace-fs",
    new LocalFileSystemProvider(),
    { isReadonly: false }
  );
  const taskDisposable = vscode.tasks.registerTaskProvider(
    "extrace-local",
    {
      provideTasks() {
        return [
          new vscode.Task(
            { type: "extrace-local" },
            vscode.TaskScope.Workspace,
            "ExTrace Local Task",
            "extrace",
            new vscode.ShellExecution("echo extrace")
          ),
        ];
      },
      resolveTask(task) {
        return task;
      },
    }
  );
  const terminalProfileDisposable = vscode.window.registerTerminalProfileProvider(
    "extrace.local.profile",
    {
      provideTerminalProfile() {
        return {
          options: {
            name: "ExTrace Local Profile",
            shellPath: "/bin/bash",
          },
        };
      },
    }
  );
  const testController = vscode.tests.createTestController(
    "extrace.harness.tests",
    "ExTrace Harness Tests"
  );
  const testItem = testController.createTestItem(
    "extrace.harness.tests.item",
    "Harness Smoke"
  );
  testController.items.add(testItem);
  testController.createRunProfile(
    "Harness Run",
    vscode.TestRunProfileKind.Run,
    () => {},
    true
  );
  testController.createRunProfile(
    "Harness Debug",
    vscode.TestRunProfileKind.Debug,
    () => {},
    true
  );

  const commentController = vscode.comments.createCommentController(
    "extrace.harness.comments",
    "ExTrace Harness Comments"
  );

  const commandDisposable = vscode.commands.registerCommand(
    "extrace.harness.runCurrentStimulus",
    async () => {
      const payload = await readHarnessContext();
      const attempt = payload.attempt || {};
      const family = String(attempt.event_family || attempt.activation_event || "");
      console.log(`[extrace-harness] running ${family}`);
      await ensureCommentThread(commentController);
      await dispatchStimulus(payload);
    }
  );

  context.subscriptions.push(
    authDisposable,
    fsDisposable,
    taskDisposable,
    terminalProfileDisposable,
    testController,
    commentController,
    commandDisposable
  );
}

async function dispatchStimulus(payload) {
  const attempt = payload.attempt || {};
  const family = String(attempt.event_family || "");
  const value = String(attempt.event_value || "");
  const activationEvent = String(attempt.activation_event || "");
  const providerId =
    payload.auth_provider_ids?.[0] || value || "extrace.local";

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
    await vscode.env.openExternal(
      vscode.Uri.parse("http://127.0.0.1:39111/extrace")
    );
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
        new vscode.NotebookCellOutputItem(
          Buffer.from("extrace"),
          "text/plain"
        ),
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
  const readme = vscode.Uri.file(path.join("/workspace", "README.md"));
  const range = new vscode.Range(0, 0, 0, 0);
  const thread = commentController.createCommentThread(readme, range, []);
  thread.label = "ExTrace Harness Thread";
  thread.dispose();
}

async function readHarnessContext() {
  try {
    const raw = await fs.readFile(CONTEXT_PATH, "utf8");
    return JSON.parse(raw);
  } catch {
    return {};
  }
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
  const target =
    rawTarget && typeof rawTarget === "object" ? rawTarget : {};
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
  const dynamicFocusCommands = allCommands.filter((commandId) =>
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

class LocalAuthProvider {
  constructor() {
    this.onDidChangeSessions = new vscode.EventEmitter();
    this.currentSession = {
      id: "extrace-local-session",
      accessToken: "extrace-local-token",
      account: {
        id: "extrace-local-account",
        label: "ExTrace Local Account",
      },
      scopes: ["default"],
    };
  }

  getSessions() {
    return Promise.resolve([this.currentSession]);
  }

  createSession(scopes) {
    this.currentSession = {
      ...this.currentSession,
      scopes,
    };
    return Promise.resolve(this.currentSession);
  }

  removeSession() {
    return Promise.resolve();
  }
}

class LocalFileSystemProvider {
  stat() {
    return {
      ctime: Date.now(),
      mtime: Date.now(),
      size: 7,
      type: vscode.FileType.File,
    };
  }

  readDirectory() {
    return [];
  }

  createDirectory() {}

  readFile() {
    return Buffer.from("extrace");
  }

  writeFile() {}

  delete() {}

  rename() {}

  watch() {
    return new vscode.Disposable(() => {});
  }
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
