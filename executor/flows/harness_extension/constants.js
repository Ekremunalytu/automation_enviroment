const CONTEXT_PATH = "/workspace/.extrace-harness/context.json";
const READY_PATH = "/workspace/.extrace-harness/ready.json";
const HARNESS_RUN_COMMAND_ID = "extrace.harness.runCurrentStimulus";

// W13-1 (Codex H6): the harness HMAC secret is written by launch_vscode.sh
// before each VS Code start and read-and-unlinked by activate() so the
// same-UID target extension cannot reach it. /run is image-layer (not
// tmpfs by default) and the directory is 0700 owned by executor.
const HARNESS_SECRET_PATH = "/run/extrace/harness-secret";

const BUILTIN_VIEW_CONTAINER_COMMANDS = {
  debug: ["workbench.view.debug"],
  explorer: ["workbench.view.explorer"],
  extensions: ["workbench.view.extensions"],
  scm: ["workbench.view.scm"],
  search: ["workbench.view.search"],
  test: ["workbench.view.testing"],
};

module.exports = {
  BUILTIN_VIEW_CONTAINER_COMMANDS,
  CONTEXT_PATH,
  HARNESS_RUN_COMMAND_ID,
  HARNESS_SECRET_PATH,
  READY_PATH,
};
