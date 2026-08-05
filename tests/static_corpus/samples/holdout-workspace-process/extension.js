// Inert source-to-sink shape for advisory measurement only.
const cp = require("child_process");
function inertWorkspaceShape(workspaceValue) {
  return cp.exec(workspaceValue);
}
module.exports.activate = () => inertWorkspaceShape.name;
