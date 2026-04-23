"use strict";

const vscode = require("vscode");

function activate(context) {
  console.log("[fixture-chat] activated");

  const participant = vscode.chat.createChatParticipant(
    "extrace.fixture-chat.agent",
    async (_request, _chatContext, stream) => {
      stream.markdown("Fixture chat participant response.");
    },
  );

  context.subscriptions.push(participant);
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
