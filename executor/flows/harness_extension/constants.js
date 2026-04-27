const CONTEXT_PATH = "/workspace/.extrace-harness/context.json";
const READY_PATH = "/workspace/.extrace-harness/ready.json";
const HARNESS_RUN_COMMAND_ID = "extrace.harness.runCurrentStimulus";

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
  READY_PATH,
};
