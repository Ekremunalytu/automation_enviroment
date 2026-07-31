// Declawed source-only marker. Nothing in this corpus is executed.
const childProcess = require("child_process");
const fs = require("fs");
const downloaded = "/tmp/declawed-marker";
function inertDropperShape() {
  fs.chmodSync(downloaded, 0o700);
  return childProcess.execFile(downloaded);
}
module.exports.activate = () => inertDropperShape.name;
