const vscode = require("vscode");

const {
  emitHarnessEvent,
  emitHarnessMarker,
  readHarnessContext,
  writeHarnessReadyMarker,
} = require("./markers");
const { LocalAuthProvider, LocalFileSystemProvider } = require("./providers");
const { dispatchStimulus, ensureCommentThread } = require("./stimulus_dispatch");

// PR345 PR5: capture target-owned output-channel writes by wrapping
// vscode.window.createOutputChannel before any non-harness extension
// activates. ADR 0006 §2 documents the contract; the hook installs once
// per Extension Host process and emits each append/appendLine call as a
// JSON-line marker the Python parser converts into an EvidenceEvent
// (kind="output_channel_appendline", collector="harness_extension").
let _outputChannelHookInstalled = false;
function installOutputChannelHook() {
  if (_outputChannelHookInstalled) {
    return;
  }
  _outputChannelHookInstalled = true;
  const _origCreate = vscode.window.createOutputChannel;
  vscode.window.createOutputChannel = function patchedCreateOutputChannel(name, ...rest) {
    const channel = _origCreate.call(vscode.window, name, ...rest);
    const wrap = (fn) => function patchedAppend(value) {
      try {
        const text = String(value == null ? "" : value);
        const truncated = text.length > 500 ? text.slice(0, 500) : text;
        emitHarnessEvent({
          kind: "output_channel_appendline",
          channel: name,
          text: truncated,
          ts: Date.now(),
          collector: "harness_extension",
        });
      } catch (_err) {
        // Hook must never break the wrapped extension's flow.
      }
      return fn.apply(channel, arguments);
    };
    if (typeof channel.append === "function") {
      channel.append = wrap(channel.append);
    }
    if (typeof channel.appendLine === "function") {
      channel.appendLine = wrap(channel.appendLine);
    }
    return channel;
  };
}

async function activate(context) {
  installOutputChannelHook();
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
  const taskDisposable = vscode.tasks.registerTaskProvider("extrace-local", {
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
  });
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
      const attemptId = String(payload.attempt_id || attempt.attempt_id || "");

      emitHarnessMarker("start", {
        attempt_id: attemptId,
        family,
        activation_event: String(attempt.activation_event || ""),
        event_value: String(attempt.event_value || ""),
      });
      console.log(`[extrace-harness] running ${family}`);
      try {
        await ensureCommentThread(commentController);
        await dispatchStimulus(payload);
        emitHarnessMarker("complete", {
          attempt_id: attemptId,
          family,
          activation_event: String(attempt.activation_event || ""),
          event_value: String(attempt.event_value || ""),
        });
      } catch (error) {
        emitHarnessMarker("failed", {
          attempt_id: attemptId,
          family,
          activation_event: String(attempt.activation_event || ""),
          event_value: String(attempt.event_value || ""),
          error: error instanceof Error ? error.message : String(error || "unknown"),
        });
        throw error;
      }
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

  // Marker write must succeed or activation fails: the Python harness polls
  // for this file to verify the command is registered before invoking it.
  await writeHarnessReadyMarker();
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
