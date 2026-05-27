const fs = require("node:fs");
const vscode = require("vscode");

const { HARNESS_SECRET_PATH } = require("./constants");
const {
  emitHarnessEvent,
  emitHarnessMarker,
  readHarnessContext,
  setHarnessChannel,
  setHarnessNonceSecret,
  writeHarnessReadyMarker,
} = require("./markers");

// Output channel name reserved for harness markers + activate diagnostics.
// installOutputChannelHook skips this name so the marker-emit channel
// is not wrapped by the target-extension appendLine listener (would
// otherwise cause each emitted marker to recursively emit an
// output_channel_appendline marker).
const HARNESS_OUTPUT_CHANNEL_NAME = "ExTrace Harness";
const { LocalAuthProvider, LocalFileSystemProvider } = require("./providers");
const { dispatchStimulus, ensureCommentThread } = require("./stimulus_dispatch");

// W13-1 (Codex H6): pull the per-launch HMAC secret out of the
// executor-only file and immediately unlink it, so by the time the
// Python orchestration installs the analyzed (target) extension and
// the target's `activate()` runs, the file no longer exists. Same-UID
// path mode would not isolate target from harness; the protection is
// temporal — the file lives only in the window between
// launch_vscode.sh writing it and the harness reading it. ENOENT is a
// soft failure: emit functions fall back to unsigned markers and the
// Python verifier rejects the run as unverified (fail-closed).
async function consumeHarnessNonceSecret() {
  // Reload reactivations spawn a fresh Extension Host whose activate()
  // fires before the orchestration has had a chance to rewrite the
  // per-launch secret. Poll briefly so a write-after-spawn race resolves
  // on its own without surfacing as a verification gap.
  const MAX_ATTEMPTS = 30;
  const SLEEP_MS = 100;
  let secret = "";
  let readError = "";
  let preExisted = false;
  let attempts = 0;
  for (; attempts < MAX_ATTEMPTS; attempts++) {
    try {
      preExisted = fs.existsSync(HARNESS_SECRET_PATH);
      secret = fs.readFileSync(HARNESS_SECRET_PATH, "utf8").trim();
      if (secret) {
        readError = "";
        break;
      }
    } catch (err) {
      secret = "";
      readError = err && err.code ? err.code : String(err && err.message ? err.message : err);
    }
    await new Promise((resolve) => setTimeout(resolve, SLEEP_MS));
  }
  try {
    fs.unlinkSync(HARNESS_SECRET_PATH);
  } catch (_err) {
    // Already gone; nothing to do.
  }
  setHarnessNonceSecret(secret);
  return {
    secret_path: HARNESS_SECRET_PATH,
    pre_existed: preExisted,
    has_secret: secret.length > 0,
    secret_length: secret.length,
    read_error: readError,
    poll_attempts: attempts + 1,
  };
}

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
    if (name === HARNESS_OUTPUT_CHANNEL_NAME) {
      return channel;
    }
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
  // W13-1: must run first — populates the in-memory HMAC secret used by
  // every subsequent emitHarnessMarker / emitHarnessEvent call,
  // including the diagnostic appendLine writes done through
  // the OutputChannel hook installed below.
  const _secretConsumeDiag = await consumeHarnessNonceSecret();
  installOutputChannelHook();
  // W8-0: dedicated diagnostic channel. Created AFTER the hook so its
  // appendLine writes are captured as OutputSignalEvent (kind=
  // output_channel_appendline, channel="ExTrace Harness"). This gives
  // the Python side a deterministic record of activate() enter/exit
  // and marker-write phases, separate from generic stimulus markers.
  const harnessChannel = vscode.window.createOutputChannel(HARNESS_OUTPUT_CHANNEL_NAME);
  context.subscriptions.push(harnessChannel);
  // Route emitHarnessMarker / emitHarnessEvent to this channel so markers
  // reach the parser via the channel's log file. console.log alone is
  // discarded because launch_vscode.sh sends VS Code stdout to /dev/null.
  setHarnessChannel(harnessChannel);
  const _diag = (phase, extra) => {
    try {
      harnessChannel.appendLine(
        JSON.stringify({
          phase,
          pid: process.pid,
          ts: Date.now(),
          ...(extra || {}),
        })
      );
    } catch (_err) {
      // Diagnostic must never break activation.
    }
  };
  _diag("activate_enter", _secretConsumeDiag);
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

  // W21-3: Workspace trust observability. Baseline trust state emitted at
  // activate() entry, then onDidGrantWorkspaceTrust listener emits a
  // transition marker when trust is granted on the current workspace.
  // Routes through emitHarnessEvent so payloads are HMAC-signed and reach
  // the parser via the reserved "ExTrace Harness" OutputChannel (W19-X
  // Bug B paterni — console.log alone is discarded by launch_vscode.sh).
  const _emitWorkspaceTrustState = (phase) => {
    emitHarnessEvent({
      kind: "workspace_trust_state",
      phase,
      is_trusted: !!vscode.workspace.isTrusted,
      ts: Date.now(),
      collector: "harness_extension",
    });
  };
  _emitWorkspaceTrustState("baseline");
  const trustDisposable = vscode.workspace.onDidGrantWorkspaceTrust(() => {
    _emitWorkspaceTrustState("granted");
  });

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
    trustDisposable,
    commandDisposable
  );

  // Marker write must succeed or activation fails: the Python harness polls
  // for this file to verify the command is registered before invoking it.
  _diag("marker_write_start");
  try {
    await writeHarnessReadyMarker();
    _diag("marker_write_done");
  } catch (err) {
    _diag("marker_write_failed", {
      error: err && err.message ? String(err.message) : String(err),
    });
    throw err;
  }
  _diag("activate_exit");
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
