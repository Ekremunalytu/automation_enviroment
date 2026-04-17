const CONTEXT_PATH = "/workspace/.extrace-harness/context.json";

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
};
