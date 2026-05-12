"use strict";

const vscode = require("vscode");

function activate(context) {
  console.log("[fixture-cmd] activated");

  const disposable = vscode.commands.registerCommand(
    "extrace.fixture-cmd.run",
    () => {
      console.log("[fixture-cmd] deterministic fixture noop invoked");
    },
  );

  context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
